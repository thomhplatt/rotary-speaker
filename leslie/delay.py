import math


class FracDelay:
    """Circular buffer read at a fractional delay with 4-point Hermite interpolation.

    A delay of 0 is the most recently written sample. Reads need delay >= 1 so the
    sample "after" the read point already exists.
    """

    def __init__(self, size=256):
        assert size & (size - 1) == 0, "size must be a power of two"
        self.buf = [0.0] * size
        self.mask = size - 1
        self.w = 0  # index of the next write

    def write(self, x):
        self.buf[self.w] = x
        self.w = (self.w + 1) & self.mask

    def read_hermite(self, delay):
        i = int(math.floor(delay))
        f = delay - i
        n = self.w - 1 - i  # index of the sample at the integer delay
        buf, mask = self.buf, self.mask
        xm1 = buf[(n + 1) & mask]
        x0 = buf[n & mask]
        x1 = buf[(n - 1) & mask]
        x2 = buf[(n - 2) & mask]

        c1 = 0.5 * (x1 - xm1)
        c2 = xm1 - 2.5 * x0 + 2.0 * x1 - 0.5 * x2
        c3 = 0.5 * (x2 - xm1) + 1.5 * (x0 - x1)
        return ((c3 * f + c2) * f + c1) * f + x0
