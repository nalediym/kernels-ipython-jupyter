"""
🎬  DAY 2 — Fernando Pérez · grad student, Boulder · 2001 → 2011

It's 2001. You do physics in Python, but the plain `>>>` REPL is amnesiac: it
forgets every result the moment it prints it, and there's no fast way to time a
loop or list your variables. So you build a nicer shell on top of Python and
call it **IPython** — it remembers results in `_` and `Out[]`, and it adds
`%magic` commands: little functions you summon with a `%`.

Then, 2011. Your REPL and your running code live in the same process, so a UI
crash kills your whole session, and you can't attach a second window to the same
namespace. The fix: split it in two. The executor becomes a separate **kernel**
process, and the front-end talks to it over **ZeroMQ**. You borrowed Unix's word
on purpose — shell out front, kernel in back.

Your contributions:  build_history() · build_magics() · build_transport()
"""


def build(builder):
    print("━" * 64)
    print("DAY 2 · Fernando Pérez · 2001→2011 · IPython")
    print("━" * 64)
    s = builder.result()

    # --- 2001: remember results -----------------------------------------
    print("  2001 · the REPL should REMEMBER:")
    builder.build_history()
    s._run("21 * 2")                          # prints Out[n]: 42
    s._run("_ + 1")                           # `_` is the last result → 43
    print("  ✓ Out[] and `_` work now.\n")

    # --- 2001: magics are just functions --------------------------------
    print("  2001 · %magics (just registered functions):")
    builder.build_magics()
    s._run("nums = list(range(1000))")
    s._run("%time sum(nums)")                 # custom %time
    s._run("%who")                            # custom %who
    print("  ✓ % commands dispatch to functions.\n")

    # --- 2011: split the kernel out over ZeroMQ -------------------------
    print("  2011 · move the executor into its OWN process (ZeroMQ):")
    builder.build_transport()
    printed = s.client_send("print('this ran in the kernel process, not here')")
    print(f"  front-end sent code over a socket; kernel replied: {printed.strip()!r}")
    print("  ✓ the front-end no longer runs your code — a socket does.\n")
