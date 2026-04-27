from flask import Flask, request, jsonify, render_template_string, session as flask_session
import os
import requests

app = Flask(__name__)

# Needed so Flask can store each browser user's backend cookie jar in a signed browser cookie.
# For real deployment, set FLASK_SECRET_KEY in your environment.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-secret-key")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:4000")


def make_backend_session():
    """Create a requests session and load this browser user's saved backend cookies."""
    s = requests.Session()
    for name, value in flask_session.get("backend_cookies", {}).items():
        s.cookies.set(name, value)
    return s


def save_backend_cookies(s):
    """Save backend cookies back into the Flask browser session."""
    flask_session["backend_cookies"] = requests.utils.dict_from_cookiejar(s.cookies)
    flask_session.modified = True


HTML = r"""
<!DOCTYPE html>
<html>
<head>
  <title>BU Scheduler Backend Test UI</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      background: #f5f5f5;
      color: #222;
    }

    header {
      background: #111827;
      color: white;
      padding: 16px 24px;
    }

    h1 {
      margin: 0;
      font-size: 24px;
    }

    main {
      padding: 20px;
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 20px;
    }

    section {
      background: white;
      border-radius: 12px;
      padding: 16px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 20px;
    }

    h2 {
      margin-top: 0;
      font-size: 18px;
      border-bottom: 1px solid #ddd;
      padding-bottom: 8px;
    }

    h3 {
      margin-bottom: 8px;
      font-size: 15px;
    }

    input, textarea, button, select {
      width: 100%;
      box-sizing: border-box;
      padding: 9px;
      margin: 5px 0;
      border-radius: 8px;
      border: 1px solid #bbb;
      font-size: 14px;
    }

    textarea {
      min-height: 70px;
      resize: vertical;
    }

    button {
      background: #2563eb;
      color: white;
      border: none;
      cursor: pointer;
      font-weight: bold;
    }

    button:hover {
      background: #1d4ed8;
    }

    .danger {
      background: #dc2626;
    }

    .danger:hover {
      background: #b91c1c;
    }

    .secondary {
      background: #4b5563;
    }

    .secondary:hover {
      background: #374151;
    }

    .success {
      background: #059669;
    }

    .success:hover {
      background: #047857;
    }

    .small-button {
      width: auto;
      padding: 6px 10px;
      font-size: 12px;
      margin-right: 5px;
    }

    .response-box {
      background: #111827;
      color: #d1fae5;
      padding: 12px;
      border-radius: 10px;
      overflow: auto;
      max-height: 360px;
      font-size: 12px;
      white-space: pre-wrap;
    }

    .layout-wide {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 16px;
    }

    .course-palette {
      background: #f9fafb;
      border: 1px dashed #bbb;
      border-radius: 10px;
      padding: 10px;
      min-height: 200px;
    }

    .course-card {
      background: #e0ecff;
      border: 1px solid #93c5fd;
      border-radius: 10px;
      padding: 10px;
      margin: 8px 0;
      cursor: grab;
      user-select: none;
    }

    .course-card.selected {
      outline: 3px solid #f59e0b;
      background: #fef3c7;
    }

    .course-code {
      font-weight: bold;
      font-size: 14px;
    }

    .course-comment {
      font-size: 12px;
      color: #444;
      margin-top: 4px;
    }

    .terms-grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(170px, 1fr));
      gap: 12px;
    }

    .term-box {
      background: #f9fafb;
      border: 2px dashed #cbd5e1;
      border-radius: 12px;
      padding: 10px;
      min-height: 220px;
    }

    .term-box:hover {
      border-color: #2563eb;
      background: #eff6ff;
    }

    .term-title {
      font-weight: bold;
      margin-bottom: 8px;
      text-align: center;
    }

    .course-search-results {
      max-height: 250px;
      overflow: auto;
      border: 1px solid #ddd;
      border-radius: 10px;
      padding: 8px;
      background: #fafafa;
    }

    .result-item {
      border-bottom: 1px solid #ddd;
      padding: 8px;
      cursor: pointer;
    }

    .result-item:hover {
      background: #e5e7eb;
    }

    .muted {
      color: #666;
      font-size: 12px;
    }

    .top-row {
      display: flex;
      gap: 8px;
    }

    .top-row button {
      flex: 1;
    }

    .status-pill {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 999px;
      background: #e5e7eb;
      color: #111827;
      font-size: 12px;
      margin-top: 6px;
    }
  </style>
</head>

<body>
  <header>
    <h1>BU Course Scheduler Backend Test UI</h1>
    <div class="muted">Flask test UI → Node backend through Flask proxy</div>
    <div class="status-pill" id="cookieStatus">Checking session...</div>
  </header>

  <main>
    <div>
      <section>
        <h2>Server</h2>
        <button onclick="healthCheck()">Health Check</button>
        <button onclick="getMe()">Get Current User</button>
        <button class="secondary" onclick="checkFlaskSession()">Check Flask Cookie Storage</button>
        <button class="danger" onclick="clearFlaskSession()">Clear Stored Flask Session</button>
      </section>

      <section>
        <h2>Auth</h2>

        <h3>Register</h3>
        <input id="registerEmail" placeholder="email@bu.edu">
        <input id="registerPassword" type="password" placeholder="password">
        <input id="registerName" placeholder="display name">
        <button onclick="registerUser()">Register</button>

        <h3>Verify Email</h3>
        <input id="verifyEmail" placeholder="email@bu.edu">
        <input id="verifyCode" placeholder="6 digit code">
        <button onclick="verifyEmail()">Verify</button>
        <button class="secondary" onclick="resendVerificationCode()">Resend Verification Code</button>

        <h3>Login</h3>
        <input id="loginEmail" placeholder="email@bu.edu">
        <input id="loginPassword" type="password" placeholder="password">
        <button onclick="loginUser()">Login</button>
        <button class="secondary" onclick="logoutUser()">Logout</button>
      </section>

      <section>
        <h2>Forgot Password</h2>
        <h3>Send Reset Code</h3>
        <input id="forgotEmail" placeholder="email@bu.edu">
        <button onclick="forgotPassword()">Send Password Reset Code</button>

        <h3>Reset Password</h3>
        <input id="resetEmail" placeholder="email@bu.edu">
        <input id="resetCode" placeholder="6 digit reset code">
        <input id="newPassword" type="password" placeholder="new password">
        <button class="success" onclick="resetPassword()">Reset Password</button>
      </section>

      <section>
        <h2>Course Search</h2>
        <input id="courseQuery" placeholder="Search course, instructor, status...">
        <button onclick="searchCourses()">Search Courses</button>

        <div class="course-search-results" id="courseResults">
          <div class="muted">Search results will appear here. Click a result to add it to the course palette.</div>
        </div>
      </section>

      <section>
        <h2>Raw API Response</h2>
        <pre class="response-box" id="responseBox">No response yet.</pre>
      </section>
    </div>

    <div>
      <section>
        <h2>Schedule Builder</h2>

       <input id="scheduleTitle" value="My EE Four-Year Plan" placeholder="Schedule title">

<select id="scheduleMajor">
  <option value="">Select major</option>
  <option value="Electrical Engineering">Electrical Engineering</option>
  <option value="Computer Engineering">Computer Engineering</option>
  <option value="Mechanical Engineering">Mechanical Engineering</option>
  <option value="Biomedical Engineering">Biomedical Engineering</option>
  <option value="Computer Science">Computer Science</option>
  <option value="Other">Other</option>
</select>

<textarea id="scheduleComments" placeholder="Schedule comments">Testing schedule from Flask UI.</textarea>

        <div class="layout-wide">
          <div>
            <h3>Course Palette</h3>
            <div class="muted">
              Drag a course into a semester, or click a course then click a semester box.
            </div>

            <input id="manualCourseCode" placeholder="Example: ENG EC 327">
            <input id="manualCourseComment" placeholder="Optional comment">
            <button onclick="addManualCourse()">Add Course Box</button>

            <div class="course-palette" id="coursePalette" ondrop="dropCourse(event)" ondragover="allowDrop(event)">
              <div class="course-card" draggable="true" onclick="selectCourse(this)" ondragstart="dragCourse(event)" data-code="CAS MA 123" data-comment="Calculus I">
                <div class="course-code">CAS MA 123</div>
                <div class="course-comment">Calculus I</div>
              </div>

              <div class="course-card" draggable="true" onclick="selectCourse(this)" ondragstart="dragCourse(event)" data-code="ENG EK 125" data-comment="Programming for Engineers">
                <div class="course-code">ENG EK 125</div>
                <div class="course-comment">Programming for Engineers</div>
              </div>

              <div class="course-card" draggable="true" onclick="selectCourse(this)" ondragstart="dragCourse(event)" data-code="ENG EC 327" data-comment="Computer elective option">
                <div class="course-code">ENG EC 327</div>
                <div class="course-comment">Computer elective option</div>
              </div>

              <div class="course-card" draggable="true" onclick="selectCourse(this)" ondragstart="dragCourse(event)" data-code="Hub Elective" data-comment="Choose Hub requirement">
                <div class="course-code">Hub Elective</div>
                <div class="course-comment">Choose Hub requirement</div>
              </div>
            </div>
          </div>

          <div>
            <h3>Terms</h3>
            <div class="top-row">
              <button onclick="loadMySchedule()">Load My Schedule</button>
              <button onclick="saveSchedule()">Save/Update My Schedule</button>
              <button class="secondary" onclick="previewSchedule()">Preview JSON</button>
            </div>

            <div class="terms-grid" id="termsGrid">
              <div class="term-box" data-term="Fall 2025" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Fall 2025</div></div>
              <div class="term-box" data-term="Spring 2026" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Spring 2026</div></div>
              <div class="term-box" data-term="Fall 2026" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Fall 2026</div></div>
              <div class="term-box" data-term="Spring 2027" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Spring 2027</div></div>
              <div class="term-box" data-term="Fall 2027" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Fall 2027</div></div>
              <div class="term-box" data-term="Spring 2028" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Spring 2028</div></div>
              <div class="term-box" data-term="Fall 2028" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Fall 2028</div></div>
              <div class="term-box" data-term="Spring 2029" onclick="termClicked(this)" ondrop="dropCourse(event)" ondragover="allowDrop(event)"><div class="term-title">Spring 2029</div></div>
            </div>

            <br>
            <button class="danger" onclick="clearSchedule()">Clear Schedule Boxes</button>
          </div>
        </div>
      </section>

      <section>
        <h2>Public Schedules</h2>
        <button onclick="getAllSchedules()">Get All Public Schedules</button>
        <input id="scheduleIdInput" placeholder="Schedule ID">
        <button onclick="getOneSchedule()">Get One Schedule</button>
        <button class="danger" onclick="deleteSchedule()">Delete Schedule by ID</button>
      </section>
    </div>
  </main>

<script>
let selectedCourse = null;
let draggedCourseId = null;
let nextCourseId = 1;

function saveAuthFields() {
  const ids = ["registerEmail", "verifyEmail", "loginEmail", "forgotEmail", "resetEmail"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) localStorage.setItem(id, el.value || "");
  });
}

function loadAuthFields() {
  const ids = ["registerEmail", "verifyEmail", "loginEmail", "forgotEmail", "resetEmail"];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el && localStorage.getItem(id)) el.value = localStorage.getItem(id);
    if (el) el.addEventListener("input", saveAuthFields);
  });
}

function showResponse(data) {
  const box = document.getElementById("responseBox");
  if (typeof data === "string") {
    box.textContent = data;
  } else {
    box.textContent = JSON.stringify(data, null, 2);
  }
}

async function api(method, path, body = null) {
  const options = {
    method,
    headers: {
      "Content-Type": "application/json"
    },
    credentials: "same-origin"
  };

  if (body !== null) {
    options.body = JSON.stringify(body);
  }

  const res = await fetch("/proxy" + path, options);
  const text = await res.text();

  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = text;
  }

  showResponse({ status: res.status, data });
  await checkFlaskSession(false);
  return { status: res.status, data };
}

function makeCourseCard(code, comment = "") {
  const card = document.createElement("div");
  card.className = "course-card";
  card.draggable = true;
  card.dataset.code = code;
  card.dataset.comment = comment;
  card.id = "course-card-" + nextCourseId++;

  card.onclick = function(event) {
    event.stopPropagation();
    selectCourse(card);
  };

  card.ondragstart = dragCourse;

  card.innerHTML = `
    <div class="course-code">${escapeHtml(code)}</div>
    <div class="course-comment">${escapeHtml(comment || "")}</div>
    <button class="small-button danger" onclick="removeCard(event, this)">Remove</button>
  `;

  return card;
}

function removeCard(event, button) {
  event.stopPropagation();
  const card = button.closest(".course-card");
  if (selectedCourse === card) selectedCourse = null;
  card.remove();
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function selectCourse(card) {
  document.querySelectorAll(".course-card").forEach(c => c.classList.remove("selected"));
  selectedCourse = card;
  card.classList.add("selected");
}

function termClicked(termBox) {
  if (!selectedCourse) return;
  termBox.appendChild(selectedCourse);
  selectedCourse.classList.remove("selected");
  selectedCourse = null;
}

function allowDrop(event) { event.preventDefault(); }

function dragCourse(event) {
  if (!event.target.id) event.target.id = "course-card-" + nextCourseId++;
  draggedCourseId = event.target.id;
  event.dataTransfer.setData("text/plain", draggedCourseId);
}

function dropCourse(event) {
  event.preventDefault();
  const id = event.dataTransfer.getData("text/plain") || draggedCourseId;
  const card = document.getElementById(id);
  if (!card) return;
  event.currentTarget.appendChild(card);
}

function addManualCourse() {
  const code = document.getElementById("manualCourseCode").value.trim();
  const comment = document.getElementById("manualCourseComment").value.trim();
  if (!code) { alert("Enter a course code."); return; }
  const card = makeCourseCard(code, comment);
  document.getElementById("coursePalette").appendChild(card);
  document.getElementById("manualCourseCode").value = "";
  document.getElementById("manualCourseComment").value = "";
}

function buildScheduleJson() {
  const title = document.getElementById("scheduleTitle").value.trim();
  const major = document.getElementById("scheduleMajor").value.trim();
  const comments = document.getElementById("scheduleComments").value.trim();
  const terms = {};

  document.querySelectorAll(".term-box").forEach(termBox => {
    const termName = termBox.dataset.term;
    const courses = [];
    termBox.querySelectorAll(".course-card").forEach(card => {
      courses.push({ course_code: card.dataset.code, comments: card.dataset.comment || "" });
    });
    terms[termName] = courses;
  });

  return {
  title,
  major,
  comments,
  terms
};
}

function previewSchedule() { showResponse(buildScheduleJson()); }

function clearSchedule() {
  const palette = document.getElementById("coursePalette");
  document.querySelectorAll(".term-box .course-card").forEach(card => palette.appendChild(card));
}

function renderSchedule(schedule) {
  document.getElementById("scheduleTitle").value = schedule.title || "";
  document.getElementById("scheduleMajor").value = schedule.major || "";
  document.getElementById("scheduleComments").value = schedule.comments || "";

  document.querySelectorAll(".term-box").forEach(termBox => {
    const title = termBox.querySelector(".term-title");
    termBox.innerHTML = "";
    termBox.appendChild(title);
  });

  const terms = schedule.terms || {};
  for (const [termName, courses] of Object.entries(terms)) {
    let termBox = document.querySelector(`.term-box[data-term="${termName}"]`);
    if (!termBox) {
      termBox = document.createElement("div");
      termBox.className = "term-box";
      termBox.dataset.term = termName;
      termBox.onclick = function() { termClicked(termBox); };
      termBox.ondrop = dropCourse;
      termBox.ondragover = allowDrop;
      termBox.innerHTML = `<div class="term-title">${escapeHtml(termName)}</div>`;
      document.getElementById("termsGrid").appendChild(termBox);
    }
    courses.forEach(course => {
      const card = makeCourseCard(course.course_code, course.comments || course.comment || course.course_title || "");
      termBox.appendChild(card);
    });
  }
}

// -----------------------------
// Endpoint tests
// -----------------------------
async function healthCheck() { await api("GET", "/health"); }

async function checkFlaskSession(show = true) {
  const res = await fetch("/session-status", { credentials: "same-origin" });
  const data = await res.json();
  document.getElementById("cookieStatus").textContent = data.hasBackendCookies
    ? "Backend login cookie stored in Flask session"
    : "No backend login cookie stored";
  if (show) showResponse(data);
  return data;
}

async function clearFlaskSession() {
  const res = await fetch("/clear-session", { method: "POST", credentials: "same-origin" });
  const data = await res.json();
  showResponse(data);
  await checkFlaskSession(false);
}

async function registerUser() {
  const email = document.getElementById("registerEmail").value.trim();
  const password = document.getElementById("registerPassword").value;
  const displayName = document.getElementById("registerName").value.trim();
  document.getElementById("verifyEmail").value = email;
  document.getElementById("loginEmail").value = email;
  saveAuthFields();
  await api("POST", "/api/auth/register", { email, password, displayName });
}

async function resendVerificationCode() {
  const email = document.getElementById("verifyEmail").value.trim() || document.getElementById("registerEmail").value.trim();
  document.getElementById("verifyEmail").value = email;
  saveAuthFields();
  await api("POST", "/api/auth/resend-verification-code", { email });
}

async function verifyEmail() {
  const email = document.getElementById("verifyEmail").value.trim();
  const code = document.getElementById("verifyCode").value.trim();
  await api("POST", "/api/auth/verify-email", { email, code });
}

async function loginUser() {
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;
  saveAuthFields();
  await api("POST", "/api/auth/login", { email, password });
}

async function logoutUser() {
  await api("POST", "/api/auth/logout");
  await clearFlaskSession();
}

async function forgotPassword() {
  const email = document.getElementById("forgotEmail").value.trim();
  document.getElementById("resetEmail").value = email;
  saveAuthFields();
  await api("POST", "/api/auth/forgot-password", { email });
}

async function resetPassword() {
  const email = document.getElementById("resetEmail").value.trim();
  const code = document.getElementById("resetCode").value.trim();
  const newPassword = document.getElementById("newPassword").value;
  await api("POST", "/api/auth/reset-password", { email, code, newPassword });
}

async function getMe() { await api("GET", "/api/auth/me"); }

async function searchCourses() {
  const q = document.getElementById("courseQuery").value.trim();
  const result = await api("GET", "/api/courses?q=" + encodeURIComponent(q));
  const container = document.getElementById("courseResults");
  container.innerHTML = "";

  const courses = result.data?.data?.results || result.data?.results || [];
  if (!Array.isArray(courses) || courses.length === 0) {
    container.innerHTML = `<div class="muted">No results found.</div>`;
    return;
  }

  courses.slice(0, 50).forEach(course => {
    const item = document.createElement("div");
    item.className = "result-item";
    const code = course.course_code || "Unknown";
    const title = course.course_title || course.hub?.name || "";
    const instructor = course.instructor || "";
    const status = course.status || "";
    item.innerHTML = `<strong>${escapeHtml(code)}</strong><br>${escapeHtml(title)}<br><span class="muted">${escapeHtml(instructor)} ${escapeHtml(status)}</span>`;
    item.onclick = () => document.getElementById("coursePalette").appendChild(makeCourseCard(code, title));
    container.appendChild(item);
  });
}

async function saveSchedule() {
  const schedule = buildScheduleJson();
  if (!schedule.title) { alert("Schedule title required."); return; }
  await api("POST", "/api/schedules", schedule);
}

async function loadMySchedule() {
  const result = await api("GET", "/api/my-schedule");
  const schedule = result.data?.data?.schedule || result.data?.schedule;
  if (!schedule) { alert("No saved schedule found for this logged-in user."); return; }
  renderSchedule(schedule);
}

async function getAllSchedules() { await api("GET", "/api/schedules"); }

async function getOneSchedule() {
  const id = document.getElementById("scheduleIdInput").value.trim();
  if (!id) { alert("Enter a schedule ID."); return; }
  await api("GET", "/api/schedules/" + encodeURIComponent(id));
}

async function deleteSchedule() {
  const id = document.getElementById("scheduleIdInput").value.trim();
  if (!id) { alert("Enter a schedule ID."); return; }
  await api("DELETE", "/api/schedules/" + encodeURIComponent(id));
}

window.addEventListener("load", () => {
  loadAuthFields();
  checkFlaskSession(false);
});
</script>

</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/session-status")
def session_status():
    cookies = flask_session.get("backend_cookies", {})
    return jsonify({
        "hasBackendCookies": bool(cookies),
        "backendCookieNames": list(cookies.keys()),
        "note": "Cookies are stored per browser in Flask's signed session cookie, not in one shared global Python session.",
    })


@app.route("/clear-session", methods=["POST"])
def clear_session():
    flask_session.pop("backend_cookies", None)
    flask_session.modified = True
    return jsonify({"message": "Cleared Flask-stored backend cookies."})


@app.route("/proxy/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    backend_path = "/" + path
    url = BACKEND_URL + backend_path
    backend_session = make_backend_session()

    try:
        if request.method == "GET":
            response = backend_session.get(url, params=request.args, timeout=20)
        elif request.method == "POST":
            response = backend_session.post(url, json=request.get_json(silent=True), timeout=20)
        elif request.method == "PUT":
            response = backend_session.put(url, json=request.get_json(silent=True), timeout=20)
        elif request.method == "DELETE":
            response = backend_session.delete(url, json=request.get_json(silent=True), timeout=20)
        else:
            return jsonify({"error": "Unsupported method"}), 405

        save_backend_cookies(backend_session)

        # If backend logout clears its cookie, also clear our stored cookie jar.
        if path == "api/auth/logout" and request.method == "POST" and response.status_code < 400:
            flask_session.pop("backend_cookies", None)
            flask_session.modified = True

        try:
            data = response.json()
            return jsonify(data), response.status_code
        except Exception:
            return response.text, response.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Could not connect to backend.",
            "detail": f"Make sure your Node backend is running at {BACKEND_URL}."
        }), 502

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "Backend request timed out.",
            "detail": "The backend did not respond before the Flask proxy timeout."
        }), 504

    except Exception as e:
        return jsonify({
            "error": "Proxy error.",
            "detail": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
