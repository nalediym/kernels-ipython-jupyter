"""The Director — assembles the stack by running the makers in order.

In the Builder pattern the Director knows the *sequence*, not the details. It
never changes, even as you reimplement the build_* steps from scratch. That
separation is the whole lesson: history is the Director; each person is a step.

    python build/director.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stack_builder import StackBuilder
import day1_the_shell
import day2_ipython
import day3_jupyter


def main():
    builder = StackBuilder()

    # The Director's only job: call the steps in the order history did.
    for maker in (day1_the_shell, day2_ipython, day3_jupyter):
        maker.build(builder)

    stack = builder.result()
    print("═" * 64)
    print("ASSEMBLED PRODUCT:  " + "  +  ".join([
        "repl", "history", "magics", "transport", "protocol",
    ]))
    layers = ", ".join(sorted(stack.has))
    print(f"installed layers : {layers}")
    print("you rebuilt  shell ⇄ kernel ⇄ notebook  the way history did. 🌰")
    print("═" * 64)

    # tidy up the background kernel sockets the days stood up
    for stop in ("_stop_transport", "_stop_protocol"):
        getattr(stack, stop, lambda: None)()


if __name__ == "__main__":
    main()
