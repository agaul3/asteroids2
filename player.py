import pygame
from circleshape import CircleShape
from constants import PLAYER_RADIUS, LINE_WIDTH, PLAYER_TURN_SPEED, PLAYER_SPEED, PLAYER_SHOOT_SPEED, PLAYER_SHOOT_COOLDOWN_SECONDS
from shot import Shot

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.cooldown_timer = 0

    # in the Player class
    def triangle(self) -> list[pygame.Vector2]:
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def point_in_triangle(self, point, triangle):
        a, b, c = triangle

        def sign(p1, p2, p3):
            return (
                (p1.x - p3.x) * (p2.y - p3.y)
                - (p2.x - p3.x) * (p1.y - p3.y)
            )

        side_1 = sign(point, a, b) < 0
        side_2 = sign(point, b, c) < 0
        side_3 = sign(point, c, a) < 0

        return side_1 == side_2 == side_3

    def distance_to_line(self, point, start, end):
        line = end - start

        if line.length_squared() == 0:
            return point.distance_to(start)

        t = (point - start).dot(line) / line.length_squared()
        t = max(0, min(1, t))

        closest_point = start + line * t

        return point.distance_to(closest_point)

    def collides_with(self, other):
        triangle = self.triangle()

        # Check if the center of the asteroid is inside the triangle
        if self.point_in_triangle(other.position, triangle):
            return True

        # Check if the asteroid touches any edge of the triangle
        for i in range(3):
            start = triangle[i]
            end = triangle[(i + 1) % 3]

            distance = self.distance_to_line(other.position, start, end)

            if distance <= other.radius:
                return True

        return False

    def draw(self, screen):
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def update(self, dt: float) -> None:
        self.cooldown_timer -= dt
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_a]:
            self.rotate(-dt)

        if keys[pygame.K_d]:
            self.rotate(dt)

        if keys[pygame.K_w]:
            self.move(dt)

        if keys[pygame.K_s]:
            self.move(-dt)

        if keys[pygame.K_SPACE]:
            self.shoot()

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def shoot(self):
        if self.cooldown_timer > 0:
            return
        self.cooldown_timer = PLAYER_SHOOT_COOLDOWN_SECONDS
        shot = Shot(self.position.x, self.position.y)
        direction = pygame.Vector2(0, 1)
        direction = direction.rotate(self.rotation)
        shot.velocity = direction * PLAYER_SHOOT_SPEED        
