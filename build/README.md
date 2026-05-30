# build/ — code the stack from scratch, the way history did

A **day in the life of the people who first built each layer**, structured as
the Gang-of-Four **Builder pattern**: one product (a notebook stack) assembled
step by step. Each maker contributes their part; a Director runs them in order.

```
Day 1 · Ken Thompson  · Unix    1971   build_repl()                         → the SHELL
Day 2 · Fernando Pérez · IPython 2001  build_history() · build_magics()      → memory + magics
                                 2011  build_transport()                     → kernel over ZeroMQ
Day 3 · Jupyter team   · Jupyter 2014  build_protocol()                      → signed messages
```

Each `build_*()` adds one capability to the same `StackBuilder` and returns
`self`, so the days chain. By the last call you've reassembled
`shell ⇄ kernel ⇄ notebook` — and it runs.

## Run it

```bash
uv run python build/director.py   # watch the makers assemble the stack, in character
uv run python build/check.py      # the green-check gate — 7 layers must pass
```

`director.py` is the Director: it knows the *sequence*, never the details.
That's the point — it doesn't change even when you rewrite the steps.

## Code it from scratch

The reference implementation in `stack_builder.py` is complete so the track
runs out of the box. To actually *build* it:

1. Pick a step — say `build_magics()` — and blank out its body.
2. Reimplement it from the maker-day's narrative (`day2_ipython.py`).
3. Run `python build/check.py` until that layer goes green.
4. Climb to the next step. The Director and the other days never change.

The `demos/` at the repo root are your reference solutions — `custom_magic.py`
for magics, `zmq_sniff.py` for the protocol, `swap_kernels.py` for why the
frozen protocol makes the kernel swappable.

## Files

```
stack_builder.py   the Builder — NotebookStack product + all build_* steps
director.py        the Director — runs the days in historical order
day1_the_shell.py  🎬 Ken Thompson, 1971 — build_repl()
day2_ipython.py    🎬 Fernando Pérez, 2001→2011 — history, magics, transport
day3_jupyter.py    🎬 Jupyter team, 2014 — protocol
check.py           green-check gate (7 assertions)
```
