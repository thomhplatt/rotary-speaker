from leslie import biquad


class Crossover:
    """4th-order Linkwitz-Riley crossover: two cascaded Butterworth biquads per band.

    The low and high outputs are in phase, so low + high sums to a flat (allpass) response.
    """

    def __init__(self, fs, fc=800.0):
        self.lp1 = biquad.lowpass(fs, fc)
        self.lp2 = biquad.lowpass(fs, fc)
        self.hp1 = biquad.highpass(fs, fc)
        self.hp2 = biquad.highpass(fs, fc)

    def process(self, x):
        low = self.lp2.process(self.lp1.process(x))
        high = self.hp2.process(self.hp1.process(x))
        return low, high
