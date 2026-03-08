# Tina the Destroyer
# Copyright (c) 2026 Jordi Corbilla.
# All rights reserved.

from __future__ import annotations

import pygame

from settings import (
    PLAYER_MOVE_SPEED,
    PLAYER_SMASH_COOLDOWN,
    PLAYER_SMASH_DURATION,
    RAT_SQUASH_VISIBLE,
    SMASH_HITBOX_HEIGHT,
    SMASH_HITBOX_WIDTH,
)


class Player:
    def __init__(
        self,
        idle_image: pygame.Surface,
        smash_image: pygame.Surface,
        start_x: int,
        floor_y: int,
        screen_width: int,
    ) -> None:
        self.idle_image = idle_image
        self.smash_image = smash_image
        self.screen_width = screen_width
        self.floor_y = floor_y
        self.rect = self.idle_image.get_rect(midbottom=(start_x, floor_y))
        self.smashing = False
        self.smash_end_at = 0.0
        self.next_smash_at = 0.0

    def reset(self, start_x: int) -> None:
        self.rect = self.idle_image.get_rect(midbottom=(start_x, self.floor_y))
        self.smashing = False
        self.smash_end_at = 0.0
        self.next_smash_at = 0.0

    def update(self, dt: float, keys: pygame.key.ScancodeWrapper, now: float) -> None:
        direction = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction += 1

        if direction:
            self.rect.x += int(round(direction * PLAYER_MOVE_SPEED * dt))
            self.rect.left = max(0, self.rect.left)
            self.rect.right = min(self.screen_width, self.rect.right)

        if self.smashing and now >= self.smash_end_at:
            self.smashing = False

    def try_smash(self, now: float) -> bool:
        if now < self.next_smash_at:
            return False
        self.smashing = True
        self.smash_end_at = now + PLAYER_SMASH_DURATION
        self.next_smash_at = now + PLAYER_SMASH_COOLDOWN
        return True

    def get_smash_hitbox(self, screen_height: int) -> pygame.Rect:
        hitbox = pygame.Rect(0, 0, SMASH_HITBOX_WIDTH, SMASH_HITBOX_HEIGHT)
        hitbox.centerx = self.rect.centerx
        hitbox.bottom = min(screen_height - 6, self.rect.bottom + 8)
        return hitbox

    def draw(self, surface: pygame.Surface) -> None:
        image = self.smash_image if self.smashing else self.idle_image
        surface.blit(image, self.rect)


class Rat:
    def __init__(
        self,
        alive_image: pygame.Surface,
        squashed_image: pygame.Surface,
        x: int,
        y: int,
        speed: float,
    ) -> None:
        self.alive_image = alive_image
        self.squashed_image = squashed_image
        self.rect = self.alive_image.get_rect(midtop=(x, y))
        self.y = float(self.rect.y)
        self.speed = speed
        self.squashed = False
        self.remove_at = 0.0

    def squash(self, now: float) -> bool:
        if self.squashed:
            return False
        self.squashed = True
        preserved_bottom = self.rect.bottom
        self.rect = self.squashed_image.get_rect(center=self.rect.center)
        self.rect.bottom = preserved_bottom
        self.y = float(self.rect.y)
        self.remove_at = now + RAT_SQUASH_VISIBLE
        return True

    def update(self, dt: float, now: float, bottom_limit: int) -> str | None:
        if self.squashed:
            if now >= self.remove_at:
                return "remove"
            return None

        self.y += self.speed * dt
        self.rect.y = int(round(self.y))
        if self.rect.top >= bottom_limit:
            return "missed"
        return None

    def draw(self, surface: pygame.Surface) -> None:
        if not self.squashed:
            shadow_rect = pygame.Rect(0, 0, max(8, self.rect.width - 18), 9)
            shadow_rect.midtop = (self.rect.centerx, self.rect.bottom - 5)
            pygame.draw.ellipse(surface, (0, 0, 0, 50), shadow_rect)
            surface.blit(self.alive_image, self.rect)
            return
        surface.blit(self.squashed_image, self.rect)


class ImpactEffect:
    def __init__(
        self,
        image: pygame.Surface,
        center_x: int,
        bottom_y: int,
        start_time: float,
        duration: float,
    ) -> None:
        self.image = image
        self.rect = self.image.get_rect(midbottom=(center_x, bottom_y))
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration

    def is_alive(self, now: float) -> bool:
        return now < self.end_time

    def draw(self, surface: pygame.Surface, now: float) -> None:
        age = now - self.start_time
        ratio = max(0.0, min(1.0, age / self.duration if self.duration > 0 else 1.0))
        alpha = int(255 * (1.0 - ratio))
        image = self.image.copy()
        image.set_alpha(alpha)
        surface.blit(image, self.rect)
