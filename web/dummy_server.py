"""The DUMB half, on its own — serve the notebook front-end with NO kernel.

This hosts web/notebook.html and literally nothing else: there's no /execute,
no namespace, no Python evaluator. It exists to show the "just the front-end"
state — open it and every Run says "I'm just HTML, I can't run anything,"
because the page polls the kernel port (8799) and finds nobody home.

    uv run python web/dummy_server.py     →  open http://localhost:8798

To bring it to life, start the real kernel in another terminal:
    uv run python web/server.py           →  the badge flips 🔴 → 🟢
"""
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8798"))
HERE = os.path.dirname(os.path.abspath(__file__))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve the page itself for any "document" request; 404 everything else.
        # (The page looks for a kernel on :8799, not here — so it stays dead.)
        if self.path in ("/", "/index.html", "/notebook.html"):
            with open(os.path.join(HERE, "notebook.html"), "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"🔴 dummy front-end (NO kernel) on http://localhost:{PORT}")
    print("   it's just HTML. start web/server.py to give it a brain.")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
