"""Top-down view of the Leslie model: horn and drum spinning, mic positions, speed buttons."""
import math
import time

import pygame

from leslie import rotor
from leslie.leslie import MIC_DISTANCE, STEREO_MIC_ANGLES

PPM = 400  # pixels per metre
CENTER = (250, 220)

horn = rotor.horn()
drum = rotor.drum()

pygame.init()
screen = pygame.display.set_mode((500, 500))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Mono", 15)

# Buttons
buttons = {
    rotor.SLOW: (pygame.Rect(50, 430, 100, 50), font.render("Slow", True, "black")),
    rotor.FAST: (pygame.Rect(200, 430, 100, 50), font.render("Fast", True, "black")),
    rotor.STOP: (pygame.Rect(350, 430, 100, 50), font.render("Stop", True, "black")),
}


def to_screen(x, y):
    return CENTER[0] + x * PPM, CENTER[1] + y * PPM


def draw_rotor(r, color):
    tip = to_screen(r.radius * math.cos(r.angle), r.radius * math.sin(r.angle))
    pygame.draw.circle(screen, color, CENTER, r.radius * PPM, 1)
    pygame.draw.line(screen, color, CENTER, tip, 3)
    return tip


previous_time = time.time()
running = True
while running:

    # ----- input -----
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for mode, (rect, _) in buttons.items():
                if rect.collidepoint(event.pos):
                    horn.set_mode(mode)
                    drum.set_mode(mode)

    # ----- time -----
    current_time = time.time()
    dt = current_time - previous_time
    previous_time = current_time

    # ----- physics -----
    horn.step(dt)
    drum.step(dt)

    # ----- draw -----
    screen.fill("grey")

    for rect, text in buttons.values():
        pygame.draw.rect(screen, "white", rect, border_radius=5)
        screen.blit(text, text.get_rect(center=rect.center))

    drum_tip = draw_rotor(drum, "orange")
    horn_tip = draw_rotor(horn, "white")

    # mics, with lines from each rotor
    for angle in STEREO_MIC_ANGLES:
        mic = to_screen(MIC_DISTANCE * math.cos(angle), MIC_DISTANCE * math.sin(angle))
        pygame.draw.line(screen, "blue", horn_tip, mic, 1)
        pygame.draw.line(screen, "brown", drum_tip, mic, 1)
        pygame.draw.circle(screen, "red", mic, 5)

    label = f"horn {horn.speed:4.2f} rev/s   drum {drum.speed:4.2f} rev/s"
    screen.blit(font.render(label, True, "black"), (20, 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
