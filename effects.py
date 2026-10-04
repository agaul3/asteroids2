"""Time-based combat effects. These sprites never participate in collisions."""

import math
import random
from functools import lru_cache

import pygame

from visuals import draw_centered


CYAN = (55, 230, 255)
MAGENTA = (255, 45, 167)
YELLOW = (255, 220, 45)
WHITE = (230, 255, 255)
PALETTES = {
    "asteroid-mineral": CYAN,
    "asteroid-scrap": YELLOW,
    "asteroid-crystal": MAGENTA,
}
# Independent of both asteroid geometry and spawn/split randomness.
effect_random = random.Random()


@lru_cache(maxsize=96)
def _glow(radius, color):
    extent = math.ceil(radius * 1.8)
    image = pygame.Surface((extent * 2 + 1, extent * 2 + 1), pygame.SRCALPHA)
    for distance in range(extent, 0, -1):
        opacity = round(255 * math.exp(-3 * (distance / radius) ** 2))
        pygame.draw.circle(image, (*color, opacity), (extent, extent), distance)
    return image


def glow_disc(canvas, center, radius, color, alpha):
    # Smooth radial alpha, without changing shared cached glow surfaces.
    image = _glow(max(1, round(radius)), color).copy()
    image.set_alpha(alpha)
    canvas.blit(image, image.get_rect(center=center))


def neon_ring(canvas, center, radius, color, alpha):
    radius = max(1, round(radius))
    pygame.draw.circle(canvas, (*color, round(alpha * 0.18)), center, radius, min(radius, 5))
    pygame.draw.circle(canvas, (*color, round(alpha * 0.7)), center, radius, min(radius, 2))
    pygame.draw.circle(canvas, (*WHITE, alpha), center, radius, 1)


def local_point(center, offset):
    return (round(center[0] + offset.x), round(center[1] + offset.y))


