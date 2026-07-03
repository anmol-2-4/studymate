"""Cognee Cloud wrapper — every StudyMate memory operation goes through here.

Topic  -> Cognee dataset      (remember / forget)
Session-> Cognee session      (QAEntry per quiz answer)
Adapt  -> improve(session_ids)(feedback weights bridge into the graph)
"""

import os
import re
import json

import cognee
import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = (os.getenv("COGNEE_BASE_URL") or os.getenv("COGNEE_SERVICE_URL") or "").rstrip("/")
API_KEY = os.getenv("COGNEE_API_KEY", "")

_connected = False


def dataset_for(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    return f"studymate_{slug}"


async def connect() -> bool:
    global _connected
    if _connected:
        return True
    if not BASE_URL or not API_KEY:
        return False
    await cognee.serve(url=BASE_URL, api_key=API_KEY)
    _connected = True
    return True


async def disconnect():
    global _connected
    if _connected:
        await cognee.disconnect()
        _connected = False


def is_connected() -> bool:
    return _connected


# ---------- remember ----------

async def ingest_notes(topic: str, text: str):
    result = await cognee.remember(text, dataset_name=dataset_for(topic))
    return getattr(result, "status", "ok")


# ---------- recall ----------

def _entry_text(entry) -> str:
    for attr in ("answer", "text", "content"):
        value = getattr(entry, attr, None)
        if isinstance(value, str) and value.strip():
            return value
    return ""


async def _recall_text(topic: str, query: str, system_prompt: str | None = None,
                       session_id: str | None = None) -> str:
    results = await cognee.recall(
        query,
        datasets=[dataset_for(topic)],
        top_k=10,
        session_id=session_id,
        system_prompt=system_prompt,
        feedback_influence=0.5,
    )
    parts = [_entry_text(r) for r in results]
    return "\n".join(p for p in parts if p).strip()


async def ask(topic: str, question: str, session_id: str | None = None) -> str:
    answer = await _recall_text(topic, question, session_id=session_id)
    return answer or "I couldn't find anything about that in your notes yet."


QUIZ_PROMPT = (
    "You are a strict but fair tutor writing an exam. Using ONLY the provided "
    "context from the student's own study notes, write exactly ONE short-answer "
    "quiz question. Output the question text alone — no preamble, no answer, "
    "no numbering."
)

GRADE_PROMPT = (
    "You are grading a student's short answer using the provided context from "
    "their study notes as the source of truth. Respond with ONLY a JSON object: "
    '{"correct": true|false, "explanation": "<one- or two-sentence explanation '
    'with the right answer>", "concept": "<2-4 word name of the concept tested>"}'
)


async def quiz_question(topic: str, avoid: list[str], weak_concepts: list[str]) -> str:
    focus = (
        f"the concepts the student previously got wrong: {', '.join(weak_concepts)}"
        if weak_concepts else "the most important concepts, definitions and facts"
    )
    query = f"Test me on {focus} in {topic}."
    prompt = QUIZ_PROMPT
    if avoid:
        prompt += " Do NOT ask about the same thing as any of these already-asked questions: "
        prompt += " | ".join(avoid[-8:])
    question = await _recall_text(topic, query, system_prompt=prompt)
    return question


async def grade_answer(topic: str, question: str, answer: str) -> dict:
    raw = await _recall_text(
        topic,
        f"Question: {question}\nStudent's answer: {answer}",
        system_prompt=GRADE_PROMPT,
    )
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return {
                "correct": bool(data.get("correct")),
                "explanation": str(data.get("explanation", "")).strip(),
                "concept": str(data.get("concept", "")).strip(),
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    lowered = raw.lower()
    return {
        "correct": "true" in lowered and "false" not in lowered,
        "explanation": raw.strip()[:400],
        "concept": "",
    }


# ---------- session memory (quiz answers) ----------

async def record_qa(topic: str, session_id: str, question: str, answer: str,
                    context: str, correct: bool):
    entry = cognee.QAEntry(
        type="qa",
        question=question,
        answer=answer,
        context=context,
        feedback_text="correct answer" if correct else "student answered incorrectly — weak spot",
        feedback_score=5 if correct else 1,
    )
    await cognee.remember(entry, dataset_name=dataset_for(topic), session_id=session_id)


# ---------- improve ----------

async def adapt(topic: str, session_id: str):
    return await cognee.improve(dataset=dataset_for(topic), session_ids=[session_id])


# ---------- forget ----------

async def wipe(topic: str) -> dict:
    return await cognee.forget(dataset=dataset_for(topic))


# ---------- graph visualization (Cloud REST) ----------

async def graph_html(topic: str) -> str | None:
    headers = {"X-Api-Key": API_KEY, "Authorization": f"Bearer {API_KEY}"}
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=60) as client:
        datasets = (await client.get("/api/v1/datasets")).json()
        wanted = dataset_for(topic)
        dataset_id = next((d["id"] for d in datasets if d.get("name") == wanted), None)
        if not dataset_id:
            return None
        response = await client.get("/api/v1/visualize", params={"dataset_id": dataset_id})
        if response.status_code == 200:
            return response.text
    return None
