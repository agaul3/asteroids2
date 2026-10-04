"""Live animation/SFX reel, or a reproducible headless contact sheet."""

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headless", action="store_true", help="Save assets/combat-preview.png without audio.")
    args = parser.parse_args()
    if args.headless:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    import pygame
    from asteroid import Asteroid
    from audio import SoundManager
    from effects import CYAN, MAGENTA, YELLOW, effect_random
    from feedback import FeedbackController
    from player import Player
    from visuals import get_sprite, visual_random

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    cases = (
        ("laser", "LASER // MUZZLE FLASH", 0.12),
        ("mineral", "MINERAL // CYAN NOVA", 0.55),
        ("scrap", "SALVAGE // GOLD NOVA", 0.55),
        ("crystal", "CRYSTAL // MAGENTA NOVA", 0.55),
        ("damage", "DAMAGE // SHIELD RUPTURE", 0.55),
        ("fatal", "FATAL // POWER COLLAPSE", 1.4),
    )

    class Silent:
        def play(self, event):
            pass

    def scene(name, position, sounds):
        # Fixed cosmetics make the exported sequence reproducible.
        effect_random.seed(2077)
        visual_random.seed(2077)
        feedback = FeedbackController(sounds)
        player = Player(*position, feedback)
        player.rotation = 180
        if name == "laser":
            player.shoot()
        elif name == "damage":
            feedback.player_damaged(player)
        elif name == "fatal":
            feedback.player_damaged(player, fatal=True)
        else:
            asteroid = Asteroid(*position, 40)
            asteroid.visual_variant = f"asteroid-{name}"
            asteroid.image = get_sprite(asteroid.visual_variant, (80, 80))
            feedback.asteroid_destroyed(asteroid)
        return feedback, player

    try:
        if args.headless:
            screen = pygame.display.set_mode((1320, 1120))
            screen.fill((8, 12, 20))
            title_font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 30, bold=True)
            font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 15)
            screen.blit(title_font.render("CYBERPUNK // COMBAT ANIMATION REEL", True, YELLOW), (30, 20))
            screen.blit(font.render("Actual gameplay scale / original sprite fragments / time-based VFX", True, CYAN), (30, 62))
            for row, (name, title, duration) in enumerate(cases):
                y = 110 + row * 165
                screen.blit(font.render(title.split(" // ")[0], True, CYAN), (24, y + 30))
                screen.blit(font.render(f"{duration:.2f}s", True, (155, 174, 191)), (24, y + 55))
                for column, progress in enumerate((0, 0.12, 0.35, 0.65, 0.95)):
                    x = 160 + column * 230
                    cell = pygame.Surface((220, 145))
                    cell.fill((12, 19, 30))
                    pygame.draw.rect(cell, (35, 60, 75), cell.get_rect(), 1)
                    feedback, player = scene(name, (110, 70), Silent())
                    feedback.update(duration * progress)
                    if name in ("laser", "damage", "fatal"):
                        player.draw(cell)
                    feedback.draw(cell)
                    screen.blit(cell, (x, y))
                    screen.blit(font.render(f"{duration * progress:.3f}s", True, (155, 174, 191)), (x + 6, y + 145))
            destination = ROOT / "assets" / "combat-preview.png"
            pygame.image.save(screen, str(destination))
            print(destination)
            from main import Game
            ending = pygame.Surface((1280, 720))
            game = Game(ending, Silent())
            game.game_over = True
            game.lives = 0
            game.feedback.player_damaged(game.player, fatal=True)
            game.feedback.update(1.4)
            game.draw()
            ending_path = ROOT / "assets" / "game-over-preview.png"
            pygame.image.save(ending, str(ending_path))
            print(ending_path)
            return

        screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Cyberpunk Combat // Animation + Audio Preview")
        title_font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 34, bold=True)
        font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 22)
        sounds = SoundManager()
        clock = pygame.time.Clock()
        index, elapsed = 0, 0.0
        feedback, player = scene(cases[index][0], (640, 350), sounds)
        while True:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
            elapsed += dt
            feedback.update(dt)
            name, title, duration = cases[index]
            if elapsed > duration + 1.1:
                index = (index + 1) % len(cases)
                elapsed = 0.0
                feedback, player = scene(cases[index][0], (640, 350), sounds)
                name, title, duration = cases[index]
            screen.fill((8, 12, 20))
            screen.blit(title_font.render(title, True, YELLOW), (40, 40))
            screen.blit(font.render("Actual game scale  //  ESC or close to exit", True, CYAN), (40, 95))
            if name in ("laser", "damage", "fatal"):
                # Live attachment demo: rotate and drift while shield is active.
                if name == "damage":
                    player.rotation = 180 + elapsed * 40
                    player.position.x = 640 + min(elapsed, duration) * 100
                player.draw(screen)
            feedback.draw(screen)
            screen.blit(font.render(f"{min(elapsed, duration):.2f}s / {duration:.2f}s", True, MAGENTA), (40, 625))
            pygame.draw.rect(screen, (35, 60, 75), (40, 670, 1200, 4))
            pygame.draw.rect(screen, CYAN, (40, 670, round(1200 * min(elapsed / duration, 1)), 4))
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
