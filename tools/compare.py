"""Golden test: the C++ core must match the Python reference sample for sample.

  cmake -S cpp -B cpp/build && cmake --build cpp/build
  python -m tools.compare
"""
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

from render import FS, load_input, parse_schedule, render

BINARY = os.path.join("cpp", "build", "render")
SCHEDULE = "0:slow,1.5:fast,4:stop,5:slow"
TOLERANCE = 1e-4

CASES = (
    ("stereo", []),
    ("mono", ["--mono"]),
    ("stereo, balance 0.8, mix 0.6", ["--balance", "0.8", "--mix", "0.6"]),
)


def flag(args, name, default):
    return float(args[args.index(name) + 1]) if name in args else default


def main():
    if not os.path.exists(BINARY):
        sys.exit(f"{BINARY} not found; build it with cmake first")
    os.makedirs("out", exist_ok=True)

    x = load_input("organ:220", 6.0).astype(np.float32)
    in_path = "out/compare_in.wav"
    sf.write(in_path, x, FS, subtype="FLOAT")
    x = x.astype(np.float64)  # the exact float32 values the C++ side reads

    failed = False
    for name, args in CASES:
        out_path = "out/compare_cpp.wav"
        subprocess.run([BINARY, in_path, out_path, "--schedule", SCHEDULE, *args],
                       check=True, capture_output=True)
        cpp, _ = sf.read(out_path, always_2d=True)
        py = render(x, parse_schedule(SCHEDULE), stereo="--mono" not in args,
                    balance=flag(args, "--balance", 0.5), mix=flag(args, "--mix", 1.0))

        err = np.max(np.abs(cpp - py))
        ok = cpp.shape == py.shape and err < TOLERANCE
        failed |= not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:30s} max diff {err:.2e}  (peak {np.max(np.abs(py)):.2f})")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
