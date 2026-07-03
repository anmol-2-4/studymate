"""StudyMate — a tutor that remembers you. FastAPI backend on Cognee Cloud."""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
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
    session_id: str | None = None


class AnswerIn(BaseModel):
    session_id: str
    question: str
    answer: str


class SessionIn(BaseModel):
    session_id: str


def _dataset(name: str) -> str:
    dataset = store.dataset_of(name)
    if not dataset:
        raise HTTPException(404, "No such topic")
    return dataset


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
    result = await memory.wipe(_dataset(name))
    store.remove_topic(name)
    return {"ok": True, "forgotten": result}


@app.post("/api/topics/{name}/notes")
async def add_notes(name: str, body: NotesIn):
    dataset = _dataset(name)
    if not body.text.strip():
        raise HTTPException(422, "Notes text is empty")
    status = await memory.ingest_notes(dataset, body.text.strip())
    store.bump_notes(name)
    return {"ok": True, "status": str(status)}


@app.post("/api/topics/{name}/ask")
async def ask(name: str, body: AskIn):
    answer = await memory.ask(_dataset(name), body.question, session_id=body.session_id)
    return {"answer": answer}


ALLOWED_UPLOADS = {".pdf", ".txt", ".md", ".csv", ".json"}


@app.post("/api/topics/{name}/upload")
async def upload_notes(name: str, file: UploadFile):
    dataset = _dataset(name)
    suffix = ("." + file.filename.rsplit(".", 1)[-1].lower()) if "." in file.filename else ""
    if suffix not in ALLOWED_UPLOADS:
        raise HTTPException(422, f"Unsupported file type {suffix or '(none)'} — "
                                 f"use {', '.join(sorted(ALLOWED_UPLOADS))}")
    content = await file.read()
    if not content:
        raise HTTPException(422, "File is empty")
    status = await memory.ingest_file(dataset, file.filename, content)
    store.bump_notes(name)
    return {"ok": True, "status": str(status), "filename": file.filename}


@app.post("/api/topics/{name}/quiz/start")
async def quiz_start(name: str):
    dataset = _dataset(name)
    session_id = f"quiz_{uuid.uuid4().hex[:12]}"
    store.start_session(name, session_id)
    weak = store.weak_concepts(name)
    question = await memory.quiz_question(dataset, avoid=[], weak_concepts=weak)
    if not question:
        raise HTTPException(409, "No study material yet — add notes first")
    return {"session_id": session_id, "question": question, "targeting": weak}


@app.post("/api/topics/{name}/quiz/answer")
async def quiz_answer(name: str, body: AnswerIn):
    dataset = _dataset(name)
    graded = await memory.grade_answer(dataset, body.question, body.answer,
                                       known_concepts=store.weak_concepts(name))
    await memory.record_qa(
        dataset, body.session_id, body.question, body.answer,
        context=graded["explanation"], correct=graded["correct"],
    )
    store.record_result(name, body.session_id, body.question,
                        graded["correct"], graded["concept"])
    asked = _asked_questions(name, body.session_id, body.question)
    weak = store.weak_concepts(name)
    next_question = await memory.quiz_question(dataset, avoid=asked, weak_concepts=weak)
    return {**graded, "next_question": next_question, "targeting": weak}


_session_questions: dict[str, list[str]] = {}


def _asked_questions(name: str, session_id: str, question: str) -> list[str]:
    asked = _session_questions.setdefault(session_id, [])
    if question not in asked:
        asked.append(question)
    return asked


@app.post("/api/topics/{name}/quiz/finish")
async def quiz_finish(name: str, body: SessionIn):
    _dataset(name)
    await memory.adapt(body.session_id)
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
    html = await memory.graph_html(_dataset(name))
    if not html:
        raise HTTPException(404, "Graph not available yet — add notes first")
    return HTMLResponse(html)


@app.get("/")
async def index():
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND), name="frontend")
