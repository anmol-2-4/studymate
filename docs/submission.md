# Submission kit

Everything to paste into the submission form, plus the two side-track
artifacts. Deadline: **July 5, 2026**.

## One-line pitch

StudyMate is a tutor that remembers you — it turns your own study notes into
a Cognee knowledge graph, quizzes you from it, and opens every new session by
targeting exactly the concepts you got wrong last time.

## Short description (~150 words)

Every AI study tool forgets you the moment you close the tab. StudyMate is
built on Cognee Cloud so it doesn't: your notes (pasted text or uploaded
PDF/Markdown files) become permanent graph memory, one dataset per topic.
Answers to your questions are grounded in your own material and cite the
exact note chunks as evidence. Quizzes are generated and graded against your
notes using Cognee's server-side LLM — the backend holds zero LLM keys. Every
quiz answer is recorded as scored `QAEntry` feedback in session memory, which
Cognee Cloud bridges into the permanent graph in the background; the next
session opens by attacking your tracked weak spots, and lets go of a concept
once you answer it correctly. Progress, session history, an embedded
interactive view of your actual knowledge graph, and a one-click `forget`
complete the memory lifecycle. Ships with two test harnesses that run against
live Cognee Cloud, including a 16-check browser end-to-end suite.

## Links

- Repo: https://github.com/anmol-2-4/studymate
- Demo video: https://youtu.be/klpzYBrldos
- Live demo: https://zshops-slight-list-cons.trycloudflare.com
  _(quick tunnel from the dev machine — **keep the laptop awake and the tunnel
  running through judging**; if it drops, restart with
  `~/.local/bin/cloudflared tunnel --url http://localhost:8300`, then update
  this URL and the README)_
- Blog post: _(add after publishing docs/blog.md)_

## Form reminders

- Track: **Best Build on Cognee Cloud**
- **Declare AI assistance on the form** (planned disclosure — do not skip)
- Team: solo

## Cognee bug report (file at github.com/topoteretes/cognee/issues)

**Title:** Cloud: re-ingesting into a previously forgotten dataset name fails
with 409 ProgrammingError; orphaned dataset record cannot be deleted

**Body:**

On Cognee Cloud (SDK 1.2.2, `cognee.serve()` direct mode), after
`forget(dataset="name")` succeeds, the dataset record remains visible in
`GET /api/v1/datasets/` and the name is permanently unusable:

1. `remember(data, dataset_name="name")` → `409 {"error": "An error occurred
   during remember: RetryError[... raised ProgrammingError]"}` — same result
   for text and file ingestion, while the same payload into a fresh dataset
   name succeeds.
2. `DELETE /api/v1/datasets/{id}` on the orphaned record → `500 Internal
   Server Error`.

Since dataset IDs are deterministic (name+user), any app that lets users
delete and re-create a topic hits this. Workaround we shipped: suffix every
dataset name with a random ID so names are never reused. Repro steps:
`remember` → `forget` → `remember` with the same `dataset_name`.

Found while building StudyMate for The Hangover Part AI hackathon.

## Social post draft (Buzz track)

> Every AI tutor forgets you the moment you close the tab.
>
> So I built StudyMate for the @WeMakeDevs × @cognee_ hackathon: it turns MY
> notes into a knowledge graph, quizzes me from them, and opens every session
> by targeting what I got wrong last time — and drops a concept once I master
> it.
>
> Real memory, not a prompt trick: wrong answers become scored feedback that
> reshapes the graph (Cognee Cloud bridges it in the background).
>
> Demo: youtu.be/klpzYBrldos — repo: github.com/anmol-2-4/studymate #TheHangoverPartAI
