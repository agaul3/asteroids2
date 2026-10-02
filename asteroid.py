import pygame
import random
from logger import log_event
from circleshape import CircleShape
from constants import LINE_WIDTH
from constants import ASTEROID_MIN_RADIUS

class Asteroid(CircleShape):
    def __init__(self, x: float, y: float, radius: float) -> None:
        super().__init__(x, y, radius)

        self.points = []

        for angle in range(0, 360, 36):
            distance = random.uniform(self.radius * 0.75, self.radius)
            point = pygame.Vector2(distance, 0).rotate(angle)
            self.points.append(point)

    def draw(self, screen):
        asteroid_points = []


        for point in self.points:
            asteroid_points.append(self.position + point)

        pygame.draw.polygon(screen, "white", asteroid_points, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt
        
    def split(self):
        self.kill()
        if self.radius <= ASTEROID_MIN_RADIUS:
            return
        else:
            log_event("asteroid_split")
            random_angle = random.uniform(20, 50)
            rotated_angle_1 = self.velocity.rotate(random_angle)
            rotated_angle_2 = self.velocity.rotate(-random_angle)
            new_radius = self.radius - ASTEROID_MIN_RADIUS
            asteroid_2 = Asteroid(self.position.x, self.position.y, new_radius)
            asteroid_3 = Asteroid(self.position.x, self.position.y, new_radius)
            asteroid_2.velocity = rotated_angle_1 * 1.2
            asteroid_3.velocity = rotated_angle_2 * 1.2
