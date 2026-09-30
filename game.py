import pygame
import random
import math
import time

pygame.init()

WIDTH, HEIGHT = 800, 560
FPS = 60
BG = (18, 18, 22)

# -----------------------------
# Zombie Types
# -----------------------------

class Zombie:
    SPEED = 1.5
    MAX_HP = 3
    SIZE = 30
    COLOR = (80, 200, 80)

    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, self.SIZE, self.SIZE)
        self.hp = self.MAX_HP

    def update(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist > 0:
            self.rect.x += int(self.SPEED * dx / dist)
            self.rect.y += int(self.SPEED * dy / dist)

    def hit(self):
        self.hp -= 1
        return self.hp <= 0

    def draw(self, screen):
        pygame.draw.rect(screen, self.COLOR, self.rect)


class FastZombie(Zombie):
    SPEED = 3.0
    MAX_HP = 1
    SIZE = 20
    COLOR = (80, 180, 255)


class TankZombie(Zombie):
    SPEED = 0.8
    MAX_HP = 6
    SIZE = 44
    COLOR = (180, 80, 180)


def spawn_zombie(zombie_type="standard"):
    side = random.choice(["top", "bottom", "left", "right"])

    if side == "top":
        x = random.randint(0, WIDTH - 30)
        y = -40
    elif side == "bottom":
        x = random.randint(0, WIDTH - 30)
        y = HEIGHT + 40
    elif side == "left":
        x = -40
        y = random.randint(0, HEIGHT - 30)
    else:
        x = WIDTH + 40
        y = random.randint(0, HEIGHT - 30)

    if zombie_type == "fast":
        return FastZombie(x, y)

    if zombie_type == "tank":
        return TankZombie(x, y)

    return Zombie(x, y)


# -----------------------------
# Explosive Barrel
# -----------------------------

class Barrel:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 36)
        self.color = (170, 100, 35)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        pygame.draw.rect(
            screen,
            (90, 50, 20),
            (self.rect.x, self.rect.y + 7, self.rect.width, 4)
        )
        pygame.draw.rect(
            screen,
            (90, 50, 20),
            (self.rect.x, self.rect.y + 25, self.rect.width, 4)
        )


# -----------------------------
# Player
# -----------------------------

