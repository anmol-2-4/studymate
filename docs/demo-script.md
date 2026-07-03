# Demo video script (~2.5 min)

Target: show all four memory-lifecycle verbs working, with the adaptive loop
as the climax. Record at 1440×900, app at http://localhost:8300 with a clean
store (delete `data/store.json` and forget old topics first).

## 0:00 — Hook (voice over title screen)

> "Every AI tutor forgets you the moment you close the tab. I built one that
> doesn't. This is StudyMate, running on Cognee Cloud."

## 0:15 — Remember

- Create topic **Operating Systems**.
- Upload `demo/operating-systems.md` (or paste it).
- While it processes: "My notes are being turned into a knowledge graph —
  entities, relationships, the works. This is Cognee's `remember`."
- Flip to the **Graph** tab, load it, zoom around for 3–4 seconds:
  "…and this is the actual graph it built from one page of my notes."

## 0:50 — Recall

- **Ask** tab: "What are the four conditions required for deadlock?"
- Expand the **📎 evidence** collapsible:
  "Every answer is grounded in MY notes — it cites the exact chunk it came
  from. That's `recall` with references."
- Follow up: "Which of those is broken by resource ordering?" —
  "Follow-ups work because the chat is session-aware."

## 1:20 — Quiz session 1 (get things wrong on purpose)

- Start quiz. Answer the first question wrong ("no idea").
- Show the red feedback card with the correct explanation.
- Answer one more (wrong or right), then **Finish session & adapt**.
- Read the summary line: "…every answer was recorded as scored feedback in
  session memory, and Cognee Cloud is bridging it into my permanent graph."

## 1:50 — The climax: it remembers you

- Open **Progress**: point at the weak-spots list. "It knows what I'm bad at."
- Start **quiz session 2**. Point at the 🎯 **targeting badge**:
  "New session — and it opens by attacking exactly what I missed last time.
  No AI tutor I've used does this."
- Answer the targeted question CORRECTLY this time. Finish session.
- Progress again: the mastered concept has **dropped off the weak list**.
  "…and once I get it right, it lets go. That's a real feedback loop, not a
  prompt trick."

## 2:20 — Forget + close

- Click **Forget topic** on a throwaway topic: "And when exams are done —
  `forget`. Gone from the graph, permanently."
- Close: "StudyMate. Remember, recall, adapt, forget — a tutor with an actual
  memory, built on Cognee Cloud. Repo link below."

## Checklist before recording

- [ ] `data/store.json` deleted, old topics forgotten (clean sidebar)
- [ ] Cloud connected (green dot bottom-left)
- [ ] `demo/operating-systems.md` ready to upload
- [ ] Answer session 2's targeted question COMPLETELY — if it asks for a
      definition AND an example, give both, or the strict grader marks it
      wrong and the weak spot won't drop off

## Observed latencies (from dry run — plan cuts or narration over these)

| Step | Wait |
|---|---|
| Upload + graph build | ~25–40 s |
| Graph tab load | ~9 s |
| Ask answer | ~5–8 s |
| Quiz start / next question | ~10–17 s |
| Grading an answer | ~15–35 s |
| Finish session / forget | ~2 s |

Total waiting across the whole demo ≈ 2 min — record long, cut to 2:30.
