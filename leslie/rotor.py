import math

STOP = 0
SLOW = 1
FAST = 2

MODE_NAMES = {"stop": STOP, "slow": SLOW, "fast": FAST}


class Rotor:
    """A Leslie rotor (horn or drum) easing toward its target speed.

    Speed is in revolutions per second (Hz). Spin-up and spin-down use separate
    one-pole time constants, since the heavy drum takes much longer than the horn.
    """

    def __init__(self, slow_hz, fast_hz, tau_up, tau_down, radius, direction=1):
        self.slow_hz = slow_hz
        self.fast_hz = fast_hz
        self.tau_up = tau_up
        self.tau_down = tau_down
        self.radius = radius
        self.direction = direction  # +1 or -1; horn and drum spin opposite ways

        self.angle = 0.0
        self.speed = slow_hz
        self.target = slow_hz

    def set_mode(self, mode):
        if mode == FAST:
            self.target = self.fast_hz
        elif mode == SLOW:
            self.target = self.slow_hz
        else:
            self.target = 0.0

    def step(self, dt):
        tau = self.tau_up if self.target > self.speed else self.tau_down
        self.speed += (self.target - self.speed) * min(dt / tau, 1.0)

        self.angle += self.direction * 2.0 * math.pi * self.speed * dt
        self.angle %= 2.0 * math.pi


def horn():
    return Rotor(slow_hz=0.8, fast_hz=6.7, tau_up=0.7, tau_down=0.8, radius=0.15, direction=1)


def drum():
    # The drum's woofer is fixed and fires into a rotating scoop, so the moving source is
    # smaller than the drum itself: radius is an effective value, not the drum size.
    return Rotor(slow_hz=0.7, fast_hz=5.9, tau_up=7.0, tau_down=9.0, radius=0.10, direction=-1)
