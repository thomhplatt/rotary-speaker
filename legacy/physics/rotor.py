import math

STOP_SPEED = 0
SLOW_SPEED = 2
FAST_SPEED = 30

MAX_VEL = 50
p = 0.05

class Rotor:

    def __init__(self, radius):
        self.radius = radius

        self.angle_pos = 0.0
        self.angle_vel = 0.0
        self.angle_acc = 0.0

        self.target_vel = 0.0

        self.max_acc = 2.0
        self.max_vel = 10.0

    def update(self, dt):

        # set acceleration
        error = self.target_vel - self.angle_vel
        self.angle_acc = error * p
        self.angle_vel = max(-MAX_VEL, min(self.angle_vel, MAX_VEL)) # bounded
        
        
        # set velocity and bound
        self.angle_vel += self.angle_acc * dt
        self.angle_vel = max(-MAX_VEL, min(self.angle_vel, MAX_VEL)) # bounded

        # restrict backwards motion
        if self.angle_vel < 0:
            self.angle_vel = 0
            self.angle_acc = 0

        # set new position
        self.angle_pos += self.angle_vel * dt
        self.angle_pos %= 2 * math.pi







