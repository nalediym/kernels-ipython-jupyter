"""Construct the annotated teaching notebook programmatically.

We build it with nbformat (no hand-edited JSON), then it gets executed by
nbconvert so the committed .ipynb carries REAL outputs. Re-run any time:

    uv run python notebooks/build_notebook.py
    uv run jupyter nbconvert --to notebook --execute --inplace notebooks/playground.ipynb
"""
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
cells = []
md = lambda s: cells.append(new_markdown_cell(s.strip()))
code = lambda s: cells.append(new_code_cell(s.strip()))

md(r"""
# The kernel playground — feel the three layers

This notebook is **running inside a kernel**: a separate Python process (an
IPython kernel, `ipykernel`) that this UI talks to over ZeroMQ. Nothing in
here is special notebook magic baked into the file — every output below was
produced by that live process. Let's prove it and poke at it.

> **Layered model:** `Jupyter (this UI)` ⇄ `ZeroMQ (signed JSON messages)` ⇄ `Kernel (IPython, holds your state)`
""")

md("## 1. Which Python is my kernel? (the venv/`source` confusion)\nThe kernel is a *process*. The first thing worth knowing is which interpreter it is.")
code("""
import sys, os
print("kernel interpreter :", sys.executable)
print("python version     :", sys.version.split()[0])
print("kernel process PID  :", os.getpid())
""")

md("""That `sys.executable` is the source of endless confusion: the kernel points at
**one specific Python** (here, our `.venv`). Activating a different venv in your
terminal does **not** move a *running* kernel — the kernel keeps the interpreter
it was launched with. `!which python3` (the shell's idea) and `sys.executable`
(the kernel's reality) can disagree:""")
code('print("shell sees :", end=" "); ' + "\n" + "!which python3")
code('print("kernel is  :", sys.executable)')

md("""## 2. State lives in the kernel, not the cells
Cells aren't isolated scripts. They all run in the **same process**, so a name
defined in one cell is alive in the next. That persistence *is* the kernel.""")
code("secret = 6 * 7        # define it here, produce no output")
code("secret * 2            # ...and it's still alive one cell later")

md("""## 3. `_`, `In`, `Out` — IPython's history (bare `python3` has none of this)
IPython caches every result. `_` is the last value; `Out[n]` is the value of cell *n*.""")
code('print("last result (_):", _)\nprint("Out cache keys     :", list(Out.keys()))')

md("""## 4. Magics — the `%`/`%%` commands that aren't Python
A *magic* is a command IPython intercepts before the line reaches Python.
`%timeit` measures, `%who` lists your variables, `%%writefile` saves a cell.""")
code("%timeit sum(range(10_000))")
code("name = 'naledi'\npi = 3.14159\n%who          # every name currently alive in the kernel")

md("### `%run` — execute a whole script *inside this kernel's namespace*")
code("""%%writefile hello_run.py
# This file is written by the cell above, then run by the cell below.
greeting = "hello from %run — I ran inside the kernel"
print(greeting)
""")
code('%run hello_run.py\nprint("and `greeting` now lives in the notebook:", greeting)')

md("""## 5. `!` — shell access straight from a cell
A leading `!` ships the line to the OS shell and pipes the output back. You can
even capture it into a Python variable.""")
code('!echo "shell says: I am $(uname -s) and the time is $(date +%H:%M:%S)"')
code('files = !ls -1\nprint("this cell captured a shell listing into Python:", files)')

md("""## 6. A custom magic — magics are just registered functions
`demos/custom_magic.py` defines `%clap` and `%%shout`. We load it and use it,
proving magics are extensible, not hard-coded.""")
code("""
import sys
sys.path.insert(0, "../demos")   # so the kernel can import custom_magic
%load_ext custom_magic
%clap kernels are just processes that hold state
""")
code("""%%shout
state persists across cells, and magics are yours to write
""")

md("""## 7. So what *is* each layer?

| Layer | What it is | In this notebook |
|---|---|---|
| **Kernel** | the process that runs code and holds state | the `ipykernel` PID printed in §1 |
| **IPython** | the enhanced REPL that the default kernel wraps | `_`, `Out[]`, magics, `!shell` above |
| **Jupyter** | the UI/front-end that talks to a kernel over ZeroMQ | the thing rendering this page |

Want to *see* the ZeroMQ messages this UI exchanges with the kernel?
Run `python demos/zmq_sniff.py` at the repo root — it prints the raw frames.
""")

nb["cells"] = cells
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
with open("notebooks/playground.ipynb", "w") as f:
    nbf.write(nb, f)
print(f"wrote notebooks/playground.ipynb with {len(cells)} cells")
