"""Render a WAV file (or a test tone) through the Leslie model, offline.

  python render.py in.wav out.wav --schedule "0:slow,2:fast,7:slow"
  python render.py sine:440 out.wav --duration 10 --mono
  python render.py organ:220 out.wav --dry out_dry.wav
"""
import argparse
import math
import time

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from leslie import rotor
from leslie.leslie import Leslie

FS = 48000

# Hammond drawbars as (multiple of the note, level): 16' 5 1/3' 8' 4' 2 2/3' 2' 1 3/5' 1 1/3' 1'.
# The upper four sit above the 800 Hz crossover for a 220 Hz note, so the horn has something to spin.
ORGAN_PARTIALS = (
    (0.5, 0.8), (1.5, 0.5), (1.0, 1.0), (2.0, 0.7), (3.0, 0.5),
    (4.0, 0.5), (5.0, 0.3), (6.0, 0.3), (8.0, 0.4),
)


def parse_schedule(text):
    """'0:slow,2:fast' -> [(0.0, SLOW), (2.0, FAST)], sorted by time."""
    events = []
    for item in text.split(","):
        t, name = item.split(":")
        events.append((float(t), rotor.MODE_NAMES[name.strip().lower()]))
    return sorted(events)


def load_input(source, duration):
    kind, _, arg = source.partition(":")
    if kind in ("sine", "organ") and arg:
        f = float(arg)
        t = np.arange(int(duration * FS)) / FS
        if kind == "sine":
            x = np.sin(2 * np.pi * f * t)
        else:
            x = sum(level * np.sin(2 * np.pi * f * mult * t) for mult, level in ORGAN_PARTIALS)
        return 0.5 * x / np.max(np.abs(x))

    x, fs = sf.read(source, dtype="float64", always_2d=True)
    x = x.mean(axis=1)  # the pedal input is mono
    if fs != FS:
        g = math.gcd(FS, fs)
        x = resample_poly(x, FS // g, fs // g)
    if duration:
        x = x[: int(duration * FS)]
    return x


def render(x, schedule, stereo=True, balance=0.5, mix=1.0):
    leslie = Leslie(FS, stereo=stereo)
    leslie.set_balance(balance)
    leslie.set_mix(mix)

    # Sample index at which each mode change happens
    events = [(int(t * FS), mode) for t, mode in schedule]
    next_event = 0

    out = np.zeros((len(x), 2))
    for n, sample in enumerate(x.tolist()):
        while next_event < len(events) and events[next_event][0] <= n:
            leslie.set_mode(events[next_event][1])
            next_event += 1
        out[n] = leslie.process(sample)
    return out if stereo else out[:, :1]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input", help="WAV path, or sine:<hz> / organ:<hz> for a test tone")
    p.add_argument("output")
    p.add_argument("--schedule", default="0:slow,5:fast,18:slow", help="time:mode pairs (stop/slow/fast)")
    p.add_argument("--duration", type=float, default=0.0, help="seconds (required for test tones)")
    p.add_argument("--mono", action="store_true", help="one mic instead of two")
    p.add_argument("--balance", type=float, default=0.5, help="0 drum only .. 1 horn only")
    p.add_argument("--mix", type=float, default=1.0, help="0 dry .. 1 wet")
    p.add_argument("--dry", metavar="PATH", help="also write the unprocessed input here, loudness-matched")
    args = p.parse_args()

    x = load_input(args.input, args.duration or 30.0)
    start = time.time()
    y = render(x, parse_schedule(args.schedule), not args.mono, args.balance, args.mix)
    peak = np.max(np.abs(y))
    if peak > 1.0:
        print(f"warning: output peaks at {peak:.2f}, normalising")
        y /= peak
    sf.write(args.output, y.astype(np.float32), FS, subtype="FLOAT")
    print(f"{len(x) / FS:.1f} s rendered in {time.time() - start:.1f} s -> {args.output}")

    if args.dry:
        # Same loudness (RMS) as the effected file, so the comparison is fair
        dry = x * np.sqrt(np.mean(y**2)) / np.sqrt(np.mean(x**2))
        dry /= max(1.0, np.max(np.abs(dry)))
        sf.write(args.dry, np.repeat(dry[:, None], y.shape[1], axis=1).astype(np.float32), FS, subtype="FLOAT")
        print(f"dry, loudness-matched -> {args.dry}")


if __name__ == "__main__":
    main()
