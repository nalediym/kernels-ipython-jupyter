# kernels-ipython-jupyter

A hands-on playground for *feeling* the difference between three things that
get conflated constantly:

| Term | One sentence | The thing in this repo |
|---|---|---|
| **Kernel** | the **process** that runs your code and holds its state | the `ipykernel` PID you'll print |
| **IPython** | the **enhanced REPL** that the default kernel wraps | `_`, `Out[]`, `%magics`, `!shell` |
| **Jupyter** | the **front-end** that talks to a kernel over **ZeroMQ** | JupyterLab / the notebook UI |

The mental model the whole repo is built to make concrete:

```
┌─────────────┐   signed JSON over    ┌──────────────────────────┐
│   JUPYTER    │  5 ZeroMQ sockets     │         KERNEL            │
│  (the UI)    │ ───────────────────►  │   a separate process     │
│              │   execute_request     │   running IPython        │
│  notebook /  │ ◄───────────────────  │   ── holds your state ── │
│  JupyterLab  │  stream / result /    │   x = 42 lives HERE       │
│              │  status (idle/busy)   │                          │
└─────────────┘                        └──────────────────────────┘
       ▲                                          ▲
   renders cells                          runs code, never sees the UI
```

**The UI never runs your code.** It serializes "please run this" into a signed
JSON message, pushes it over a socket, and renders whatever streams back. Swap
the process on the right and the same UI now drives a different language.

---

## Or build the whole thing from scratch → [`build/`](build/)

Don't just watch it — **rebuild it the way history did.** The [`build/`](build/)
track is a day in the life of the people who first made each layer, structured
as the **Builder pattern**: one product assembled step by step.

```
Day 1 · Ken Thompson  · Unix    1971   build_repl()        → the SHELL holds state
Day 2 · Fernando Pérez · IPython 2001  build_history/magics → memory + % commands
                                 2011  build_transport()   → kernel over ZeroMQ
Day 3 · Jupyter team   · Jupyter 2014  build_protocol()    → signed JSON messages
```

```bash
uv run python build/director.py   # the makers assemble the stack, in character
uv run python build/check.py      # green-check gate — 7 layers must pass
```

It runs out of the box; blank out any `build_*` step and reimplement it until
`check.py` goes green. See [`build/README.md`](build/README.md).

---

## Setup

