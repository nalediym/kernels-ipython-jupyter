"""Green-check gate for the build/ track.

If you've blanked out a build_* step and reimplemented it from scratch, run
this until every layer passes. It drives the StackBuilder directly — no
narration — and asserts each capability actually works.

    python build/check.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stack_builder import StackBuilder

PASS, FAIL = "✓", "✗"
results = []


def check(name, ok):
    results.append((name, ok))
    print(f"  {PASS if ok else FAIL}  {name}")


b = StackBuilder()
s = b.result()

# Day 1 — REPL holds state
b.build_repl()
s._run("a = 10")
check("Day 1 · REPL persists state across calls", s._run("a * 4") == 40)

# Day 2 — history (_, Out[])
b.build_history()
s._run("2 + 5")
check("Day 2 · `_` holds the last result", s._run("_") == 7)
check("Day 2 · Out[] caches results", s.Out and list(s.Out.values())[-1] == 7)

# Day 2 — magics
b.build_magics()
s._run("zz = 99")
captured = []
import io
import contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    s._run("%who")
check("Day 2 · %who is a dispatched magic", "zz" in buf.getvalue())

# Day 2 — transport (code runs over a socket, in another thread)
b.build_transport()
out = s.client_send("print('over the wire')")
check("Day 2 · code executes over a ZeroMQ socket", "over the wire" in out)
s._stop_transport()

# Day 3 — protocol (signed JSON messages)
b.build_protocol()
reply = s.protocol_execute("print('hi'); 1 + 1")
check("Day 3 · signed execute_request → ok reply", reply.get("status") == "ok")
check("Day 3 · kernel streams stdout back", "hi" in reply.get("stdout", ""))
s._stop_protocol()

print()
ok = sum(1 for _, v in results if v)
total = len(results)
print(f"{ok}/{total} layers green" + ("  🌰 you built the stack." if ok == total else ""))
sys.exit(0 if ok == total else 1)
