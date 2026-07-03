# 🧠 StudyMate — a tutor that remembers you

Every AI tutor forgets you the moment you close the tab. StudyMate doesn't.

Built on **[Cognee Cloud](https://www.cognee.ai/)** for the WeMakeDevs × Cognee
hackathon *"The Hangover Part AI: Where's My Context?"* — **Best Build on Cognee
Cloud** track.

## What it does

Feed StudyMate your own study notes. It builds a knowledge graph of what *you*
are learning, then tutors you against it — and it remembers every session:

- **📝 Notes** — paste lecture notes / textbook excerpts; they become permanent
  graph memory.
- **💬 Ask** — question-answering grounded in *your* notes, not generic LLM
  knowledge.
- **🎯 Quiz** — StudyMate generates questions from your notes, grades your
  answers, and records every result. The next session doesn't start from zero:
  it **targets the concepts you got wrong last time**.
- **📈 Progress** — mastery per topic, weak spots, session history.
- **🕸️ Graph** — the actual knowledge graph Cognee built from your notes.
- **🗑️ Forget** — wipe a topic completely and re-learn it fresh.

## How it uses the Cognee memory lifecycle

| StudyMate feature | Cognee API |
|---|---|
| Ingest notes into a topic | `remember(text, dataset_name=topic)` — one dataset per topic |
| Answer questions from your notes | `recall(query, datasets=[topic], feedback_influence=0.5)` |
| Generate & grade quiz questions | `recall()` with custom `system_prompt` (server-side LLM) |
| Record every quiz answer | `remember(QAEntry(feedback_score=1..5), session_id=...)` — session memory |
| Adapt to your weak spots | `improve(dataset, session_ids=[...])` — feedback weights bridge into the permanent graph |
| Wipe a topic | `forget(dataset=topic)` |
| Visualize your knowledge | Cognee Cloud `GET /api/v1/visualize` |

The adaptive loop is the point: wrong answers become low-score `QAEntry`
feedback in session memory; `improve()` applies those feedback weights to the
graph; subsequent `recall()` calls (with `feedback_influence > 0`) and quiz
generation are steered toward exactly what you struggle with.

## Running it

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env   # add your Cognee Cloud tenant URL + API key

.venv/bin/uvicorn main:app --app-dir backend --port 8000
```

Open http://localhost:8000 — create a topic, paste notes, start studying.

Smoke-test the full memory lifecycle end to end:

```bash
.venv/bin/python scripts/smoke.py
```

## Stack

FastAPI · Cognee Cloud (Python SDK + REST) · vanilla JS, zero frontend
dependencies.
