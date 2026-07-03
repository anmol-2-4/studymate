"""StudyMate — a tutor that remembers you. FastAPI backend on Cognee Cloud."""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import memory
import store

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await memory.connect()
    yield
    await memory.disconnect()


app = FastAPI(title="StudyMate", lifespan=lifespan)


class TopicIn(BaseModel):
    name: str


class NotesIn(BaseModel):
    text: str


class AskIn(BaseModel):
    question: str


class AnswerIn(BaseModel):
    session_id: str
    question: str
    answer: str


class SessionIn(BaseModel):
    session_id: str


@app.get("/api/status")
async def status():
    return {"connected": memory.is_connected()}


@app.get("/api/topics")
async def topics():
    return store.list_topics()


@app.post("/api/topics")
async def create_topic(body: TopicIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Topic name is required")
    store.add_topic(name)
    return {"ok": True, "name": name}


@app.delete("/api/topics/{name}")
async def forget_topic(name: str):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    result = await memory.wipe(name)
    store.remove_topic(name)
    return {"ok": True, "forgotten": result}


@app.post("/api/topics/{name}/notes")
async def add_notes(name: str, body: NotesIn):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    if not body.text.strip():
        raise HTTPException(422, "Notes text is empty")
    status = await memory.ingest_notes(name, body.text.strip())
    store.bump_notes(name)
    return {"ok": True, "status": str(status)}


@app.post("/api/topics/{name}/ask")
async def ask(name: str, body: AskIn):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    answer = await memory.ask(name, body.question)
    return {"answer": answer}


@app.post("/api/topics/{name}/quiz/start")
async def quiz_start(name: str):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    session_id = f"quiz_{uuid.uuid4().hex[:12]}"
    store.start_session(name, session_id)
    weak = store.weak_concepts(name)
    question = await memory.quiz_question(name, avoid=[], weak_concepts=weak)
    if not question:
        raise HTTPException(409, "No study material yet — add notes first")
    return {"session_id": session_id, "question": question, "targeting": weak}


@app.post("/api/topics/{name}/quiz/answer")
async def quiz_answer(name: str, body: AnswerIn):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    graded = await memory.grade_answer(name, body.question, body.answer)
    await memory.record_qa(
        name, body.session_id, body.question, body.answer,
        context=graded["explanation"], correct=graded["correct"],
    )
    store.record_result(name, body.session_id, body.question,
                        graded["correct"], graded["concept"])
    asked = _asked_questions(name, body.session_id, body.question)
    weak = store.weak_concepts(name)
    next_question = await memory.quiz_question(name, avoid=asked, weak_concepts=weak)
    return {**graded, "next_question": next_question, "targeting": weak}


_session_questions: dict[str, list[str]] = {}


def _asked_questions(name: str, session_id: str, question: str) -> list[str]:
    asked = _session_questions.setdefault(session_id, [])
    if question not in asked:
        asked.append(question)
    return asked


@app.post("/api/topics/{name}/quiz/finish")
async def quiz_finish(name: str, body: SessionIn):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    await memory.adapt(name, body.session_id)
    store.mark_adapted(name, body.session_id)
    _session_questions.pop(body.session_id, None)
    topic = store.get_topic(name)
    session = next((s for s in topic["sessions"] if s["id"] == body.session_id), {})
    return {"ok": True, "session": session, "weak_concepts": store.weak_concepts(name)}


@app.get("/api/topics/{name}/progress")
async def progress(name: str):
    topic = store.get_topic(name)
    if not topic:
        raise HTTPException(404, "No such topic")
    return {
        "summary": next(t for t in store.list_topics() if t["name"] == name),
        "sessions": topic["sessions"],
        "missed": topic["missed"],
        "weak_concepts": store.weak_concepts(name),
    }


@app.get("/api/topics/{name}/graph")
async def graph(name: str):
    if not store.get_topic(name):
        raise HTTPException(404, "No such topic")
    html = await memory.graph_html(name)
    if not html:
        raise HTTPException(404, "Graph not available yet — add notes first")
    return HTMLResponse(html)


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="frontend")
