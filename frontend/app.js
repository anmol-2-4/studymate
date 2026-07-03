const $ = (id) => document.getElementById(id);

let currentTopic = null;
let quizSession = null;
let currentQuestion = null;

async function api(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const detail = (await response.json().catch(() => ({}))).detail;
    throw new Error(detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function toast(message, ms = 3500) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.add("hidden"), ms);
}

function busy(button, isBusy, label) {
  button.disabled = isBusy;
  if (label) button.textContent = isBusy ? "…" : label;
}

/* ---------- connection status ---------- */

async function refreshStatus() {
  const el = $("conn-status");
  try {
    const { connected } = await api("/status");
    el.className = `conn ${connected ? "conn-ok" : "conn-bad"}`;
    el.textContent = connected ? "cloud connected" : "no cloud key";
  } catch {
    el.className = "conn conn-bad";
    el.textContent = "backend down";
  }
}

/* ---------- topics ---------- */

async function refreshTopics() {
  const topics = await api("/topics");
  const list = $("topic-list");
  list.innerHTML = "";
  for (const topic of topics) {
    const item = document.createElement("div");
    item.className = `topic-item${topic.name === currentTopic ? " active" : ""}`;
    const mastery = topic.mastery === null ? "" :
      `<div class="mastery-bar"><div style="width:${topic.mastery}%"></div></div>`;
    item.innerHTML = `
      <div class="t-name"></div>
      <div class="t-meta">${topic.notes} notes · ${topic.sessions} sessions` +
      `${topic.mastery === null ? "" : ` · ${topic.mastery}% mastery`}</div>${mastery}`;
    item.querySelector(".t-name").textContent = topic.name;
    item.onclick = () => selectTopic(topic.name);
    list.appendChild(item);
  }
}

function selectTopic(name) {
  currentTopic = name;
  quizSession = null;
  $("empty-state").classList.add("hidden");
  $("workspace").classList.remove("hidden");
  $("topic-title").textContent = name;
  $("chat-log").innerHTML = "";
  $("notes-log").innerHTML = "";
  resetQuizUI();
  showTab("notes");
  refreshTopics();
}

$("btn-add-topic").onclick = async () => {
  const input = $("new-topic-name");
  const name = input.value.trim();
  if (!name) return;
  await api("/topics", { method: "POST", body: JSON.stringify({ name }) });
  input.value = "";
  await refreshTopics();
  selectTopic(name);
};
$("new-topic-name").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("btn-add-topic").click();
});

$("btn-forget").onclick = async () => {
  if (!confirm(`Erase ALL memory of "${currentTopic}"? Cognee forget() is permanent.`)) return;
  try {
    await api(`/topics/${encodeURIComponent(currentTopic)}`, { method: "DELETE" });
    toast(`🗑️ Forgot everything about ${currentTopic}`);
    currentTopic = null;
    $("workspace").classList.add("hidden");
    $("empty-state").classList.remove("hidden");
    refreshTopics();
  } catch (err) { toast(err.message); }
};

/* ---------- tabs ---------- */

function showTab(name) {
  document.querySelectorAll(".tab").forEach((t) =>
    t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((p) =>
    p.classList.toggle("hidden", p.id !== `tab-${name}`));
  if (name === "progress") loadProgress();
}
document.querySelectorAll(".tab").forEach((t) => (t.onclick = () => showTab(t.dataset.tab)));

/* ---------- notes ---------- */

$("btn-save-notes").onclick = async () => {
  const text = $("notes-input").value.trim();
  if (!text) return;
  const button = $("btn-save-notes");
  busy(button, true);
  $("notes-status").textContent = "Building knowledge graph… (this can take a minute)";
  try {
    await api(`/topics/${encodeURIComponent(currentTopic)}/notes`, {
      method: "POST", body: JSON.stringify({ text }),
    });
    const log = document.createElement("div");
    log.textContent = `✅ Remembered ${text.length} chars — ${new Date().toLocaleTimeString()}`;
    $("notes-log").prepend(log);
    $("notes-input").value = "";
    $("notes-status").textContent = "";
    toast("🧠 Notes stored in permanent graph memory");
    refreshTopics();
  } catch (err) {
    $("notes-status").textContent = "";
    toast(err.message);
  } finally { busy(button, false); }
};

/* ---------- ask ---------- */

function addMessage(kind, text) {
  const msg = document.createElement("div");
  msg.className = `msg ${kind}`;
  msg.textContent = text;
  $("chat-log").appendChild(msg);
  $("chat-log").scrollTop = $("chat-log").scrollHeight;
  return msg;
}

$("btn-ask").onclick = async () => {
  const input = $("ask-input");
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  addMessage("user", question);
  const thinking = addMessage("bot thinking", "recalling…");
  try {
    const { answer } = await api(`/topics/${encodeURIComponent(currentTopic)}/ask`, {
      method: "POST", body: JSON.stringify({ question }),
    });
    thinking.className = "msg bot";
    thinking.textContent = answer;
  } catch (err) {
    thinking.className = "msg bot";
    thinking.textContent = `⚠️ ${err.message}`;
  }
};
$("ask-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("btn-ask").click();
});

/* ---------- quiz ---------- */

let questionNumber = 0;

function resetQuizUI() {
  $("quiz-idle").classList.remove("hidden");
  $("quiz-active").classList.add("hidden");
  $("quiz-summary").classList.add("hidden");
  $("quiz-feedback").innerHTML = "";
}

