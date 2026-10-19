"""Sanity checks for the Leslie model. Prints numbers and writes plots to out/check.png.

  python -m tools.check
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import hilbert

from leslie import rotor
from leslie.crossover import Crossover
from render import FS, render

N_FFT = 1 << 15


def crossover_response():
    xo = Crossover(FS)
    low = np.zeros(N_FFT)
    high = np.zeros(N_FFT)
    for n in range(N_FFT):
        low[n], high[n] = xo.process(1.0 if n == 0 else 0.0)
    f = np.fft.rfftfreq(N_FFT, 1 / FS)
    db = lambda h: 20 * np.log10(np.maximum(np.abs(np.fft.rfft(h)), 1e-12))
    return f, db(low), db(high), db(low + high)


def rotor_ramp(make_rotor, seconds=40.0):
    """Speed over time for slow -> fast at t=0 -> slow at half time."""
    r = make_rotor()
    dt = 1 / 1000
    t = np.arange(int(seconds / dt)) * dt
    speed = np.zeros_like(t)
    for i, ti in enumerate(t):
        r.set_mode(rotor.FAST if ti < seconds / 2 else rotor.SLOW)
        r.step(dt)
        speed[i] = r.speed
    return t, speed


def time_to(t, speed, start, end, fraction=0.63):
    target = start + fraction * (end - start)
    hit = np.nonzero((speed - target) * np.sign(end - start) >= 0)[0]
    return t[hit[0]] if len(hit) else float("nan")


def pitch_wobble(f0=440.0):
    """Instantaneous frequency of a mono sine render held on fast (horn only)."""
    t = np.arange(4 * FS) / FS
    x = 0.5 * np.sin(2 * np.pi * f0 * t)
    y = render(x, [(0.0, rotor.FAST)], stereo=False, balance=1.0)[:, 0]
    phase = np.unwrap(np.angle(hilbert(y)))
    inst = np.diff(phase) * FS / (2 * np.pi)
    settled = inst[3 * FS : -1000]  # horn has reached speed; skip the Hilbert edge
    cents = 1200 * np.log2(settled / f0)
    return t[1:], inst, cents


def main():
    os.makedirs("out", exist_ok=True)
    fig, ax = plt.subplots(3, 1, figsize=(9, 11))

    f, low, high, total = crossover_response()
    band = (f > 20) & (f < 20000)
    print(f"crossover: low+high deviation {total[band].min():+.3f} .. {total[band].max():+.3f} dB")
    print(f"crossover: low/high at 800 Hz {np.interp(800, f, low):.2f} / {np.interp(800, f, high):.2f} dB (LR4 expects -6.02)")
    ax[0].semilogx(f[band], low[band], label="low (drum)")
    ax[0].semilogx(f[band], high[band], label="high (horn)")
    ax[0].semilogx(f[band], total[band], "k--", label="sum")
    ax[0].set(ylim=(-60, 6), xlabel="Hz", ylabel="dB", title="LR4 crossover @ 800 Hz")
    ax[0].legend()

    for name, make in (("horn", rotor.horn), ("drum", rotor.drum)):
        r = make()
        t, speed = rotor_ramp(make)
        half = len(t) // 2
        up = time_to(t[:half], speed[:half], r.slow_hz, r.fast_hz)
        down = time_to(t[half:], speed[half:], r.fast_hz, r.slow_hz) - t[half]
        print(f"{name}: 63% spin-up {up:.2f} s (tau {r.tau_up}), spin-down {down:.2f} s (tau {r.tau_down})")
        ax[1].plot(t, speed, label=name)
    ax[1].set(xlabel="s", ylabel="rev/s", title="Rotor speed: fast at 0 s, slow at 20 s")
    ax[1].legend()

    t, inst, cents = pitch_wobble()
    print(f"horn fast pitch wobble: {cents.min():+.1f} .. {cents.max():+.1f} cents (expect about ±32)")
    ax[2].plot(t[: len(inst)], inst, lw=0.5)
    ax[2].set(xlim=(0, 4), ylim=(400, 480), xlabel="s", ylabel="Hz", title="440 Hz sine, horn only, slow -> fast")

    fig.tight_layout()
    fig.savefig("out/check.png", dpi=110)
    print("plots -> out/check.png")


if __name__ == "__main__":
    main()
