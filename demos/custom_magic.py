"""A tiny IPython extension that adds two custom magics.

Load it inside ipython or a Jupyter cell with:

    %load_ext custom_magic        # if this file is on sys.path / cwd
    %clap kernels are just processes
    %%shout
    state lives in the kernel

A "magic" is just a Python function the IPython kernel routes to when a
line starts with % (line magic) or a cell starts with %% (cell magic).
Nothing about this is built into Python — it's pure IPython sugar, which
is exactly why bare `python3` can't do it.
"""
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic


@magics_class
class PlaygroundMagics(Magics):
    @line_magic
    def clap(self, line):
        "Line magic: echo the line with 👏 between 👏 every 👏 word."
        return " 👏 ".join(line.split()) if line.strip() else "(give me words)"

    @cell_magic
    def shout(self, line, cell):
        "Cell magic: UPPERCASE the whole cell and print it."
        print(cell.upper().rstrip())


def load_ipython_extension(ipython):
    """Called by IPython when you run `%load_ext custom_magic`."""
    ipython.register_magics(PlaygroundMagics)
