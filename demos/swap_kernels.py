"""Same front-end code, two languages — proof the kernel is swappable.

The notebook UI / jupyter_client doesn't know or care what language runs your
cell. It speaks the messaging protocol; the kernel on the other end decides
what "run this code" means. Here we drive a Python kernel and a Bash kernel
through the *identical* client function — only the kernel_name changes.

Run:  python demos/swap_kernels.py
"""
from jupyter_client.manager import start_new_kernel


def run(kernel_name, code):
    """Boot `kernel_name`, run `code`, return whatever it printed/returned.

    This function has ZERO language-specific logic. That's the whole point.
    """
    km, kc = start_new_kernel(kernel_name=kernel_name)
    out = []

    def on_output(msg):
        t = msg["header"]["msg_type"]
        if t == "stream":
            out.append(msg["content"]["text"])
        elif t in ("execute_result", "display_data"):
            out.append(msg["content"]["data"].get("text/plain", ""))
        elif t == "error":
            out.append("\n".join(msg["content"]["traceback"]))

    kc.execute_interactive(code, output_hook=on_output, timeout=30)
    kc.stop_channels()
    km.shutdown_kernel(now=True)
    return "".join(out).strip()


CASES = [
    ("python3", "import platform\nprint('python kernel:', platform.python_version())\n2 ** 10"),
    ("bash",    "echo \"bash kernel: $(bash --version | head -1)\"; echo \"2^10 = $((2 ** 10))\""),
]

for name, code in CASES:
    print(f"\n===== kernel = {name!r} =====")
    print(f"  sent : {code!r}")
    print(f"  got  : {run(name, code)!r}")

print("\nTAKEAWAY: one client, one protocol, two languages. The 'kernel' is a")
print("pluggable back-end — Python today, Bash here, R/Julia/Deno elsewhere.")
print("Swap the kernel, keep the notebook. That's the whole architecture.")
