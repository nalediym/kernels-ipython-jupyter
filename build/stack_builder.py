"""The Builder — ONE product (a notebook stack), assembled part by part.

This is the classic Gang-of-Four **Builder pattern**: a single product is
constructed through a sequence of steps, each `build_*()` bolts on one
capability and returns `self` so the maker-days can chain their contributions.
A Director (director.py) calls the steps in historical order. By the final
call you've reassembled `shell ⇄ kernel ⇄ notebook` — the way history did.

    Day 1 · Ken Thompson  · Unix    →  build_repl()
    Day 2 · Fernando Pérez · IPython →  build_history() · build_magics() · build_transport()
    Day 3 · Jupyter team   · Jupyter →  build_protocol()

Each step is fully implemented here as the *reference*. To "code it from
scratch": blank out a build_* body, reimplement it, and run check.py until the
green check returns. The Director never changes — that's the point of Builder.
"""
import ast
import io
import json
import time
import hmac
import hashlib
import threading
import contextlib


class NotebookStack:
    """The PRODUCT. Starts empty; every builder step bolts on a capability."""

    def __init__(self):
        self.ns = {}        # the kernel's ONE persistent namespace
        self.In = {}        # input history          (Day 2)
        self.Out = {}       # output cache, the Out[] dict (Day 2)
        self.count = 0      # execution counter      (Day 2)
        self.magics = {}    # % commands             (Day 2)
        self.has = set()    # which layers are installed (for narration)


