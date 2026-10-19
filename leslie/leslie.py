import math

from leslie import rotor
from leslie.crossover import Crossover
from leslie.delay import FracDelay

SOUND = 343.0       # speed of sound, m/s
MIC_DISTANCE = 0.5  # mic distance from the cabinet centre, m
MIN_DELAY = 2.0     # samples; keeps Hermite reads inside written data
DELAY_SIZE = 256    # samples; must cover 2 * radius / SOUND * fs + MIN_DELAY + 2

HORN_DIRECTIVITY = 0.7  # 0 = omnidirectional, 1 = silent when facing away
DRUM_DIRECTIVITY = 0.35  # low frequencies barely beam, so the drum is mostly omni

STEREO_MIC_ANGLES = (math.radians(-60.0), math.radians(60.0))
MONO_MIC_ANGLES = (0.0,)


class Voice:
    """One rotor heard by one mic: a delay line for Doppler, a gain for directivity and distance."""

    def __init__(self, fs, rot, mic_angle, directivity):
        self.fs = fs
        self.rotor = rot
        self.mic_x = MIC_DISTANCE * math.cos(mic_angle)
        self.mic_y = MIC_DISTANCE * math.sin(mic_angle)
        self.cos_mic = math.cos(mic_angle)
        self.sin_mic = math.sin(mic_angle)
        self.k = directivity
        self.norm = 1.0 / ((1.0 - directivity) + 0.5 * directivity)  # average gain -> 1
        self.base = MIC_DISTANCE - rot.radius  # closest approach, removed from the delay
        self.delay = FracDelay(DELAY_SIZE)

    def process(self, x, cos_t, sin_t):
        self.delay.write(x)

        r = self.rotor.radius
        dx = self.mic_x - r * cos_t
        dy = self.mic_y - r * sin_t
        dist = math.sqrt(dx * dx + dy * dy)

        d = (dist - self.base) / SOUND * self.fs + MIN_DELAY
        y = self.delay.read_hermite(d)

        facing = cos_t * self.cos_mic + sin_t * self.sin_mic  # cos(theta - phi)
        gain = (1.0 - self.k) + self.k * 0.5 * (1.0 + facing)
        gain *= self.norm * MIC_DISTANCE / dist
        return y * gain


class Leslie:
    def __init__(self, fs, stereo=True, crossover_hz=800.0):
        self.fs = fs
        self.dt = 1.0 / fs
        self.stereo = stereo
        self.crossover = Crossover(fs, crossover_hz)
        self.horn = rotor.horn()
        self.drum = rotor.drum()

        angles = STEREO_MIC_ANGLES if stereo else MONO_MIC_ANGLES
        self.horn_voices = [Voice(fs, self.horn, a, HORN_DIRECTIVITY) for a in angles]
        self.drum_voices = [Voice(fs, self.drum, a, DRUM_DIRECTIVITY) for a in angles]

        self.horn_gain = 1.0
        self.drum_gain = 1.0
        self.mix = 1.0

    def set_mode(self, mode):
        self.horn.set_mode(mode)
        self.drum.set_mode(mode)

    def set_balance(self, balance):
        """0 = drum only, 0.5 = equal, 1 = horn only."""
        self.horn_gain = min(1.0, 2.0 * balance)
        self.drum_gain = min(1.0, 2.0 * (1.0 - balance))

    def set_mix(self, mix):
        """0 = dry, 1 = fully wet."""
        self.mix = mix

    def process(self, x):
        low, high = self.crossover.process(x)

        self.horn.step(self.dt)
        self.drum.step(self.dt)
        hc, hs = math.cos(self.horn.angle), math.sin(self.horn.angle)
        dc, ds = math.cos(self.drum.angle), math.sin(self.drum.angle)

        out = []
        for hv, dv in zip(self.horn_voices, self.drum_voices):
            wet = self.horn_gain * hv.process(high, hc, hs) + self.drum_gain * dv.process(low, dc, ds)
            out.append(self.mix * wet + (1.0 - self.mix) * x)

        if self.stereo:
            return out[0], out[1]
        return out[0], out[0]
