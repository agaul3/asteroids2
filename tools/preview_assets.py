"""Render the asset gallery with the same sprite renderer as the game."""

import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pygame
from visuals import ASTEROID_SPRITES, draw_centered, get_sprite
from constants import PLAYER_RADIUS


def main():
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    screen.fill((8, 12, 20))
    fonts = {size: pygame.font.SysFont("menlo,dejavusansmono,consolas", size) for size in (14, 18, 32)}
    cyan, yellow, muted = (62, 224, 241), (252, 230, 38), (140, 159, 179)

    def text(label, x, y, size=14, color=muted):
        screen.blit(fonts[size].render(label, True, color), (x, y))

    pygame.draw.line(screen, yellow, (40, 32), (1240, 32), 2)
    text("CYBERPUNK // ORBITAL ASSETS", 40, 52, 32, yellow)
    text("GRAPHITE ARMOR  /  NEON ENERGY  /  NIGHT CITY PALETTE", 42, 99)
    cards = [
        (40, 320, "01 / INTERCEPTOR", "player", (176, 264), "YELLOW ARMOR + CYAN DRIVE"),
        (380, 270, "02 / MINERAL", ASTEROID_SPRITES[0], (205, 205), "IONIZED CYAN FISSURES"),
        (670, 270, "03 / SALVAGE", ASTEROID_SPRITES[1], (205, 205), "SCRAP ARMOR + WARNING LEDs"),
        (960, 280, "04 / CRYSTAL", ASTEROID_SPRITES[2], (205, 205), "MAGENTA CRYSTAL OUTCROPS"),
    ]
    for x, width, title, name, size, caption in cards:
        pygame.draw.rect(screen, (13, 20, 31), (x, 140, width, 360))
        pygame.draw.rect(screen, (42, 60, 75), (x, 140, width, 360), 1)
        pygame.draw.line(screen, cyan, (x, 140), (x + 60, 140), 2)
        text(title, x + 16, 158, 18, cyan)
        draw_centered(screen, get_sprite(name, size), pygame.Vector2(x + width / 2, 327))
        text(caption, x + 16, 472)

    text("ACTUAL GAME SCALE / 1280 x 720", 40, 529, 18, yellow)
    size = (round(PLAYER_RADIUS * 4 / 3), round(PLAYER_RADIUS * 2))
    draw_centered(screen, get_sprite("player", size), pygame.Vector2(82, 610))
    text("SHIP", 61, 659)
    draw_centered(screen, get_sprite("shot", (10, 20)), pygame.Vector2(163, 610))
    text("LASER", 140, 659)
    for index, name in enumerate(ASTEROID_SPRITES):
        x = 260 + index * 330
        for radius, offset in ((20, 0), (40, 75), (60, 190)):
            diameter = radius * 2
            draw_centered(screen, get_sprite(name, (diameter, diameter)), pygame.Vector2(x + offset, 608))
        text("40px / 80px / 120px", x - 15, 677)
    pygame.image.save(screen, str(ROOT / "assets" / "preview.png"))
    pygame.quit()


if __name__ == "__main__":
    main()
