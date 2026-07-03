"""End-to-end smoke test against Cognee Cloud: remember -> recall -> QA session
-> improve -> forget. Run from the repo root:

    .venv/bin/python scripts/smoke.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import memory  # noqa: E402

TOPIC = "Smoke Test Topic"
NOTES = (
    "The mitochondria is the powerhouse of the cell. It produces ATP through "
    "cellular respiration. The nucleus stores the cell's DNA. Ribosomes "
    "synthesize proteins. The cell membrane controls what enters and leaves the cell."
)


async def main():
    print("1. connect")
    ok = await memory.connect()
    if not ok:
        print("   FAIL: COGNEE_BASE_URL / COGNEE_API_KEY missing in .env")
        return 1
    print("   connected")

    print("2. remember (ingest notes)")
    status = await memory.ingest_notes(TOPIC, NOTES)
    print(f"   status: {status}")

    print("3. recall (ask)")
    answer = await memory.ask(TOPIC, "What produces ATP in the cell?")
    print(f"   answer: {answer[:200]}")

    print("4. quiz question generation")
    question = await memory.quiz_question(TOPIC, avoid=[], weak_concepts=[])
    print(f"   question: {question[:200]}")

    print("5. grade an answer")
    graded = await memory.grade_answer(TOPIC, question, "I have no idea")
    print(f"   graded: {graded}")

    print("6. record QA in session memory")
    await memory.record_qa(TOPIC, "smoke_session_1", question, "I have no idea",
                           context=graded["explanation"], correct=graded["correct"])
    print("   recorded")

    print("7. improve (bridge session -> graph)")
    result = await memory.adapt(TOPIC, "smoke_session_1")
    print(f"   improve result: {str(result)[:200]}")

    print("8. graph visualization")
    html = await memory.graph_html(TOPIC)
    print(f"   graph html: {'OK, ' + str(len(html)) + ' bytes' if html else 'NOT AVAILABLE'}")

    print("9. forget (cleanup)")
    result = await memory.wipe(TOPIC)
    print(f"   forget result: {str(result)[:200]}")

    await memory.disconnect()
    print("\nALL STEPS COMPLETED")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
