# I built a tutor that actually remembers me — on Cognee Cloud, in two days

*Draft for the WeMakeDevs × Cognee hackathon blog track.*

Every AI study tool I've used has the same flaw: it doesn't know me. It
doesn't know that I've confused the Coffman conditions three times this week,
or that I finally understand paging and never need another paging question
again. Close the tab and the tutor gets amnesia — which, fittingly, was the
whole theme of this hackathon: *"The Hangover Part AI: Where's My Context?"*

So for the Cognee Cloud track I built **StudyMate**: paste or upload your own
study notes, and it becomes a tutor with a persistent, adapting memory of
*you*. Here's what I learned building it in two days.

## The idea: map the product onto the memory lifecycle

Cognee's API is four verbs — `remember`, `recall`, `improve`, `forget` — and
the trick that made StudyMate work was refusing to treat them as a database.
Each product feature IS one of the verbs:

- **A topic is a dataset.** Notes go in with `remember(notes,
  dataset_name=topic)`; deleting a topic is `forget(dataset=topic)`. Clean
  one-to-one mapping, no glue schema.
- **Q&A is `recall`** with `include_references=True`, which appends a
  deterministic evidence block citing the exact chunk of your notes the answer
  came from. A tutor that can show its receipts.
- **A quiz session is a Cognee session.** Every graded answer becomes a
  `QAEntry` with a `feedback_score` from 1 to 5 in session memory.
- **Adaptation is the bridge.** Cognee Cloud takes that scored session
  feedback and folds it into the permanent graph in the background. Next
  session, StudyMate opens by targeting exactly the concepts you got wrong —
  and drops them once you answer correctly.

The quiz generation and grading also run on `recall` with task-specific
system prompts, which means the LLM lives server-side in Cognee Cloud. My
backend has **zero LLM keys** in it.

## Four things the docs won't tell you (I found out the hard way)

I test against the real service, not my assumptions, and Cognee Cloud had
four surprises for me:

**1. Cloud `recall()` returns plain dicts, not Pydantic objects.** The local
SDK returns typed objects you read with `result.text`. Point the same SDK at
the cloud with `cognee.serve()` and you get JSON dicts back. My first recall
"worked" but every answer looked empty because `getattr(dict, "text")` is
`None`. Normalize both shapes.

**2. Auth is `X-Api-Key` — and ONLY `X-Api-Key`.** I sent both `X-Api-Key`
and `Authorization: Bearer` headers to the REST API to cover my bases, and
got `{"detail": "Invalid header"}`. Belt-and-suspenders actively breaks it.

**3. There is no `improve` endpoint on the cloud — because you don't need
one.** The SDK's `cognee.improve()` 404s against Cognee Cloud. I dug through
the OpenAPI spec expecting to find a renamed route, and instead found this in
the `remember` docs: session data is *"bridged into the permanent graph in
the background."* The cloud runs the enrichment step for you, continuously.
My "Finish session & adapt" button went from triggering a pipeline to simply
reporting bridging status from `GET /api/v1/sessions/{id}`.

**4. `query_text` is for retrieval only.** For grading, I originally sent
"Question: … Student's answer: …" as the query and asked the system prompt to
grade it. The grader kept replying "no answer was provided" — the student's
answer never reached the LLM, because the query is used to search the graph,
not as prompt content. Anything the model must *see* goes in the
`system_prompt`; the query should be the retrieval anchor (the question
text).

## Testing: drive the real thing

Two harnesses ship in the repo, and both run against live Cognee Cloud: a
smoke test that exercises the full lifecycle end-to-end in nine steps, and a
Playwright script that drives the actual UI in headless Chrome — 14 checks,
including the one that matters: *does session 2 open with a targeting badge
for the concept I missed in session 1, and does it disappear after I get it
right?* It does, and watching that pass was the moment the project felt real.

That browser test caught three real bugs the API tests couldn't: the grading
prompt issue above, a button that became unreachable after finishing a
session, and "Coffman condition" vs "Coffman conditions" being tracked as two
different weaknesses.

## Where this goes

StudyMate is a hackathon build, but the shape feels right: the memory layer
carries the intelligence, so the app stays small — FastAPI, vanilla JS, no
frontend dependencies, no model keys. Spaced repetition scheduled off the
weak-concept list is the obvious next step; the graph already knows what I
need to see again and when I last saw it.

Repo: https://github.com/anmol-2-4/studymate

*Built solo for the WeMakeDevs × Cognee hackathon, June 29 – July 5, 2026.*
