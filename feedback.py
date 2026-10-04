"""Coordinate a single combat event's animation and matching sound."""

import pygame

from effects import CYAN, MAGENTA, PALETTES, MuzzleFlash, NovaBurst, ShieldRupture
from visuals import draw_centered, get_sprite


class FeedbackController:
    def __init__(self, sounds):
        self.sounds = sounds
        self.effects = pygame.sprite.Group()
        self.damage = None
        self.death = None
        self.dead = False

    @property
    def death_complete(self):
        return self.death is not None and self.death.finished

    def laser_fired(self, player):
        if self.dead:
            return
        self.effects.add(MuzzleFlash(player))
        self.sounds.play("laser")

    def asteroid_destroyed(self, asteroid, cause="laser"):
        self.effects.add(NovaBurst(asteroid.position, asteroid.radius, asteroid.image,
                                   PALETTES.get(asteroid.visual_variant, CYAN)))
        if cause == "laser":
            self.sounds.play("asteroid_hit")

    def player_damaged(self, player, fatal=False):
        if self.dead:
            return
        if fatal:
            self.dead = True
            for effect in tuple(self.effects):
                if isinstance(effect, (MuzzleFlash, ShieldRupture)):
                    effect.kill()
            self.damage = None
            size = (round(player.radius * 4 / 3), round(player.radius * 2))
            image = get_sprite("player", size, 180 - player.rotation)
            self.death = NovaBurst(player.position, player.radius, image, MAGENTA, fatal=True)
            self.effects.add(self.death)
            self.sounds.play("game_over")
        else:
            if self.damage is not None and not self.damage.finished:
                self.damage.restart()
            else:
                self.damage = ShieldRupture(player)
                self.effects.add(self.damage)
            self.sounds.play("player_hit")

    def update(self, dt):
        self.effects.update(dt)
        if self.damage is not None and self.damage.finished:
            self.damage = None

    def draw_player(self, screen, player, image):
        if self.dead:
            return
        if self.damage is not None:
            # Copy before tinting/flickering: cached sprites stay immutable.
            image = image.copy()
            if int(self.damage.age * 30) % 2 == 0:
                image.fill((45, 105, 120, 0), special_flags=pygame.BLEND_RGBA_ADD)
            else:
                image.set_alpha(145)
        draw_centered(screen, image, player.position)

    def draw(self, screen):
        for effect in self.effects:
            effect.draw(screen)