class Effect(pygame.sprite.Sprite):
    def __init__(self, duration, canvas_size):
        super().__init__()
        self.duration = duration
        self.age = 0.0
        self.canvas = pygame.Surface((canvas_size, canvas_size), pygame.SRCALPHA)
        self.center = (canvas_size // 2, canvas_size // 2)

    @property
    def progress(self):
        return min(1.0, self.age / self.duration)

    @property
    def finished(self):
        return self.age >= self.duration - 1e-9

    def update(self, dt):
        self.age += max(0, dt)
        if self.finished:
            self.kill()


class MuzzleFlash(Effect):
    def __init__(self, player):
        super().__init__(0.12, 80)
        self.player = player

    def draw(self, screen):
        self.canvas.fill((0, 0, 0, 0))
        p = self.progress
        alpha = round(255 * (1 - p))
        forward = pygame.Vector2(0, 1).rotate(self.player.rotation)
        right = forward.rotate(90)
        position = self.player.position + forward * self.player.radius
        neon_ring(self.canvas, self.center, 3 + p * 14, CYAN, alpha)
        glow_disc(self.canvas, self.center, 6 * (1 - p) + 1, CYAN, alpha)
        tip = forward * (15 * (1 - p) + 4)
        points = [local_point(self.center, tip), local_point(self.center, right * 4),
                  local_point(self.center, -forward * 4), local_point(self.center, -right * 4)]
        pygame.draw.polygon(self.canvas, (*WHITE, alpha), points)
        draw_centered(screen, self.canvas, position)


class ShieldRupture(Effect):
    def __init__(self, player):
        super().__init__(0.55, math.ceil(player.radius * 5))
        self.player = player

    def restart(self):
        self.age = 0.0

    def draw(self, screen):
        self.canvas.fill((0, 0, 0, 0))
        p = self.progress
        radius = self.player.radius * (1.18 + p * 0.25)
        alpha = round(235 * (1 - p))
        angle = math.radians(self.player.rotation)
        rect = pygame.Rect(0, 0, round(radius * 2), round(radius * 2))
        rect.center = self.center
        # Broken shield arcs rotate with the hull.
        for offset in (0, math.pi):
            pygame.draw.arc(self.canvas, (*CYAN, alpha), rect,
                            angle + offset, angle + offset + 2.2, 3)
        for offset in (-65, 65, 180):
            direction = pygame.Vector2(0, 1).rotate(self.player.rotation + offset)
            side = direction.rotate(90)
            distances = (0.35, 0.7, 0.85, 1.15, 1.35)
            points = [local_point(self.center, direction * self.player.radius * d
                                 + side * ((-1) ** i) * (3 + 4 * p))
                      for i, d in enumerate(distances)]
            pygame.draw.lines(self.canvas, (*MAGENTA, alpha), False, points, 2)
        if p < 0.2:
            glow_disc(self.canvas, self.center, radius * 0.7, CYAN, round(alpha * 0.45))
        draw_centered(screen, self.canvas, self.player.position)


class NovaBurst(Effect):
    """Flash and real sprite fragments, followed by a neon nova and sparks."""

    def __init__(self, position, radius, image, color=CYAN, fatal=False):
        super().__init__(1.4 if fatal else 0.55, math.ceil(radius * 9 + 120))
        self.position = pygame.Vector2(position)
        self.radius = radius
        self.color = color
        self.fatal = fatal
        self.flash = image.copy()
        self.flash.fill((120, 170, 170, 0), special_flags=pygame.BLEND_RGBA_ADD)
        self.fragments = []
        width, height = image.get_size()
        for row in range(4):
            for column in range(4):
                left, top = column * width // 4, row * height // 4
                rect = pygame.Rect(left, top, (column + 1) * width // 4 - left,
                                   (row + 1) * height // 4 - top)
                fragment = image.subsurface(rect).copy()
                if not pygame.mask.from_surface(fragment).count():
                    continue
                offset = pygame.Vector2(rect.center) - pygame.Vector2(width / 2, height / 2)
                direction = offset.normalize() if offset.length_squared() else pygame.Vector2(1, 0)
                direction = direction.rotate(effect_random.uniform(-18, 18))
                speed = effect_random.uniform(65, 135) * radius / 32.5
                self.fragments.append((fragment, offset, direction * speed,
                                       effect_random.uniform(-180, 180)))
        self.sparks = []
        for _ in range(22):
            direction = pygame.Vector2(1, 0).rotate(effect_random.uniform(0, 360))
            speed = effect_random.uniform(100, 220) * radius / 32.5
            self.sparks.append(direction * speed)

    def draw(self, screen):
        self.canvas.fill((0, 0, 0, 0))
        p = self.progress
        # Fatal overload holds the intact glowing hull briefly before separation.
        delay = 0.12 if self.fatal else 0
        travel = max(0, self.age - delay)
        fragment_alpha = round(255 * (1 - p) ** 1.3)
        for image, offset, velocity, spin in self.fragments:
            if self.fatal and self.age < delay:
                continue
            rotated = pygame.transform.rotate(image, spin * travel)
            rotated.set_alpha(fragment_alpha)
            location = pygame.Vector2(self.center) + offset + velocity * travel
            draw_centered(self.canvas, rotated, location)
        if self.age < (0.17 if self.fatal else 0.08):
            flash = self.flash.copy()
            flash.set_alpha(round(255 * max(0, 1 - self.age / (0.17 if self.fatal else 0.08))))
            draw_centered(self.canvas, flash, pygame.Vector2(self.center))
        ring_progress = min(1, self.age / (0.7 if self.fatal else 0.55))
        ring_alpha = round(245 * (1 - ring_progress))
        neon_ring(self.canvas, self.center, self.radius * (0.35 + ring_progress * 1.8),
                  CYAN, ring_alpha)
        if self.age < 0.18:
            glow_disc(self.canvas, self.center, self.radius * (0.65 + self.age * 2),
                      WHITE, round(255 * (1 - self.age / 0.18)))
        # Preserve each asteroid's identity in its fragment lights and embers.
        for index, velocity in enumerate(self.sparks):
            position = velocity * travel
            tail = position - velocity * min(0.04, travel)
            alpha = round(255 * (1 - p) ** 1.5)
            color = self.color if index % 3 else MAGENTA
            pygame.draw.line(self.canvas, (*color, alpha), local_point(self.center, tail),
                             local_point(self.center, position), 2 if index % 4 == 0 else 1)
        draw_centered(screen, self.canvas, self.position)
