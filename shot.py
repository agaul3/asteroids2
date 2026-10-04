import pygame
from constants import SHOT_RADIUS
from circleshape import CircleShape
from visuals import draw_centered, get_sprite

class Shot(CircleShape):
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y, SHOT_RADIUS)

    def draw(self, screen):
        angle = 180
        if self.velocity.length_squared() > 0:
            angle = -pygame.Vector2(0, -1).angle_to(self.velocity)
        size = (round(self.radius * 2), round(self.radius * 4))
        draw_centered(screen, get_sprite("shot", size, angle), self.position)

    def update(self, dt):
        self.position += self.velocity * dt
