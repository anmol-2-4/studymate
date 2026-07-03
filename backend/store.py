"""Tiny JSON store for app state: topics, quiz sessions, and per-topic stats.

All *memory* lives in Cognee Cloud — this file only tracks bookkeeping the UI
needs instantly (scores, session history, weak concepts).
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "store.json"
_lock = threading.Lock()


def _load() -> dict:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text())
    return {"topics": {}}


def _save(state: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(state, indent=2))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_topics() -> list[dict]:
    state = _load()
    return [
        {"name": name, **_topic_summary(topic)}
        for name, topic in sorted(state["topics"].items())
    ]


def _topic_summary(topic: dict) -> dict:
    correct = sum(s["correct"] for s in topic["sessions"])
    wrong = sum(s["wrong"] for s in topic["sessions"])
    total = correct + wrong
    return {
        "notes": topic["notes"],
        "sessions": len(topic["sessions"]),
        "correct": correct,
        "wrong": wrong,
        "mastery": round(correct / total * 100) if total else None,
    }


def add_topic(name: str):
    with _lock:
        state = _load()
        if name not in state["topics"]:
            state["topics"][name] = {
                "created": _now(), "notes": 0, "sessions": [], "missed": []
            }
            _save(state)


def remove_topic(name: str):
    with _lock:
        state = _load()
        state["topics"].pop(name, None)
        _save(state)


def get_topic(name: str) -> dict | None:
    return _load()["topics"].get(name)


def bump_notes(name: str):
    with _lock:
        state = _load()
        state["topics"][name]["notes"] += 1
        _save(state)


def start_session(name: str, session_id: str):
    with _lock:
        state = _load()
        state["topics"][name]["sessions"].append({
            "id": session_id, "started": _now(),
            "correct": 0, "wrong": 0, "adapted": False,
        })
        _save(state)


def _concept_key(concept: str) -> str:
    return concept.strip().lower().rstrip("s")


def record_result(name: str, session_id: str, question: str, correct: bool, concept: str):
    with _lock:
        state = _load()
        topic = state["topics"][name]
        for session in topic["sessions"]:
            if session["id"] == session_id:
                session["correct" if correct else "wrong"] += 1
                break
        if not correct:
            topic["missed"].append({"question": question, "concept": concept, "at": _now()})
            topic["missed"] = topic["missed"][-50:]
        elif concept:
            # mastered it — stop treating this concept as a weak spot
            topic["missed"] = [
                m for m in topic["missed"]
                if _concept_key(m["concept"]) != _concept_key(concept)
            ]
        _save(state)


def mark_adapted(name: str, session_id: str):
    with _lock:
        state = _load()
        for session in state["topics"][name]["sessions"]:
            if session["id"] == session_id:
                session["adapted"] = True
                break
        _save(state)


def weak_concepts(name: str, limit: int = 5) -> list[str]:
    topic = get_topic(name)
    if not topic:
        return []
    seen: dict[str, str] = {}
    for miss in reversed(topic["missed"]):
        concept = (miss.get("concept") or "").strip()
        if concept and _concept_key(concept) not in seen:
            seen[_concept_key(concept)] = concept
    return list(seen.values())[:limit]