function showQuestion(question, targeting) {
  questionNumber += 1;
  currentQuestion = question;
  $("quiz-qnum").textContent = `Question ${questionNumber}`;
  const target = targeting && targeting.length
    ? `<span class="badge target">🎯 targeting: ${targeting.join(", ")}</span>` : "";
  $("quiz-qnum").insertAdjacentHTML("afterend", "");
  document.querySelectorAll(".badge.target").forEach((b) => b.remove());
  if (target) $("quiz-qnum").insertAdjacentHTML("afterend", target);
  $("quiz-question").textContent = question;
  $("quiz-answer").value = "";
  $("quiz-answer").focus();
}

$("btn-quiz-start").onclick = async () => {
  const button = $("btn-quiz-start");
  busy(button, true, "Start quiz session");
  try {
    const data = await api(`/topics/${encodeURIComponent(currentTopic)}/quiz/start`, { method: "POST" });
    quizSession = data.session_id;
    questionNumber = 0;
    $("quiz-idle").classList.add("hidden");
    $("quiz-active").classList.remove("hidden");
    $("quiz-summary").classList.add("hidden");
    showQuestion(data.question, data.targeting);
    if (data.targeting.length) toast(`🎯 This session targets your weak spots: ${data.targeting.join(", ")}`);
  } catch (err) { toast(err.message); }
  finally { busy(button, false, "Start quiz session"); }
};

$("btn-quiz-submit").onclick = async () => {
  const answer = $("quiz-answer").value.trim();
  if (!answer || !quizSession) return;
  const button = $("btn-quiz-submit");
  busy(button, true, "Submit answer");
  $("quiz-feedback").innerHTML = `<div class="status">grading &amp; remembering…</div>`;
  try {
    const data = await api(`/topics/${encodeURIComponent(currentTopic)}/quiz/answer`, {
      method: "POST",
      body: JSON.stringify({ session_id: quizSession, question: currentQuestion, answer }),
    });
    const card = document.createElement("div");
    card.className = `feedback-card ${data.correct ? "good" : "bad"}`;
    card.textContent = `${data.correct ? "✅ Correct!" : "❌ Not quite."} ${data.explanation}`;
    $("quiz-feedback").innerHTML = "";
    $("quiz-feedback").appendChild(card);
    if (data.next_question) {
      setTimeout(() => {
        showQuestion(data.next_question, data.targeting);
        $("quiz-feedback").innerHTML = "";
      }, 3200);
    }
    refreshTopics();
  } catch (err) {
    $("quiz-feedback").innerHTML = "";
    toast(err.message);
  } finally { busy(button, false, "Submit answer"); }
};

$("btn-quiz-end").onclick = async () => {
  if (!quizSession) return;
  const button = $("btn-quiz-end");
  button.disabled = true;
  button.textContent = "Adapting memory…";
  try {
    const data = await api(`/topics/${encodeURIComponent(currentTopic)}/quiz/finish`, {
      method: "POST", body: JSON.stringify({ session_id: quizSession }),
    });
    const s = data.session;
    $("quiz-active").classList.add("hidden");
    $("quiz-summary").classList.remove("hidden");
    $("quiz-summary").innerHTML =
      `<strong>Session complete 🧠</strong><br>` +
      `Score: ${s.correct} correct · ${s.wrong} wrong<br>` +
      `Your answers were bridged into permanent memory with <code>improve()</code> — ` +
      `StudyMate re-weighted the graph around what you missed.<br>` +
      (data.weak_concepts.length
        ? `Next session will target: <strong>${data.weak_concepts.join(", ")}</strong>`
        : `No weak spots on record — nice work!`);
    quizSession = null;
    refreshTopics();
  } catch (err) { toast(err.message); }
  finally { button.disabled = false; button.textContent = "Finish session & adapt"; }
};

/* ---------- progress ---------- */

async function loadProgress() {
  try {
    const data = await api(`/topics/${encodeURIComponent(currentTopic)}/progress`);
    const s = data.summary;
    $("progress-cards").innerHTML = [
      [s.notes, "notes"],
      [s.sessions, "sessions"],
      [s.correct, "correct"],
      [s.wrong, "wrong"],
      [s.mastery === null ? "—" : `${s.mastery}%`, "mastery"],
    ].map(([n, l]) => `<div class="p-card"><div class="n">${n}</div><div class="l">${l}</div></div>`).join("");

    $("weak-list").innerHTML = data.weak_concepts.length
      ? data.weak_concepts.map((c) => `<li class="tag-wrong">⚠️ ${c}</li>`).join("")
      : "<li>No weak spots tracked yet — take a quiz!</li>";

    $("session-list").innerHTML = data.sessions.length
      ? data.sessions.slice().reverse().map((sess) =>
          `<li>${new Date(sess.started).toLocaleString()} — ` +
          `${sess.correct}✅ ${sess.wrong}❌ ` +
          `${sess.adapted ? '<span class="tag-adapted">memory adapted</span>' : ""}</li>`).join("")
      : "<li>No sessions yet.</li>";
  } catch (err) { toast(err.message); }
}

/* ---------- graph ---------- */

$("btn-graph-load").onclick = async () => {
  const button = $("btn-graph-load");
  busy(button, true, "Load graph");
  try {
    const response = await fetch(`/api/topics/${encodeURIComponent(currentTopic)}/graph`);
    if (!response.ok) throw new Error("Graph not ready — add notes first");
    const html = await response.text();
    const frame = $("graph-frame");
    frame.classList.remove("hidden");
    frame.srcdoc = html;
  } catch (err) { toast(err.message); }
  finally { busy(button, false, "Load graph"); }
};

/* ---------- init ---------- */

refreshStatus();
refreshTopics();
setInterval(refreshStatus, 30000);
