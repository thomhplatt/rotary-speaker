import math


class Biquad:
    """Transposed Direct Form II biquad, one sample at a time."""

    def __init__(self, b0, b1, b2, a1, a2):
        self.b0, self.b1, self.b2 = b0, b1, b2
        self.a1, self.a2 = a1, a2
        self.z1 = 0.0
        self.z2 = 0.0

    def process(self, x):
        y = self.b0 * x + self.z1
        self.z1 = self.b1 * x - self.a1 * y + self.z2
        self.z2 = self.b2 * x - self.a2 * y
        return y


# ===== RBJ cookbook coefficients (Butterworth Q = 1/sqrt(2)) =====
BUTTERWORTH_Q = 1.0 / math.sqrt(2.0)


def lowpass(fs, fc, q=BUTTERWORTH_Q):
    w0 = 2.0 * math.pi * fc / fs
    c = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)
    a0 = 1.0 + alpha
    return Biquad(
        (1.0 - c) / 2.0 / a0,
        (1.0 - c) / a0,
        (1.0 - c) / 2.0 / a0,
        -2.0 * c / a0,
        (1.0 - alpha) / a0,
    )


def highpass(fs, fc, q=BUTTERWORTH_Q):
    w0 = 2.0 * math.pi * fc / fs
    c = math.cos(w0)
    alpha = math.sin(w0) / (2.0 * q)
    a0 = 1.0 + alpha
    return Biquad(
        (1.0 + c) / 2.0 / a0,
        -(1.0 + c) / a0,
        (1.0 + c) / 2.0 / a0,
        -2.0 * c / a0,
        (1.0 - alpha) / a0,
    )
