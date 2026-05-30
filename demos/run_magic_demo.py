"""Drive the custom magics the way a kernel does: InteractiveShell.run_cell.

A Jupyter kernel doesn't do anything mystical with a cell — it hands the
source to an IPython InteractiveShell and calls run_cell(). We do the exact
same thing here, no notebook required, so the custom magic is provably real.

    python demos/run_magic_demo.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))  # find custom_magic

from IPython.core.interactiveshell import InteractiveShell

sh = InteractiveShell.instance()          # this is what a kernel wraps
sh.run_line_magic("load_ext", "custom_magic")

print(">>> %clap kernels hold state")
res = sh.run_cell("%clap kernels hold state")
print("returned:", repr(res.result))

print("\n>>> %%shout / state persists across cells")
sh.run_cell("%%shout\nstate persists across cells")
