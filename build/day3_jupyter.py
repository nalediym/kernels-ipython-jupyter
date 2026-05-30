"""
🎬  DAY 3 — the Jupyter team (Pérez, Granger, Ragan-Kelley, …) · 2014

IPython's kernel already runs in its own process. But two things still itch:
the front-end is a terminal, and the kernel only speaks Python. You want a
**browser** notebook, and you want the *same* notebook to drive R and Julia too
(Ju-Pyt-R). The unlock isn't more code in the kernel — it's freezing the
**protocol** between them.

So you spin IPython's language-agnostic parts out into **Project Jupyter** and
nail down a messaging spec: every exchange is a signed JSON *message* —
a `<IDS|MSG>` delimiter, an HMAC signature, a header (with `msg_type`), and
content. Any front-end that speaks it can drive any kernel that speaks it.
The kernel becomes a swappable back-end. Same UI, any language.

Your contribution:  build_protocol()
"""


def build(builder):
    print("━" * 64)
    print("DAY 3 · Project Jupyter · 2014 · the PROTOCOL")
    print("━" * 64)
    print("  problem: a browser should drive Python OR R OR Bash — one UI.")
    print("  insight: don't ship strings. Ship signed JSON *messages*.")
    print()
    s = builder.result()

    builder.build_protocol()
    reply = s.protocol_execute("answer = 6 * 7\nprint('kernel computed', answer)")
    print("  front-end sent a signed execute_request:")
    print("     [ <IDS|MSG> | HMAC | header{msg_type:'execute_request'} | content{code} ]")
    print(f"  kernel replied (decoded): {reply}")
    print("  ✓ a real message protocol — the exact shape zmq_sniff.py prints")
    print("    against the production kernel. You just built Jupyter's spine.\n")
