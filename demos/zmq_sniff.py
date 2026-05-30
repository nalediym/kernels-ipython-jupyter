"""Surface the RAW ZeroMQ frames flowing between a client and a live kernel.

Normally jupyter_client hides the wire. Here we go one layer lower: we boot a
real IPython kernel, then attach our OWN zmq sockets to its Shell and IOPub
ports and print the multipart frames byte-for-byte. That's the actual Jupyter
wire protocol — the thing the notebook UI speaks every time you hit Shift+Enter.

Run:  python demos/zmq_sniff.py

Wire-protocol cheat sheet (Jupyter messaging spec v5):
  Every message is a multipart zmq frame list:
    [ident0, ident1, ..., b"<IDS|MSG>", HMAC, header, parent_header, metadata, content, ...buffers]
  - idents     : zmq routing prefix (who this is for)
  - <IDS|MSG>  : the literal delimiter separating routing from payload
  - HMAC       : signature of the 4 payload frames, keyed by the kernel's secret
  - header     : JSON {msg_id, msg_type, session, date, version, username}
  - content    : JSON payload (the code you ran, the result, the status, ...)
"""
import json
import zmq
from jupyter_client.manager import KernelManager
from jupyter_client.session import Session


def short(b, n=72):
    """Render a frame for humans: decode JSON-ish, truncate the rest."""
    try:
        return json.dumps(json.loads(b))[:n]
    except Exception:
        s = b.decode("utf8", "replace") if isinstance(b, bytes) else str(b)
        return (s[:n] + "…") if len(s) > n else s


def dump(channel, frames, session):
    """Print one multipart message: raw frame layout, then decoded meaning."""
    try:
        idx = frames.index(b"<IDS|MSG>")
    except ValueError:
        idx = -1
    print(f"\n┌─ {channel} ── {len(frames)} frames "
          f"(delimiter <IDS|MSG> at position {idx}) " + "─" * 8)
    for i, f in enumerate(frames):
        tag = ""
        if f == b"<IDS|MSG>":
            tag = "  ← delimiter (routing ends here)"
        elif idx >= 0 and i == idx + 1:
            tag = f"  ← HMAC signature ({len(f)} hex chars)"
        elif idx >= 0 and i == idx + 2:
            tag = "  ← header"
        elif idx >= 0 and i == idx + 5:
            tag = "  ← content"
        print(f"  [{i}] {len(f):>4}B  {short(f)}{tag}")
    # And the same message, decoded the way jupyter_client sees it.
    # Return the decoded dict so callers don't re-deserialize (the Session
    # treats a repeated HMAC as a replay attack and refuses it).
    if idx >= 0:
        idents, msg = session.feed_identities(frames)
        d = session.deserialize(msg)
        print(f"  └─ decoded: msg_type={d['header']['msg_type']!r}")
        return d
    return None


def main():
    km = KernelManager(kernel_name="python3")
    km.start_kernel()
    pid = getattr(getattr(km, "provisioner", None), "pid", "?")
    ports = {k: v for k, v in km.get_connection_info().items() if k.endswith("_port")}
    print(f"kernel pid={pid}  connection ports={ports}")

    info = km.get_connection_info()
    session = Session(key=info["key"], signature_scheme=info["signature_scheme"])
    ctx = zmq.Context.instance()

    # Our own raw sockets onto the kernel's ports — no high-level client.
    shell = ctx.socket(zmq.DEALER)
    shell.connect(f"{info['transport']}://{info['ip']}:{info['shell_port']}")
    iopub = ctx.socket(zmq.SUB)
    iopub.setsockopt(zmq.SUBSCRIBE, b"")
    iopub.connect(f"{info['transport']}://{info['ip']}:{info['iopub_port']}")

    # Send ONE execute_request over Shell, signed with the kernel's HMAC key.
    msg = session.msg("execute_request",
                      {"code": "x = 6 * 7\nprint('the answer is', x)\nx",
                       "silent": False, "store_history": True})
    print(f"\n>>> SENDING execute_request  (code: {msg['content']['code']!r})")
    session.send(shell, msg)

    # Read frames off both channels until the kernel goes idle again.
    poller = zmq.Poller()
    poller.register(shell, zmq.POLLIN)
    poller.register(iopub, zmq.POLLIN)
    seen_reply = seen_idle = False
    for _ in range(40):
        socks = dict(poller.poll(timeout=4000))
        if not socks:
            break
        if shell in socks:
            frames = shell.recv_multipart()
            dump("SHELL", frames, session)
            seen_reply = True
        if iopub in socks:
            frames = iopub.recv_multipart()
            dm = dump("IOPUB", frames, session)
            if (dm and dm["header"]["msg_type"] == "status"
                    and dm["content"].get("execution_state") == "idle"):
                seen_idle = True
        if seen_reply and seen_idle:
            break

    print("\nTAKEAWAY: Shift+Enter in a notebook is exactly this — a signed JSON")
    print("message pushed over a ZeroMQ socket to a separate process, whose")
    print("replies stream back on another socket. The UI never runs your code.")
    km.shutdown_kernel(now=True)


if __name__ == "__main__":
    main()
