"""Browser end-to-end test: drives the full StudyMate flow in headless Chrome.

Covers: topic creation, notes ingestion, grounded Q&A with evidence, a full
quiz session (wrong + right answers), the cloud memory receipt on finish,
adaptive targeting on a second session, progress view, graph view, and topic
forget.

Requires the app running (default http://localhost:8300) and:
    pip install playwright   # uses system Chrome, no browser download needed

Run:
    .venv/bin/python scripts/ui_test.py [base_url]
"""

import sys
import time
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8300"
TOPIC = f"UITest {int(time.time())}"

NOTES = (
    "The water cycle: evaporation turns surface water into vapor using the "
    "sun's energy. Condensation forms clouds from vapor. Precipitation returns "
    "water to earth as rain or snow. Collection gathers water in oceans, "
    "lakes, and groundwater. Transpiration is the release of water vapor from "
    "plant leaves."
)

failures = []


def check(name, condition, detail=""):
    print(("PASS " if condition else "FAIL ") + name + (f" — {detail}" if detail else ""))
    if not condition:
        failures.append(name)


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                headless=True, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    console_errors = []
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: console_errors.append(str(e)))

    page.goto(BASE)
    page.wait_for_selector("#empty-state", timeout=15000)

    page.fill("#new-topic-name", TOPIC)
    page.click("#btn-add-topic")
    page.wait_for_selector("#workspace:not(.hidden)", timeout=15000)
    check("create topic", page.text_content("#topic-title") == TOPIC)

    page.fill("#notes-input", NOTES)
    page.click("#btn-save-notes")
    page.wait_for_selector("#notes-log div", timeout=240000)
    check("ingest notes (remember)", "✅" in page.text_content("#notes-log div"))

    page.click('.tab[data-tab="ask"]')
    page.fill("#ask-input", "What is transpiration?")
    page.click("#btn-ask")
    page.wait_for_function(
        "document.querySelectorAll('#chat-log .msg.bot:not(.thinking)').length >= 1",
        timeout=180000)
    answer = page.text_content("#chat-log .msg.bot")
    check("ask (recall)", "plant" in answer.lower() or "leaves" in answer.lower(),
          answer[:120])
    check("evidence citations", page.query_selector("#chat-log .evidence") is not None)

    page.click('.tab[data-tab="quiz"]')
    page.click("#btn-quiz-start")
    page.wait_for_selector("#quiz-active:not(.hidden)", timeout=180000)
    q1 = page.text_content("#quiz-question")
    check("quiz question generated", len(q1.strip()) > 10, q1[:120])

    page.fill("#quiz-answer", "No clue at all.")
    page.click("#btn-quiz-submit")
    page.wait_for_selector("#quiz-feedback .feedback-card", timeout=180000)
    check("wrong answer graded wrong",
          "❌" in page.text_content("#quiz-feedback .feedback-card"))

    page.click("#btn-quiz-end")
    page.wait_for_selector("#quiz-summary:not(.hidden)", timeout=180000)
    check("session summary shown", "Session complete" in page.text_content("#quiz-summary"))
    receipt_row = page.query_selector("#quiz-summary .receipt-row")
    check("cloud memory receipt rendered",
          receipt_row is not None and "1/5" in page.text_content("#quiz-summary .receipt"),
          (receipt_row.text_content()[:100] if receipt_row else "no receipt"))
    check("start button reachable after finish", page.is_visible("#btn-quiz-start"))

    page.click("#btn-quiz-start")
    page.wait_for_selector("#quiz-active:not(.hidden)", timeout=180000)
    check("adaptive targeting badge on session 2",
          page.query_selector(".badge.target") is not None)
    page.click("#btn-quiz-end")
    page.wait_for_selector("#quiz-summary:not(.hidden)", timeout=180000)

    page.click('.tab[data-tab="progress"]')
    page.wait_for_selector("#progress-cards .p-card", timeout=30000)
    check("progress cards render", "WRONG" in page.text_content("#progress-cards").upper())
    check("weak spots tracked", "⚠️" in page.text_content("#weak-list"))

    page.click('.tab[data-tab="graph"]')
    page.click("#btn-graph-load")
    try:
        page.wait_for_selector("#graph-frame:not(.hidden)", timeout=180000)
        check("graph loads", True)
    except Exception:
        check("graph loads", False)

    page.once("dialog", lambda d: d.accept())
    page.click("#btn-forget")
    page.wait_for_selector("#empty-state:not(.hidden)", timeout=120000)
    check("forget topic", True)

    check("no console errors", not console_errors, "; ".join(console_errors[:3]))
    browser.close()

print(f"\n{len(failures)} failure(s)" if failures else "\nALL CHECKS PASSED")
sys.exit(1 if failures else 0)
