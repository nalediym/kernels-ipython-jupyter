"""The kernel behind the dumb notebook.

This is the "backend" half of web/notebook.html. The browser page is just
HTML — it cannot run Python. This server can: its execution engine is the very
`StackBuilder` you assembled in build/. So the code you wrote from scratch
literally becomes the kernel that brings the front-end to life.

The browser ⇄ HTTP ⇄ this server IS the shell⇄kernel split, one more time:
  - the page is the SHELL (what you touch),
  - a POST /execute is the message (Jupyter sends signed JSON over ZeroMQ;
    we send JSON over HTTP — same idea, simpler wire),
  - this process is the KERNEL (holds the namespace, runs the code).

Run:  uv run python web/server.py    →  then open  http://localhost:8799
"""
import io
import os
import sys
import json
import contextlib
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "build"))
from stack_builder import StackBuilder  # noqa: E402 — the kernel you built

PORT = int(os.environ.get("PORT", "8799"))
HERE = os.path.dirname(os.path.abspath(__file__))

# Assemble the kernel ONCE: REPL (Day 1) + magics (Day 2). The notebook
# semantics — Out[n], execution_count — are the FRONT-END's job, handled below,
# exactly as a real kernel returns a value and the UI labels it Out[n].
BUILDER = StackBuilder().build_repl().build_magics()
STACK = BUILDER.result()
COUNT = {"n": 0}


def run_code(code):
    """Execute one cell against the persistent kernel namespace."""
    COUNT["n"] += 1
    buf = io.StringIO()
    result_repr, error = None, None
    try:
        with contextlib.redirect_stdout(buf):
            value = STACK._run(code)
        if value is not None:
            result_repr = repr(value)
            STACK.ns["_"] = value
    except Exception:
        error = traceback.format_exc(limit=2)
    return {
        "execution_count": COUNT["n"],
        "stdout": buf.getvalue(),
        "result": result_repr,   # becomes Out[n] in the UI
        "error": error,
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_GET(self):
        if self.path in ("/", "/index.html", "/notebook.html"):
            with open(os.path.join(HERE, "notebook.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif self.path == "/health":
            self._send(200, json.dumps({"kernel": "alive",
                                        "engine": "build/StackBuilder",
                                        "python": sys.version.split()[0]}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/execute":
            return self._send(404, json.dumps({"error": "not found"}))
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        self._send(200, json.dumps(run_code(payload.get("code", ""))))

    def log_message(self, *a):
        pass  # quiet


if __name__ == "__main__":
    print(f"🌰 kernel alive on http://localhost:{PORT}  (engine: build/StackBuilder)")
    print("   open that URL, or open web/notebook.html directly and watch it connect.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