Managed with [**uv**](https://docs.astral.sh/uv/). No IPython/Jupyter system-wide —
`pyproject.toml` + `uv.lock` pin everything (ipython, jupyterlab, bash_kernel).

```bash
uv sync                                   # build the env from the lockfile
uv run python -m bash_kernel.install --sys-prefix   # register the Bash kernel (once)
```

`uv run <cmd>` runs anything inside the project env — no activating, no `uv run …`.
Launch the real thing whenever you want to click around:

```bash
uv run jupyter lab          # opens JupyterLab in your browser
```

---

## 1. Bare `python3` vs IPython — same bytes, different world

`demos/01_bare_vs_ipython.sh` feeds the **identical snippet** to both:

```python
2 + 2
_ * 10
import math
math.sqrt(-1)
```

**Bare `python3`** (a language runtime — runs the script, echoes nothing, dies on `_`):

```
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
NameError: name '_' is not defined
```

**IPython** (a human layer on top — echoes `Out`, remembers `_`, numbers history, colors the traceback):

```
In [1]: Out[1]: 4
In [2]: Out[2]: 40
In [4]: ValueError: expected a nonnegative input, got -1.0
        ----> 1 math.sqrt(-1)
```

> **Takeaway:** Jupyter's default kernel *is* IPython. Everything that makes a
> notebook feel alive — echo, `_`, `In`/`Out`, rich tracebacks — comes from here,
> not from Python and not from the browser.

---

## 2. The notebook — state lives in the kernel

`notebooks/playground.ipynb` is pre-executed — open it in JupyterLab
(`uv run jupyter lab`) and run it yourself. It walks through, with real outputs:

- **Which Python is my kernel?** `sys.executable` vs `!which python3` — the venv/`source` confusion.
- **State persists across cells:** `secret = 6 * 7` in one cell, `secret * 2 → 84` in the next. Same process.
- **`_`, `Out[]`:** IPython's result cache.
- **Magics:** `%timeit sum(range(10_000))` → `89.4 µs ± …`, `%who`, `%%writefile` + `%run`.
- **`!shell`:** `!ls`, and capturing shell output into a Python variable.
- **A custom magic** (see §4).

Rebuild + re-execute it any time:

```bash
uv run python notebooks/build_notebook.py
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/playground.ipynb
```

---

## 3. DEEP — watch the raw ZeroMQ frames on the wire

This is the one most tutorials hand-wave. `demos/zmq_sniff.py` boots a real
kernel, attaches its **own** zmq sockets to the kernel's Shell + IOPub ports, and
prints the multipart frames byte-for-byte as you run `x = 6 * 7; print(...); x`.

```bash
uv run python demos/zmq_sniff.py
```

You watch one `execute_request` turn into the full reply lifecycle:

```
>>> SENDING execute_request  (code: "x = 6 * 7\nprint('the answer is', x)\nx")

┌─ IOPUB ── 7 frames (delimiter <IDS|MSG> at position 1) ────────
  [0]   50B  kernel.<id>.status
  [1]    9B  <IDS|MSG>                ← delimiter (routing ends here)
  [2]   64B  69d721…0acb0a3d          ← HMAC signature (64 hex chars)
  [3]  203B  {"msg_type": "status"…}  ← header
  [4]    2B  {}                       ← parent_header
  [5]    2B  {}                       ← metadata
  [6]   27B  {"execution_state": "busy"}   ← content

…  execute_input  →  stream/stdout "the answer is 42"  →  execute_result {"text/plain": "42"}
┌─ SHELL  execute_reply: {"status": "ok"} …
┌─ IOPUB  status: {"execution_state": "idle"}
```

Every frame carries the `<IDS|MSG>` delimiter, an **HMAC signature** (the kernel
won't run an unsigned message), a **header**, a **parent_header** linking each
reply back to your request, and **content**. That sequence —
`status:busy → execute_input → stream → execute_result → execute_reply → status:idle` —
is *exactly* what JupyterLab exchanges with the kernel on every Shift+Enter.

---

## 4. DEEP — write your own `%magic`

`demos/custom_magic.py` is a loadable IPython extension defining a line magic and
a cell magic. Magics aren't built into Python — they're just registered functions:

```bash
uv run python demos/run_magic_demo.py
```
```
>>> %clap kernels hold state
Out[0]: 'kernels 👏 hold 👏 state'

>>> %%shout / state persists across cells
STATE PERSISTS ACROSS CELLS
```

(`run_magic_demo.py` drives an `InteractiveShell.run_cell` — which is precisely
what a kernel does with each cell. No notebook required to prove the magic is real.)

---

## 5. DEEP — the kernel is swappable (Python ↔ Bash, same UI)

`demos/swap_kernels.py` runs **one** client function against two kernels, changing
only the `kernel_name`. Install the bash kernel once:

```bash
uv run python -m bash_kernel.install --sys-prefix
```
```bash
uv run python demos/swap_kernels.py
```
```
===== kernel = 'python3' =====
  got  : 'python kernel: 3.14.4\n1024'

===== kernel = 'bash' =====
  got  : 'bash kernel: GNU bash, version 5.2.37(1)-release …\n2^10 = 1024'
```

Same protocol, same client code, two languages. The "kernel" is a pluggable
back-end — Python, Bash, R, Julia, Deno. Swap the kernel, keep the notebook.
List what's installed:

```bash
uv run jupyter kernelspec list
```

---

## Which Python is my kernel pointing at?

The single most common Jupyter confusion. A kernel is a **process**, launched with
**one specific interpreter**, and it keeps that interpreter for its whole life:

- `sys.executable` (inside a cell) = the truth: the interpreter the kernel runs.
- `!which python3` (inside a cell) = the *shell's* `PATH`, which can be a totally different Python.
- Activating a venv in your terminal does **not** move an already-running kernel.

If imports work in your terminal but fail in the notebook, you're almost always
pointed at a different interpreter. Check `sys.executable` first, every time.

---

## Layout

```
demos/
  01_bare_vs_ipython.sh   # §1  python3 vs ipython, same snippet
  custom_magic.py         # §4  loadable extension: %clap, %%shout
  run_magic_demo.py       # §4  drive the magic via InteractiveShell.run_cell
  zmq_sniff.py            # §3  raw ZeroMQ frames between client and kernel
  swap_kernels.py         # §5  one client, python3 + bash kernels
notebooks/
  build_notebook.py       # constructs playground.ipynb with nbformat
  playground.ipynb        # the annotated, pre-executed teaching notebook
pyproject.toml            # deps: ipython, jupyterlab, bash_kernel  (managed by uv)
uv.lock                   # the full pinned, hashed lockfile (97 packages)
requirements.txt          # pip-compatible export of the lock, for non-uv users
```

Related learning repos: [`learn-virtual-envs`](../learn-virtual-envs) (the `source`/which-python
story) and [`learn-zmq-amps`](../learn-zmq-amps) (ZeroMQ messaging patterns).
