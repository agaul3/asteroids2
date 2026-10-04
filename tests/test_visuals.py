import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
import unittest
from unittest.mock import patch

import pygame

from asteroid import Asteroid
from constants import PLAYER_SHOOT_COOLDOWN_SECONDS, PLAYER_SHOOT_SPEED, SHOT_RADIUS
from player import Player
from shot import Shot
from visuals import ASTEROID_SPRITES, get_sprite, visual_random


class VisualIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.random_state = random.getstate()
        self.visual_state = visual_random.getstate()
        self.shots = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        Shot.containers = (self.shots,)
        Asteroid.containers = (self.asteroids,)
        self.screen = pygame.Surface((256, 256), pygame.SRCALPHA)

    def tearDown(self):
        random.setstate(self.random_state)
        visual_random.setstate(self.visual_state)
        del Shot.containers
        del Asteroid.containers

    def test_all_assets_have_transparency_and_visible_art(self):
        for name in ("player", "shot", *ASTEROID_SPRITES):
            with self.subTest(name=name):
                image = get_sprite(name, (80, 80))
                self.assertTrue(image.get_flags() & pygame.SRCALPHA)
                self.assertEqual(image.get_at((0, 0)).a, 0)
                self.assertGreater(pygame.mask.from_surface(image).count(), 20)

    def test_laser_rotates_with_velocity_without_changing_physics(self):
        for velocity in ((0, -500), (500, 0), (0, 500), (-500, 0), (0, 0)):
            with self.subTest(velocity=velocity):
                self.screen.fill((0, 0, 0, 0))
                shot = Shot(128, 128)
                shot.velocity = pygame.Vector2(velocity)
                shot.draw(self.screen)
                bounds = self.screen.get_bounding_rect(min_alpha=64)
                self.assertGreater(bounds.width, 0)
                if velocity[0]:
                    self.assertGreater(bounds.width, bounds.height)
                else:
                    self.assertGreater(bounds.height, bounds.width)
                self.assertEqual(shot.radius, SHOT_RADIUS)
                self.assertEqual(shot.velocity, pygame.Vector2(velocity))
                shot.update(0.1)
                self.assertEqual(shot.position, pygame.Vector2(128, 128) + pygame.Vector2(velocity) * 0.1)

    def test_shooting_speed_and_cooldown_remain_unchanged(self):
        player = Player(128, 128)
        player.rotation = 90
        player.shoot()
        player.shoot()
        self.assertEqual(len(self.shots), 1)
        shot = self.shots.sprites()[0]
        self.assertEqual(shot.position, player.position)
        self.assertEqual(shot.velocity, pygame.Vector2(0, 1).rotate(90) * PLAYER_SHOOT_SPEED)
        self.assertEqual(player.cooldown_timer, PLAYER_SHOOT_COOLDOWN_SECONDS)

    def test_drawing_ship_preserves_triangle_and_collision(self):
        player = Player(128, 128)
        near = Asteroid(128, 150, 20)
        far = Asteroid(220, 220, 20)
        for rotation in (0, 45, 90, 180, 270):
            player.rotation = rotation
            triangle = player.triangle()
            collisions = (player.collides_with(near), player.collides_with(far))
            player.draw(self.screen)
            self.assertEqual(player.triangle(), triangle)
            self.assertEqual((player.collides_with(near), player.collides_with(far)), collisions)
        self.assertFalse(player.collides_with(far))

    def test_asteroid_styles_do_not_consume_gameplay_randomness(self):
        random.seed(2077)
        for _ in range(10):
            random.uniform(15, 20)
        expected_state = random.getstate()
        random.seed(2077)
        Asteroid(128, 128, 20)
        self.assertEqual(random.getstate(), expected_state)
        visual_random.seed(2077)
        variants = {Asteroid(128, 128, 20).visual_variant for _ in range(24)}
        self.assertEqual(variants, set(ASTEROID_SPRITES))

    def test_asteroid_movement_and_splitting_remain_unchanged(self):
        parent = Asteroid(128, 128, 60)
        parent.velocity = pygame.Vector2(50, 0)
        parent.update(0.2)
        self.assertEqual(parent.position, pygame.Vector2(138, 128))
        with patch("asteroid.log_event"):
            parent.split()
        self.assertNotIn(parent, self.asteroids)
        self.assertEqual(len(self.asteroids), 2)
        for child in self.asteroids:
            self.assertEqual(child.radius, 40)
            self.assertEqual(child.position, parent.position)
            self.assertAlmostEqual(child.velocity.length(), 60)
            child.draw(self.screen)

    def test_cached_surfaces_are_reused(self):
        first = get_sprite("player", (27, 40), 181)
        self.assertIs(first, get_sprite("player", (27, 40), 541))


if __name__ == "__main__":
    unittest.main()