class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, 32, 32)

        # Task 1 - Health
        self.max_hp = 3
        self.hp = 3
        self.invincibility_timer = 0
        self.invincibility_duration = 90

        # Task 2 - Ammo
        self.max_ammo = 12
        self.ammo = 12
        self.reload_duration = 2000
        self.reload_timer = 0

        self.bullets = []
        self.shoot_cooldown = 0

    def move(self, keys):
        speed = 4

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.rect.y -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.rect.y += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.rect.x -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.rect.x += speed

        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        if self.invincibility_timer > 0:
            self.invincibility_timer -= 1

        if self.reload_timer > 0:
            self.reload_timer -= 1000 / FPS

            if self.reload_timer <= 0:
                self.reload_timer = 0
                self.ammo = self.max_ammo

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def take_damage(self):
        if self.invincibility_timer > 0:
            return False

        self.hp -= 1
        self.invincibility_timer = self.invincibility_duration

        return self.hp <= 0

    def shoot(self, target_pos):
        if self.shoot_cooldown > 0:
            return

        if self.reload_timer > 0:
            return

        if self.ammo <= 0:
            return

        dx = target_pos[0] - self.rect.centerx
        dy = target_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist == 0:
            return

        speed = 10
        vx = speed * dx / dist
        vy = speed * dy / dist

        self.bullets.append([
            float(self.rect.centerx),
            float(self.rect.centery),
            vx,
            vy
        ])

        self.ammo -= 1
        self.shoot_cooldown = 15

        if self.ammo == 0:
            self.reload_timer = self.reload_duration

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet[0] += bullet[2]
            bullet[1] += bullet[3]

            if (
                bullet[0] < 0
                or bullet[0] > WIDTH
                or bullet[1] < 0
                or bullet[1] > HEIGHT
            ):
                self.bullets.remove(bullet)

    def draw(self, screen):
        if self.invincibility_timer > 0:
            if (self.invincibility_timer // 5) % 2 == 0:
                return

        pygame.draw.rect(screen, (70, 150, 255), self.rect)

        for bullet in self.bullets:
            pygame.draw.circle(
                screen,
                (255, 230, 80),
                (int(bullet[0]), int(bullet[1])),
                4
            )


# -----------------------------
# Game Engine
# -----------------------------

class GameEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player = Player()

        self.zombies = []

        
   # Initial mixed zombies
        self.zombies.append(spawn_zombie("standard"))
        self.zombies.append(spawn_zombie("fast"))
        self.zombies.append(spawn_zombie("tank"))
        self.zombies.append(spawn_zombie("standard")) 
        self.barrels = [
            Barrel(120, 120),
            Barrel(650, 120),
            Barrel(120, 400),
            Barrel(650, 400)
        ]

        self.score = 0
        self.wave = 1
        self.kills = 0
        self.kills_to_next = 8
        self.game_over = False

        self.start_time = time.time()

    def explode_barrel(self, barrel):
        explosion_radius = 100
        center = barrel.rect.center

        destroyed = []

        for zombie in self.zombies:
            distance = math.hypot(
                zombie.rect.centerx - center[0],
                zombie.rect.centery - center[1]
            )

            if distance <= explosion_radius:
                destroyed.append(zombie)

        for zombie in destroyed:
            self.zombies.remove(zombie)
            self.kills += 1
            self.score += 10

        self.barrels.remove(barrel)

    def update(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys)
        self.player.update_bullets()

        # Zombie movement and player collision
        for zombie in self.zombies:
            zombie.update(self.player)

            if zombie.rect.colliderect(self.player.rect):
                if self.player.take_damage():
                    self.game_over = True
                    return

        # Barrel collision
        exploded_barrel = None

        for bullet in self.player.bullets[:]:
            bx, by = bullet[0], bullet[1]

            for barrel in self.barrels:
                if barrel.rect.collidepoint(bx, by):
                    exploded_barrel = barrel

                    if bullet in self.player.bullets:
                        self.player.bullets.remove(bullet)

                    break

            if exploded_barrel:
                break

        if exploded_barrel:
            self.explode_barrel(exploded_barrel)

        # Normal zombie bullet collision
        for bullet in self.player.bullets[:]:
            bx, by = bullet[0], bullet[1]

            hit_zombie = None

            for zombie in self.zombies:
                if zombie.rect.collidepoint(bx, by):
                    hit_zombie = zombie
                    break

            if hit_zombie:
                if bullet in self.player.bullets:
                    self.player.bullets.remove(bullet)

                if hit_zombie.hit():
                    self.zombies.remove(hit_zombie)
                    self.kills += 1
                    self.score += 5

        # Wave progression
        if self.kills >= self.kills_to_next:
            self.wave += 1
            self.kills = 0
            self.kills_to_next = 8 + self.wave * 2

            # Mix all zombie types into the new wave
            for _ in range(self.wave + 3):
                zombie_type = random.choice([
                    "standard",
                    "fast",
                    "tank"
                ])

                self.zombies.append(
                    spawn_zombie(zombie_type)
                )

    def draw(self, screen):
        screen.fill(BG)

        # Grid
        for x in range(0, WIDTH, 40):
            pygame.draw.line(
                screen,
                (30, 30, 36),
                (x, 0),
                (x, HEIGHT)
            )

        for y in range(0, HEIGHT, 40):
            pygame.draw.line(
                screen,
                (30, 30, 36),
                (0, y),
                (WIDTH, y)
            )

        for barrel in self.barrels:
            barrel.draw(screen)

        for zombie in self.zombies:
            zombie.draw(screen)

        self.player.draw(screen)

        font = pygame.font.SysFont(None, 26)

        hp_text = font.render(
            f"HP: {self.player.hp}/{self.player.max_hp}",
            True,
            (240, 240, 240)
        )

        if self.player.reload_timer > 0:
            ammo_text = font.render(
                f"RELOADING: {self.player.reload_timer / 1000:.1f}s",
                True,
                (255, 220, 100)
            )
        else:
            ammo_text = font.render(
                f"Ammo: {self.player.ammo}/{self.player.max_ammo}",
                True,
                (240, 240, 240)
            )

        wave_text = font.render(
            f"Wave: {self.wave}",
            True,
            (240, 240, 240)
        )

        score_text = font.render(
            f"Score: {self.score}",
            True,
            (240, 240, 240)
        )

        kills_text = font.render(
            f"Kills: {self.kills}/{self.kills_to_next}",
            True,
            (240, 240, 240)
        )

        screen.blit(hp_text, (10, 10))
        screen.blit(ammo_text, (10, 38))
        screen.blit(wave_text, (10, 66))
        screen.blit(score_text, (10, 94))
        screen.blit(kills_text, (10, 122))

        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            big_font = pygame.font.SysFont(None, 64)
            small_font = pygame.font.SysFont(None, 30)

            game_over_text = big_font.render(
                "DEVOURED!",
                True,
                (255, 80, 80)
            )

            restart_text = small_font.render(
                "Press R to restart",
                True,
                (240, 240, 240)
            )

            screen.blit(
                game_over_text,
                (
                    WIDTH // 2 - game_over_text.get_width() // 2,
                    HEIGHT // 2 - 50
                )
            )

            screen.blit(
                restart_text,
                (
                    WIDTH // 2 - restart_text.get_width() // 2,
                    HEIGHT // 2 + 20
                )
            )


def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Zombie Escape")

    clock = pygame.time.Clock()
    game = GameEngine()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    game.player.shoot(event.pos)

        game.update()
        game.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()