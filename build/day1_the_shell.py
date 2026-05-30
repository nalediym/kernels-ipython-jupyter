"""
🎬  DAY 1 — Ken Thompson · Bell Labs · ~1971

You're building Unix on a PDP-11. A user's program cannot be trusted to poke
the disk, the terminal, the memory of other programs. But people still need to
*drive* the machine interactively. Your move: write a small program whose only
job is to read what the human types and hand it off to be executed — a program
that holds a little state and DELEGATES the real work.

You call it a **shell**. The thing it delegates to — the protected core that
actually does the work — is the **kernel**. That word, that split, outlives you
by half a century.

Your contribution to the stack:  builder.build_repl()
"""


def build(builder):
    print("━" * 64)
    print("DAY 1 · Ken Thompson · 1971 · the SHELL")
    print("━" * 64)
    print("  problem: humans need to drive the machine, but code can't be")
    print("           trusted with the hardware.")
    print("  insight: a small program that holds state and DELEGATES execution.")
    print()

    builder.build_repl()
    s = builder.result()

    # Prove the one thing that matters: state lives in the process.
    s._run("x = 6 * 7")                       # a statement — no value
    answer = s._run("x * 2")                  # an expression — uses earlier state
    print("  you typed:  x = 6 * 7   then   x * 2")
    print(f"  the shell remembered x  →  {answer}")
    print("  ✓ state persists between lines. THAT is a kernel.\n")
