const $ = (id) => document.getElementById(id);
const ROWS = 5;
let token = sessionStorage.getItem("token");
let role = sessionStorage.getItem("role");
let username = sessionStorage.getItem("username");
let mode = "login";
let game = null;       // current game state from the server
let finished = false;  // true once the player clicked OK on the end-of-game message

function say(text, ok = false) {
  $("msg").textContent = text || "";
  $("msg").className = ok ? "ok" : "";
}

async function api(path, method = "GET", body) {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: "Bearer " + token } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401 && token) logout();
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.msg.replace(/^Value error, /, "")).join(". ") : d || "Something went wrong");
  }
  return data;
}

/* ---------- views ---------- */
function show() {
  $("authView").hidden = !!token;
  $("playerView").hidden = !(token && role === "player");
  $("adminView").hidden = !(token && role === "admin");
  $("who").hidden = !token;
  $("whoName").textContent = username ? `${username} (${role})` : "";
  say("");
  if (token && role === "player") loadStatus();
  if (token && role === "admin") $("dayDate").value = new Date().toLocaleDateString("en-CA");
}

function logout() {
  sessionStorage.clear();
  token = role = username = null;
  game = null;
  show();
}

/* ---------- auth ---------- */
function setMode(m) {
  mode = m;
  $("tabLogin").classList.toggle("active", m === "login");
  $("tabRegister").classList.toggle("active", m === "register");
  $("authSubmit").textContent = m === "login" ? "Log in" : "Create account";
  $("authHint").textContent = m === "register"
    ? "Username: at least 5 letters. Password: at least 5 characters with a letter, a number and one of $ % *"
    : "";
  say("");
}

$("tabLogin").onclick = () => setMode("login");
$("tabRegister").onclick = () => setMode("register");
$("logout").onclick = logout;

$("authForm").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const d = await api(`/api/auth/${mode}`, "POST", {
      username: $("username").value.trim(),
      password: $("password").value,
    });
    token = d.access_token; role = d.role; username = d.username;
    sessionStorage.setItem("token", token);
    sessionStorage.setItem("role", role);
    sessionStorage.setItem("username", username);
    $("password").value = "";
    show();
  } catch (err) { say(err.message); }
};

/* ---------- player ---------- */
function renderBoard() {
  const board = $("board");
  board.innerHTML = "";
  for (let r = 0; r < ROWS; r++) {
    const row = document.createElement("div");
    row.className = "rowtiles";
    const g = game && game.guesses[r];
    for (let c = 0; c < 5; c++) {
      const t = document.createElement("div");
      t.className = "tile" + (g ? " " + g.result[c] : "");
      t.textContent = g ? g.guess[c] : "";
      row.appendChild(t);
    }
    board.appendChild(row);
  }
}

function refreshControls(remaining) {
  const playing = game && game.status === "IN_PROGRESS" && !finished;
  $("guessForm").hidden = !playing;
  $("startBtn").hidden = playing;
  $("startBtn").disabled = remaining <= 0;
  $("quota").textContent = remaining > 0
    ? `${remaining} of 3 words left today.`
    : "You have used all 3 words for today. Come back tomorrow.";
  if (playing) $("guessInput").focus();
}

async function loadStatus() {
  try {
    const s = await api("/api/game/status");
    game = s.active_game;
    finished = false;
    renderBoard();
    refreshControls(s.games_remaining_today);
  } catch (err) { say(err.message); }
}

$("startBtn").onclick = async () => {
  say("");
  try {
    game = await api("/api/game/start", "POST");
    finished = false;
    renderBoard();
    const s = await api("/api/game/status");
    refreshControls(s.games_remaining_today);
  } catch (err) { say(err.message); }
};

$("guessInput").oninput = (e) => {
  e.target.value = e.target.value.toUpperCase().replace(/[^A-Z]/g, "");
};

$("guessForm").onsubmit = async (e) => {
  e.preventDefault();
  const guess = $("guessInput").value;
  if (!/^[A-Z]{5}$/.test(guess)) return say("Enter exactly 5 letters.");
  say("");
  try {
    game = await api(`/api/game/${game.game_id}/guess`, "POST", { guess });
    $("guessInput").value = "";
    renderBoard();
    if (game.status !== "IN_PROGRESS") {
      const won = game.status === "WON";
      // let the board paint before the blocking dialog opens
      setTimeout(async () => {
        alert(won ? `Congratulations! You guessed ${game.answer}.` : `Better luck next time. The word was ${game.answer}.`);
        finished = true;
        const s = await api("/api/game/status");
        refreshControls(s.games_remaining_today);
      }, 50);
    }
  } catch (err) { say(err.message); }
};

/* ---------- admin ---------- */
$("dayForm").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const r = await api(`/api/admin/reports/day?date=${$("dayDate").value}`);
    $("dUsers").textContent = r.users_played;
    $("dGames").textContent = r.games_played;
    $("dWins").textContent = r.correct_guesses;
    $("dayTable").hidden = false;
    say("");
  } catch (err) { say(err.message); }
};

$("userForm").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const r = await api(`/api/admin/reports/user?username=${encodeURIComponent($("reportUser").value.trim())}`);
    const body = $("userTable").querySelector("tbody");
    body.innerHTML = "";
    r.rows.forEach((x) => {
      const tr = document.createElement("tr");
      [x.date, x.words_tried, x.correct_guesses].forEach((v) => {
        const td = document.createElement("td");
        td.textContent = v;
        tr.appendChild(td);
      });
      body.appendChild(tr);
    });
    $("userTable").hidden = false;
    say(r.rows.length ? "" : `${r.username} has not played yet.`);
  } catch (err) { say(err.message); }
};

setMode("login");
show();
