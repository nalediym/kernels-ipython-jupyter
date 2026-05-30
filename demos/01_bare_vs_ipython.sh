#!/usr/bin/env bash
# Side-by-side: the SAME snippet fed to bare python3 vs ipython.
# Run from the repo root:  bash demos/01_bare_vs_ipython.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python3
IP=.venv/bin/ipython

# One snippet. Three lessons hide in it:
#   line 1: does the REPL echo the value of a bare expression?
#   line 2: does `_` remember the last result?
#   line 4: what does a traceback look like?
SNIP='2 + 2
_ * 10
import math
math.sqrt(-1)'

echo "############ BARE python3 (the plain interpreter) ############"
# Piped stdin runs as a *script*: expression values are NOT echoed,
# and there is no `_`, so line 2 raises NameError and the program dies.
printf '%s\n' "$SNIP" | "$PY" 2>&1 || true

echo
echo "############ ipython (the enhanced REPL / default kernel) ############"
# Same bytes. IPython echoes Out[n], keeps `_`, numbers In/Out, and
# renders a colored traceback with a caret under the failing call.
printf '%s\n' "$SNIP" | "$IP" --no-banner --no-confirm-exit 2>&1 || true

echo
echo "TAKEAWAY: bare python3 is a language runtime; ipython is a *human* layer"
echo "on top of it — echo, _, In/Out history, rich tracebacks. Jupyter's"
echo "default kernel IS ipython, which is why notebooks feel like this."
