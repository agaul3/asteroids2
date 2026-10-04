"""Transparent sprite assets; all sizing and rotation here are cosmetic."""

from functools import lru_cache
from pathlib import Path
import random

import pygame


ASSET_DIRECTORY = Path(__file__).resolve().parent / "assets" / "sprites"
ASTEROID_SPRITES = ("asteroid-mineral", "asteroid-scrap", "asteroid-crystal")
# Visual choices must not consume the random stream used for spawns and splits.
visual_random = random.Random()


@lru_cache(maxsize=5)
def _load_sprite(name: str) -> pygame.Surface:
    image = pygame.image.load(str(ASSET_DIRECTORY / f"{name}.png"))
    # Remove empty generation margins while retaining the visible neon halo.
    bounds = image.get_bounding_rect(min_alpha=8)
    return image.subsurface(bounds).copy()


@lru_cache(maxsize=32)
def _scaled_sprite(name: str, size: tuple[int, int]) -> pygame.Surface:
    return pygame.transform.smoothscale(_load_sprite(name), size)


@lru_cache(maxsize=512)
def _rotated_sprite(name: str, size: tuple[int, int], angle: int) -> pygame.Surface:
    return pygame.transform.rotate(_scaled_sprite(name, size), angle)


def get_sprite(name: str, size: tuple[int, int], angle: float = 0) -> pygame.Surface:
    """Return a shared cached surface. Callers should blit without modifying it."""
    return _rotated_sprite(name, size, round(angle) % 360)


def draw_centered(screen: pygame.Surface, image: pygame.Surface, position: pygame.Vector2) -> None:
    screen.blit(image, image.get_rect(center=(round(position.x), round(position.y))))