class StackBuilder:
    def __init__(self):
        self.stack = NotebookStack()

    def result(self):
        """Return the product. (Builder pattern: getResult().)"""
        return self.stack

    # ════════════════════════════════════════════════════════════════════
    #  DAY 1 · Ken Thompson · Unix (~1971) · "a shell holds state and delegates"
    # ════════════════════════════════════════════════════════════════════
    def build_repl(self):
        """The core read-eval loop: exec statements + eval a trailing
        expression against ONE namespace that survives between calls."""
        s = self.stack

        def run(code):
            block = ast.parse(code, "<cell>", "exec")
            tail = None
            if block.body and isinstance(block.body[-1], ast.Expr):
                tail = ast.Expression(block.body.pop().value)   # last expression
            exec(compile(block, "<cell>", "exec"), s.ns)        # run the statements
            if tail is not None:
                return eval(compile(tail, "<cell>", "eval"), s.ns)
            return None

        s._run = run
        s.has.add("repl")
        return self

    # ════════════════════════════════════════════════════════════════════
    #  DAY 2 · Fernando Pérez · IPython (2001 → two-process split 2011)
    # ════════════════════════════════════════════════════════════════════
    def build_history(self):
        """Wrap the REPL so results land in Out[n] and `_`, and echo them —
        the thing the plain python REPL never remembered."""
        s = self.stack
        base = s._run

        def run(code):
            s.count += 1
            s.In[s.count] = code
            result = base(code)
            if result is not None:
                s.Out[s.count] = result
                s.ns["_"] = result
                print(f"Out[{s.count}]: {result!r}")
            return result

        s._run = run
        s.has.add("history")
        return self

    def build_magics(self):
        """Intercept `%`-lines before they reach Python. A magic is just a
        registered function — proof there's nothing built-in about them."""
        s = self.stack
        engine = s._run                      # the history-aware runner

        def magic_time(line):
            t0 = time.perf_counter()
            engine(line)
            print(f"  ⏱  {(time.perf_counter() - t0) * 1e3:.3f} ms")

        def magic_who(line):
            names = [k for k in s.ns if not k.startswith("_")]
            print("  vars:", " ".join(names) or "(none)")

        s.magics.update(time=magic_time, who=magic_who)

        def run(code):
            stripped = code.lstrip()
            if stripped.startswith("%"):
                name, _, rest = stripped[1:].partition(" ")
                fn = s.magics.get(name)
                if fn:
                    return fn(rest)
                print(f"  (no magic %{name})")
                return None
            return engine(code)

        s._run = run
        s.has.add("magics")
        return self

    def build_transport(self, port=8990):
        """2011: lift the executor into its OWN process, reachable over a
        ZeroMQ socket. The front-end stops running code — it sends a message."""
        import zmq

        s = self.stack
        ctx = zmq.Context.instance()

        def kernel_loop():
            sock = ctx.socket(zmq.REP)
            sock.bind(f"tcp://127.0.0.1:{port}")
            while True:
                code = sock.recv_string()
                if code == "__STOP__":
                    sock.send_string("bye")
                    break
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    s._run(code)               # the SAME engine, now over a wire
                sock.send_string(buf.getvalue())
            sock.close()

        threading.Thread(target=kernel_loop, daemon=True).start()
        time.sleep(0.2)
        client = ctx.socket(zmq.REQ)
        client.connect(f"tcp://127.0.0.1:{port}")

        def send(code):
            client.send_string(code)
            return client.recv_string()

        s.client_send = send
        s._stop_transport = lambda: (client.send_string("__STOP__"),
                                     client.recv_string(), client.close())
        s.has.add("transport")
        return self

    # ════════════════════════════════════════════════════════════════════
    #  DAY 3 · Jupyter team · Project Jupyter (2014) · "freeze the protocol"
    # ════════════════════════════════════════════════════════════════════
    def build_protocol(self, port=8991, key=b"sekret-kernel-key"):
        """2014: stop shipping bare strings. Speak signed JSON *messages* —
        the real Jupyter wire idea: <IDS|MSG> delimiter, HMAC, header, content.
        Now ANY front-end (a browser!) can drive ANY kernel that speaks it."""
        import zmq

        s = self.stack
        ctx = zmq.Context.instance()

        def sign(*parts):
            h = hmac.new(key, digestmod=hashlib.sha256)
            for p in parts:
                h.update(p)
            return h.hexdigest().encode()

        def kernel_loop():
            sock = ctx.socket(zmq.REP)
            sock.bind(f"tcp://127.0.0.1:{port}")
            while True:
                # frames: [b"<IDS|MSG>", signature, header, content]
                _, sig, header, content = sock.recv_multipart()
                if sign(header, content) != sig:
                    sock.send_multipart([b"<IDS|MSG>", b"", b"{}",
                                         b'{"status":"BAD_SIGNATURE"}'])
                    continue
                hdr, ct = json.loads(header), json.loads(content)
                if hdr["msg_type"] == "shutdown_request":
                    sock.send_multipart([b"<IDS|MSG>", b"", b"{}", b"{}"])
                    break
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    s._run(ct["code"])
                rh = json.dumps({"msg_type": "execute_reply"}).encode()
                rc = json.dumps({"status": "ok", "stdout": buf.getvalue(),
                                 "execution_count": s.count}).encode()
                sock.send_multipart([b"<IDS|MSG>", sign(rh, rc), rh, rc])
            sock.close()

        threading.Thread(target=kernel_loop, daemon=True).start()
        time.sleep(0.2)
        client = ctx.socket(zmq.REQ)
        client.connect(f"tcp://127.0.0.1:{port}")

        def execute(code):
            hdr = json.dumps({"msg_type": "execute_request", "msg_id": "1"}).encode()
            ct = json.dumps({"code": code}).encode()
            client.send_multipart([b"<IDS|MSG>", sign(hdr, ct), hdr, ct])
            _, _sig, _hdr, reply = client.recv_multipart()
            return json.loads(reply)

        def stop():
            hdr = json.dumps({"msg_type": "shutdown_request"}).encode()
            client.send_multipart([b"<IDS|MSG>", sign(hdr, b"{}"), hdr, b"{}"])
            client.recv_multipart()
            client.close()

        s.protocol_execute = execute
        s._stop_protocol = stop
        s.has.add("protocol")
        return self
