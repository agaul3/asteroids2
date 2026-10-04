import pygame

from asteroid import Asteroid
from asteroidfield import AsteroidField
from audio import SoundManager
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from feedback import FeedbackController
from logger import log_event, log_state
from player import Player
from shot import Shot


class Game:
    """Playable world plus a persistent, responsive game-over state."""

    def __init__(self, screen, sounds=None):
        self.screen = screen
        self.score = 0
        self.lives = 3
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        self.title_font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 78, bold=True)
        self.label_font = pygame.font.SysFont("menlo,dejavusansmono,consolas", 22)
        self.shots = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.feedback = FeedbackController(sounds if sounds is not None else SoundManager())

        Shot.containers = (self.shots, self.updatable, self.drawable)
        AsteroidField.containers = (self.updatable,)
        Asteroid.containers = (self.asteroids, self.updatable, self.drawable)
        self.field = AsteroidField()
        Player.containers = (self.updatable, self.drawable)
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, self.feedback)
        self.overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.overlay.fill((4, 7, 17, 215))

    def update(self, dt):
        # Existing effects advance first; new impacts start at age zero this frame.
        self.feedback.update(dt)
        if self.game_over:
            return
        self.updatable.update(dt)

        for asteroid in self.asteroids:
            if self.player.collides_with(asteroid):
                log_event("player_hit")
                self.lives -= 1
                self.feedback.asteroid_destroyed(asteroid, cause="collision")
                asteroid.kill()
                fatal = self.lives == 0
                self.feedback.player_damaged(self.player, fatal=fatal)
                if fatal:
                    self.game_over = True
                    log_event("game_over")
                    # No further collision, scoring, or firing work after death.
                    return

        for shot in self.shots:
            for asteroid in self.asteroids:
                if shot.collides_with(asteroid):
                    log_event("asteroid_shot")
                    self.feedback.asteroid_destroyed(asteroid)
                    shot.kill()
                    asteroid.split()
                    self.score += 1
                    break

    def draw(self):
        self.screen.fill("black")
        for entity in self.drawable:
            entity.draw(self.screen)
        self.feedback.draw(self.screen)
        self.screen.blit(self.font.render(f"Score: {self.score}", True, "white"), (10, 10))
        self.screen.blit(self.font.render(f"Lives: {self.lives}", True, "white"), (10, 45))
        if self.game_over and self.feedback.death_complete:
            self.draw_game_over()

    def draw_game_over(self):
        self.screen.blit(self.overlay, (0, 0))
        width, height = self.screen.get_size()
        center = pygame.Vector2(width / 2, height / 2)
        pygame.draw.line(self.screen, (255, 45, 167),
                         (width // 2 - 255, height // 2 - 92),
                         (width // 2 + 255, height // 2 - 92), 2)
        for label, font, color, offset in (
            ("FLATLINED", self.title_font, (255, 45, 167), -28),
            (f"FINAL SCORE // {self.score:04d}", self.label_font, (55, 230, 255), 42),
            ("CLOSE THE WINDOW TO EXIT", self.label_font, (160, 179, 195), 87),
        ):
            image = font.render(label, True, color)
            self.screen.blit(image, image.get_rect(center=(round(center.x), round(center.y + offset))))


def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cyberpunk Asteroids")
        clock = pygame.time.Clock()
        game = Game(screen)
        # Keep the logger's existing group snapshots available in this frame.
        shots, asteroids = game.shots, game.asteroids
        updatable, drawable = game.updatable, game.drawable
        while True:
            dt = clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
            game.update(dt)
            score, lives = game.score, game.lives
            log_state()
            game.draw()
            pygame.display.flip()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
