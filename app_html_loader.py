from flask import Flask, request, jsonify, render_template_string, session as flask_session, abort, redirect, url_for
from pathlib import Path
import os
import requests

app = Flask(__name__)

# Needed so Flask can store each browser user's backend cookie jar in a signed browser cookie.
# For real deployment, set FLASK_SECRET_KEY in your environment.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-change-this-secret-key")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:4000")

# Folder scanned for page fragments like scheduler.html, auth.html, etc.
# By default this is the same folder as this Python file.
ROOT_DIR = Path(os.environ.get("HTML_ROOT", Path(__file__).resolve().parent)).resolve()

# HTML files with these names will not appear in the dropdown.
EXCLUDED_HTML_FILES = {"base.html", "layout.html"}


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


def list_html_pages():
    """Return page names for all *.html files in ROOT_DIR."""
    pages = []
    for file_path in sorted(ROOT_DIR.glob("*.html")):
        if file_path.name.startswith("_"):
            continue
        if file_path.name in EXCLUDED_HTML_FILES:
            continue
        pages.append(file_path.stem)
    return pages


def get_page_file(page_name):
    """Safely map /page_name to ROOT_DIR/page_name.html."""
    safe_pages = set(list_html_pages())
    if page_name not in safe_pages:
        return None
    return ROOT_DIR / f"{page_name}.html"


BASE_HTML = r"""
<!DOCTYPE html>
<html>
<head>
  <title>BU Scheduler Test UI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }

    h1 {
      margin: 0;
      font-size: 24px;
    }

    .muted {
      color: #666;
      font-size: 12px;
    }

    header .muted {
      color: #d1d5db;
    }

    .nav-box {
      min-width: 260px;
    }

    .nav-box label {
      display: block;
      font-size: 12px;
      color: #d1d5db;
      margin-bottom: 4px;
    }

    select {
      width: 100%;
      box-sizing: border-box;
      padding: 9px;
      border-radius: 8px;
      border: 1px solid #bbb;
      font-size: 14px;
    }

    #page-content {
      padding: 20px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>BU Course Scheduler Backend Test UI</h1>
      <div class="muted">Flask shell → page HTML fragments loaded from {{ root_dir }}</div>
    </div>

    <div class="nav-box">
      <label for="pageDropdown">HTML Page</label>
      <select id="pageDropdown" onchange="goToSelectedPage()">
        {% for p in pages %}
          <option value="/{{ p }}" {% if p == current_page %}selected{% endif %}>{{ p }}.html</option>
        {% endfor %}
      </select>
    </div>
  </header>

  <div id="page-content">
    {{ page_html | safe }}
  </div>

  <script>
    function goToSelectedPage() {
      const select = document.getElementById("pageDropdown");
      window.location.href = select.value;
    }
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    pages = list_html_pages()
    if not pages:
        return render_template_string(
            BASE_HTML,
            pages=[],
            current_page="",
            root_dir=str(ROOT_DIR),
            page_html="<section><h2>No HTML pages found</h2><p>Add scheduler.html, auth.html, etc. beside this Python file.</p></section>",
        )
    return redirect(url_for("page", page_name=pages[0]))


@app.route("/<page_name>")
def page(page_name):
    page_file = get_page_file(page_name)
    if not page_file:
        abort(404, description=f"No page found for {page_name}. Expected {page_name}.html in {ROOT_DIR}")

    page_html = page_file.read_text(encoding="utf-8")
    pages = list_html_pages()

    return render_template_string(
        BASE_HTML,
        pages=pages,
        current_page=page_name,
        root_dir=str(ROOT_DIR),
        page_html=page_html,
    )


@app.route("/pages")
def pages_api():
    return jsonify({"root": str(ROOT_DIR), "pages": list_html_pages()})


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
