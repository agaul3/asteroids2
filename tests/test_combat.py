import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from array import array
import random
import sys
import unittest
from unittest.mock import Mock, patch
import wave

import pygame

from asteroid import Asteroid
from asteroidfield import AsteroidField
from audio import AUDIO_DIRECTORY, SoundManager
from constants import PLAYER_RADIUS, PLAYER_SHOOT_SPEED
from effects import MuzzleFlash, NovaBurst, ShieldRupture
from feedback import FeedbackController
from main import Game, main
from player import Player
from shot import Shot
from tools.generate_sfx import DURATIONS, RATE, synthesize
from visuals import ASTEROID_SPRITES, get_sprite


class CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        cls.screen = pygame.display.set_mode((1280, 720))

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.original_containers = {cls: cls.__dict__.get("containers")
                                    for cls in (Player, Shot, Asteroid, AsteroidField)}
        self.sounds = Mock()
        self.feedback = FeedbackController(self.sounds)
        self.gameplay_random_state = random.getstate()

    def tearDown(self):
        random.setstate(self.gameplay_random_state)
        for cls, original in self.original_containers.items():
            if original is None:
                if "containers" in cls.__dict__:
                    del cls.containers
            else:
                cls.containers = original

    def make_game(self):
        game = Game(self.screen, self.sounds)
        game.field.kill()  # deterministic manual fixtures instead of timed spawns
        return game

    def test_ship_geometry_scales_at_every_heading(self):
        player = Player(640, 360)
        self.assertEqual(PLAYER_RADIUS, 20 * 1.625)
        for angle in (0, 30, 90, 180, 270):
            player.rotation = angle
            forward = pygame.Vector2(0, 1).rotate(angle)
            right = forward.rotate(90)
            for point, old_offset in zip(player.triangle(),
                                        (forward * 20, -forward * 20 - right * 20 / 1.5,
                                         -forward * 20 + right * 20 / 1.5)):
                self.assertLess((point - player.position - old_offset * 1.625).length(), 1e-6)
        image = get_sprite("player", (round(player.radius * 4 / 3), round(player.radius * 2)))
        self.assertEqual(image.get_size(), (43, 65))
        player.rotation = 0
        self.assertTrue(player.collides_with(Asteroid(640, 393, 1)))
        self.assertFalse(player.collides_with(Asteroid(640, 395, 1)))

    def test_shooting_feedback_only_on_success(self):
        game = self.make_game()
        game.player.shoot()
        game.player.shoot()
        self.sounds.play.assert_called_once_with("laser")
        self.assertEqual(len(game.shots), 1)
        self.assertEqual(len(game.feedback.effects), 1)
        shot = game.shots.sprites()[0]
        self.assertEqual(shot.position, game.player.position)
        self.assertAlmostEqual(shot.velocity.length(), PLAYER_SHOOT_SPEED)
        game.feedback.update(0.12)
        self.assertEqual(len(game.feedback.effects), 0)

    def test_shot_flash_tracks_moving_rotating_nose(self):
        player = Player(640, 360)
        effect = MuzzleFlash(player)
        player.move(0.5)
        player.rotation = 90
        surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        effect.draw(surface)
        bounds = surface.get_bounding_rect(min_alpha=32)
        nose = player.position + pygame.Vector2(0, 1).rotate(90) * player.radius
        self.assertLess(pygame.Vector2(bounds.center).distance_to(nose), 12)

    def test_asteroid_hit_scores_splits_and_triggers_once(self):
        game = self.make_game()
        parent = Asteroid(120, 120, 60)
        parent.velocity = pygame.Vector2(50, 0)
        Shot(120, 120)
        with patch("main.log_event"), patch("asteroid.log_event"):
            game.update(0)
        self.assertEqual(game.score, 1)
        self.assertEqual(len(game.shots), 0)
        self.assertEqual(len(game.asteroids), 2)
        self.sounds.play.assert_called_once_with("asteroid_hit")
        for child in game.asteroids:
            self.assertEqual(child.radius, 40)
            self.assertAlmostEqual(child.velocity.length(), 60)
        self.assertEqual(len(game.feedback.effects), 1)
        self.assertTrue(all(not isinstance(effect, (Asteroid, Shot, Player))
                            for effect in game.feedback.effects))

    def test_all_asteroid_variants_sizes_and_simultaneous_hits_render(self):
        game = self.make_game()
        for index, variant in enumerate(ASTEROID_SPRITES):
            for radius in (20, 40, 60):
                asteroid = Asteroid(120 + index * 300, 120 + radius, radius)
                asteroid.visual_variant = variant
                asteroid.image = get_sprite(variant, (radius * 2, radius * 2))
                game.feedback.asteroid_destroyed(asteroid)
        self.assertEqual(len(game.feedback.effects), 9)
        for _ in range(4):
            game.feedback.draw(self.screen)
            game.feedback.update(0.15)
        self.assertEqual(len(game.feedback.effects), 0)

    def test_nonfatal_collision_has_no_extra_asteroid_sound(self):
        game = self.make_game()
        Asteroid(*game.player.position, 20)
        with patch("main.log_event"):
            game.update(0)
        self.assertEqual(game.lives, 2)
        self.assertEqual(len(game.asteroids), 0)
        self.assertFalse(game.game_over)
        self.sounds.play.assert_called_once_with("player_hit")
        self.assertIsInstance(game.feedback.damage, ShieldRupture)
        # Movement is still allowed during the damage animation.
        before = game.player.position.copy()
        game.player.move(0.1)
        self.assertEqual(game.player.position, before + pygame.Vector2(0, 20))

    def test_repeated_damage_restarts_and_fatal_cancels_attached_effects(self):
        player = Player(640, 360, self.feedback)
        self.feedback.player_damaged(player)
        original = self.feedback.damage
        self.feedback.update(0.2)
        self.feedback.player_damaged(player)
        self.assertIs(self.feedback.damage, original)
        self.assertEqual(original.age, 0)
        self.feedback.laser_fired(player)
        self.feedback.player_damaged(player, fatal=True)
        self.feedback.player_damaged(player, fatal=True)
        self.assertIsNone(self.feedback.damage)
        self.assertEqual(len(self.feedback.effects), 1)
        self.assertIsInstance(self.feedback.death, NovaBurst)
        events = [call.args[0] for call in self.sounds.play.call_args_list]
        self.assertEqual(events.count("game_over"), 1)

    def test_damage_tracks_player_and_never_mutates_cached_image(self):
        player = Player(500, 300, self.feedback)
        size = (43, 65)
        image = get_sprite("player", size)
        before = pygame.image.tobytes(image, "RGBA")
        self.feedback.player_damaged(player)
        player.position = pygame.Vector2(700, 400)
        player.rotation = 90
        surface = pygame.Surface((1280, 720), pygame.SRCALPHA)
        self.feedback.draw(surface)
        self.assertLess(pygame.Vector2(surface.get_bounding_rect(min_alpha=32).center)
                        .distance_to(player.position), 10)
        player.draw(surface)
        self.assertEqual(before, pygame.image.tobytes(image, "RGBA"))

    def test_fatal_collision_freezes_world_and_overlay_waits_for_animation(self):
        game = self.make_game()
        game.lives = 1
        Asteroid(*game.player.position, 20)
        Asteroid(*game.player.position, 20)
        survivor = Asteroid(100, 100, 40)
        survivor.velocity = pygame.Vector2(50, 10)
        shot = Shot(100, 100)
        with patch("main.log_event"):
            game.update(0)
        self.assertTrue(game.game_over)
        self.assertEqual(game.lives, 0)
        self.assertEqual(game.score, 0)
        self.assertIn(shot, game.shots)
        self.sounds.play.assert_called_once_with("game_over")
        before = survivor.position.copy()
        spawn_timer = game.field.spawn_timer
        with patch.object(game, "draw_game_over") as overlay:
            game.draw()
            overlay.assert_not_called()
            for _ in range(14):
                game.update(0.1)
                game.draw()
            self.assertTrue(game.feedback.death_complete)
            self.assertEqual(len(game.feedback.effects), 0)
            overlay.assert_called_once()
        self.assertEqual(survivor.position, before)
        self.assertEqual(game.field.spawn_timer, spawn_timer)
        self.assertEqual(game.score, 0)
        game.draw()  # renders real persistent overlay
        game.update(10)
        self.assertEqual(game.lives, 0)

    def test_effects_do_not_consume_gameplay_randomness(self):
        player = Player(640, 360)
        asteroid = Asteroid(100, 100, 60)
        before = random.getstate()
        self.feedback.laser_fired(player)
        self.feedback.asteroid_destroyed(asteroid)
        self.feedback.player_damaged(player)
        self.feedback.player_damaged(player, fatal=True)
        self.feedback.update(0.1)
        self.feedback.draw(self.screen)
        self.assertEqual(random.getstate(), before)

    def test_missing_audio_device_is_silent_and_effects_still_finish(self):
        with patch("pygame.mixer.get_init", return_value=None), patch("builtins.print") as diagnostic:
            sounds = SoundManager()
            sounds.play("game_over")
            diagnostic.assert_called_once()
        feedback = FeedbackController(sounds)
        player = Player(640, 360)
        feedback.player_damaged(player, fatal=True)
        feedback.update(1.4)
        self.assertTrue(feedback.death_complete)

    def test_missing_audio_file_is_silent(self):
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)), \
             patch("pygame.mixer.Sound", side_effect=FileNotFoundError("missing")), \
             patch("builtins.print") as diagnostic:
            sounds = SoundManager()
            sounds.play("laser")
            self.assertEqual(sounds.sounds, {})
            diagnostic.assert_called_once()

    def test_wav_assets_are_deterministic_correct_duration_and_unclipped(self):
        for name, duration in DURATIONS.items():
            with self.subTest(name=name), wave.open(str(AUDIO_DIRECTORY / f"{name}.wav")) as file:
                self.assertEqual((file.getnchannels(), file.getsampwidth(), file.getframerate()),
                                 (2, 2, RATE))
                self.assertAlmostEqual(file.getnframes() / RATE, duration, places=3)
                data = file.readframes(file.getnframes())
                self.assertEqual(data, synthesize(name))
                pcm = array("h")
                pcm.frombytes(data)
                if sys.byteorder != "little":
                    pcm.byteswap()
                self.assertGreater(max(abs(value) for value in pcm), 20000)
                self.assertLess(max(abs(value) for value in pcm), 32767)
                self.assertEqual(tuple(pcm[:2]), (0, 0))

    def test_sound_manager_reserves_final_channel_and_stops_other_sounds(self):
        fake_sound = Mock()
        channel = Mock()
        with patch("pygame.mixer.get_init", return_value=(44100, -16, 2)), \
             patch("pygame.mixer.Sound", return_value=fake_sound), \
             patch("pygame.mixer.set_num_channels"), \
             patch("pygame.mixer.set_reserved") as reserve, \
             patch("pygame.mixer.Channel", return_value=channel) as get_channel, \
             patch("pygame.mixer.stop") as stop:
            sounds = SoundManager()
            sounds.play("game_over")
            reserve.assert_called_once_with(2)
            stop.assert_called_once()
            get_channel.assert_called_once_with(0)
            channel.play.assert_called_once_with(fake_sound)

    def test_game_over_main_loop_continues_until_window_close(self):
        frames = 0
        instances = []

        class FatalGame(Game):
            def __init__(self, screen):
                super().__init__(screen, Mock())
                self.lives = 1
                self.field.kill()
                Asteroid(*self.player.position, 20)
                instances.append(self)

        class FixedClock:
            def tick(self, fps):
                return 100

        def flip():
            nonlocal frames
            frames += 1
            if frames == 20:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

        with patch("main.Game", FatalGame), patch("main.log_event"), patch("main.log_state"), \
             patch("pygame.time.Clock", return_value=FixedClock()), \
             patch("pygame.display.flip", side_effect=flip):
            main()
        self.assertEqual(frames, 20)
        self.assertTrue(instances[0].feedback.death_complete)
        self.assertEqual(instances[0].lives, 0)
        # main correctly closes pygame; reinitialize for subsequent test classes.
        pygame.init()
        type(self).screen = pygame.display.set_mode((1280, 720))


if __name__ == "__main__":
    unittest.main()
