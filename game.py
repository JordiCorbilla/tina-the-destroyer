# Tina the Destroyer
# Copyright (c) 2026 Jordi Corbilla.
# All rights reserved.

from __future__ import annotations

import random
import time
from typing import Optional

import pygame

from entities import ImpactEffect, Player, Rat
from settings import (
    ACCENT_COLOR,
    ASSETS_DIR,
    BEST_SCORE_PATH,
    BG_COLOR_BOTTOM,
    BG_COLOR_TOP,
    DIFFICULTY_RAMP_SECONDS,
    FPS,
    GROUND_COLOR,
    GROUND_HEIGHT,
    GROUND_TOP_COLOR,
    HUD_TEXT_COLOR,
    IMPACT_DURATION,
    IMPACT_TARGET_HEIGHT,
    PLAYER_FLOOR_Y,
    PLAYER_TARGET_HEIGHT,
    RAT_BASE_SPEED,
    RAT_MAX_SPEED,
    RAT_SPEED_MULTIPLIER,
    RAT_SPEED_VARIANCE,
    RAT_TARGET_HEIGHT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SPAWN_INTERVAL_END,
    SPAWN_INTERVAL_START,
    START_LIVES,
    STATE_GAME_OVER,
    STATE_PLAYING,
    STATE_QUITTING,
    STATE_TITLE,
    WINDOW_TITLE,
)
from utils import (
    clamp,
    find_existing_path,
    lerp,
    load_best_score,
    load_scaled_image,
    load_sound,
    make_impact_placeholder,
    make_player_idle_placeholder,
    make_player_smash_placeholder,
    make_rat_placeholder,
    make_rat_squashed_placeholder,
    safe_init_mixer,
    safe_load_image,
    save_best_score,
    scale_to_fit,
)


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.mixer_ready = safe_init_mixer()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.rng = random.Random()

        self.font_small = pygame.font.Font(None, 30)
        self.font_medium = pygame.font.Font(None, 42)
        self.font_large = pygame.font.Font(None, 88)

        self.background = self._build_background()
        self.world_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.title_image: Optional[pygame.Surface] = None
        self.player_idle_image: pygame.Surface
        self.player_smash_image: pygame.Surface
        self.rat_image: pygame.Surface
        self.rat_squashed_image: pygame.Surface
        self.impact_image: pygame.Surface
        self.smash_sound: Optional[pygame.mixer.Sound] = None
        self.miss_sound: Optional[pygame.mixer.Sound] = None
        self.game_over_sound: Optional[pygame.mixer.Sound] = None
        self._load_assets()

        self.best_score = load_best_score(BEST_SCORE_PATH)
        self.score = 0
        self.lives = START_LIVES
        self.elapsed = 0.0
        self.next_spawn_at = 0.0
        self.rats: list[Rat] = []
        self.impact_effects: list[ImpactEffect] = []

        self.state = STATE_TITLE
        self.running = True

        self.shake_time = 0.0
        self.shake_strength = 0.0

        self.player = Player(
            self.player_idle_image,
            self.player_smash_image,
            start_x=SCREEN_WIDTH // 2,
            floor_y=PLAYER_FLOOR_Y,
            screen_width=SCREEN_WIDTH,
        )

    def _build_background(self) -> pygame.Surface:
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / float(SCREEN_HEIGHT)
            color = (
                int(lerp(BG_COLOR_TOP[0], BG_COLOR_BOTTOM[0], t)),
                int(lerp(BG_COLOR_TOP[1], BG_COLOR_BOTTOM[1], t)),
                int(lerp(BG_COLOR_TOP[2], BG_COLOR_BOTTOM[2], t)),
            )
            pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))

        ground_top = SCREEN_HEIGHT - GROUND_HEIGHT
        pygame.draw.rect(surface, GROUND_COLOR, (0, ground_top, SCREEN_WIDTH, GROUND_HEIGHT))
        pygame.draw.rect(surface, GROUND_TOP_COLOR, (0, ground_top - 6, SCREEN_WIDTH, 8))
        return surface

    def _load_assets(self) -> None:
        self.player_idle_image = load_scaled_image(
            [ASSETS_DIR / "player_idle.png"],
            make_player_idle_placeholder,
            PLAYER_TARGET_HEIGHT,
        )
        self.player_smash_image = load_scaled_image(
            [ASSETS_DIR / "player_smash.png"],
            make_player_smash_placeholder,
            PLAYER_TARGET_HEIGHT,
        )
        self.rat_image = load_scaled_image(
            [ASSETS_DIR / "rat.png"],
            make_rat_placeholder,
            RAT_TARGET_HEIGHT,
        )
        self.rat_squashed_image = load_scaled_image(
            [ASSETS_DIR / "rat_squashed.png"],
            make_rat_squashed_placeholder,
            max(12, int(RAT_TARGET_HEIGHT * 0.5)),
        )
        self.impact_image = load_scaled_image(
            [ASSETS_DIR / "impact.png"],
            make_impact_placeholder,
            IMPACT_TARGET_HEIGHT,
        )

        title_raw = safe_load_image(ASSETS_DIR / "title.png")
        if title_raw is not None:
            self.title_image = scale_to_fit(
                title_raw,
                int(SCREEN_WIDTH * 0.82),
                int(SCREEN_HEIGHT * 0.48),
            )

        self.smash_sound = load_sound(
            [ASSETS_DIR / "smash.wav", ASSETS_DIR / "punch.mp3", ASSETS_DIR / "smash.mp3"],
            self.mixer_ready,
        )
        self.miss_sound = load_sound(
            [ASSETS_DIR / "miss.wav", ASSETS_DIR / "miss.mp3"],
            self.mixer_ready,
        )
        self.game_over_sound = load_sound(
            [ASSETS_DIR / "game_over.wav", ASSETS_DIR / "game_over.mp3", ASSETS_DIR / "miss.mp3"],
            self.mixer_ready,
        )

        if self.smash_sound is not None:
            self.smash_sound.set_volume(0.55)
        if self.miss_sound is not None:
            self.miss_sound.set_volume(0.60)
        if self.game_over_sound is not None:
            self.game_over_sound.set_volume(0.65)

        self._try_start_music()

    def _try_start_music(self) -> None:
        if not self.mixer_ready:
            return
        music_path = find_existing_path(
            [ASSETS_DIR / "music_loop.mp3", ASSETS_DIR / "musinc_loop.mp3"]
        )
        if music_path is None:
            return
        try:
            pygame.mixer.music.load(str(music_path))
            pygame.mixer.music.set_volume(0.35)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass

    def _play_sound(self, sound: Optional[pygame.mixer.Sound]) -> None:
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass

    def _difficulty_progress(self) -> float:
        time_factor = clamp(self.elapsed / DIFFICULTY_RAMP_SECONDS, 0.0, 1.0)
        score_factor = clamp(self.score / 220.0, 0.0, 0.4)
        return clamp(time_factor + score_factor, 0.0, 1.0)

    def _current_rat_speed(self) -> float:
        return lerp(RAT_BASE_SPEED, RAT_MAX_SPEED, self._difficulty_progress()) * RAT_SPEED_MULTIPLIER

    def _current_spawn_interval(self) -> float:
        return lerp(SPAWN_INTERVAL_START, SPAWN_INTERVAL_END, self._difficulty_progress())

    def _start_gameplay(self) -> None:
        self.score = 0
        self.lives = START_LIVES
        self.elapsed = 0.0
        self.rats.clear()
        self.impact_effects.clear()
        self.player.reset(SCREEN_WIDTH // 2)
        self.next_spawn_at = time.perf_counter() + 0.65
        self.shake_time = 0.0
        self.shake_strength = 0.0
        self.state = STATE_PLAYING

    def _trigger_game_over(self) -> None:
        if self.state == STATE_GAME_OVER:
            return
        self.state = STATE_GAME_OVER
        self.impact_effects.clear()
        if self.score > self.best_score:
            self.best_score = self.score
            save_best_score(BEST_SCORE_PATH, self.best_score)
        self._play_sound(self.game_over_sound)

    def _spawn_rat(self) -> None:
        base_speed = self._current_rat_speed()
        variation = self.rng.uniform(1.0 - RAT_SPEED_VARIANCE, 1.0 + RAT_SPEED_VARIANCE)
        speed = base_speed * variation
        half_width = max(16, self.rat_image.get_width() // 2)
        x = self.rng.randint(half_width, SCREEN_WIDTH - half_width)
        y = -self.rng.randint(20, 140)
        self.rats.append(Rat(self.rat_image, self.rat_squashed_image, x=x, y=y, speed=speed))

    def _attempt_smash(self, now: float) -> None:
        if not self.player.try_smash(now):
            return
        self._play_sound(self.smash_sound)
        self.impact_effects.append(
            ImpactEffect(
                self.impact_image,
                center_x=self.player.rect.centerx,
                bottom_y=SCREEN_HEIGHT - 8,
                start_time=now,
                duration=IMPACT_DURATION,
            )
        )
        self._start_shake(duration=0.08, strength=7.0)

    def _start_shake(self, duration: float, strength: float) -> None:
        self.shake_time = max(self.shake_time, duration)
        self.shake_strength = max(self.shake_strength, strength)

    def _update_shake(self, dt: float) -> None:
        if self.shake_time <= 0.0:
            self.shake_strength = 0.0
            return
        self.shake_time -= dt
        self.shake_strength *= 0.92
        if self.shake_time <= 0.0:
            self.shake_strength = 0.0

    def _get_shake_offset(self) -> tuple[int, int]:
        if self.shake_strength <= 0.0:
            return 0, 0
        strength = max(1, int(round(self.shake_strength)))
        return self.rng.randint(-strength, strength), self.rng.randint(-strength, strength)

    def run(self) -> None:
        while self.running and self.state != STATE_QUITTING:
            dt = self.clock.tick(FPS) / 1000.0
            now = time.perf_counter()

            self._handle_events(now)
            self._update(dt, now)
            self._draw(now)
            pygame.display.flip()

        pygame.quit()

    def _handle_events(self, now: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = STATE_QUITTING
                self.running = False
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if self.state == STATE_TITLE:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_QUITTING
                    self.running = False
                else:
                    self._start_gameplay()
                continue

            if self.state == STATE_PLAYING:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_QUITTING
                    self.running = False
                elif event.key == pygame.K_r:
                    self._start_gameplay()
                elif event.key == pygame.K_SPACE:
                    self._attempt_smash(now)
                continue

            if self.state == STATE_GAME_OVER:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_QUITTING
                    self.running = False
                elif event.key in (pygame.K_r, pygame.K_RETURN):
                    self._start_gameplay()

    def _update(self, dt: float, now: float) -> None:
        self._update_shake(dt)
        if self.state != STATE_PLAYING:
            return

        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, now)
        self.elapsed += dt

        if now >= self.next_spawn_at:
            self._spawn_rat()
            self.next_spawn_at = now + self._current_spawn_interval()

        smash_hitbox = self.player.get_smash_hitbox(SCREEN_HEIGHT) if self.player.smashing else None
        remaining_rats: list[Rat] = []
        for rat in self.rats:
            status = rat.update(dt, now, SCREEN_HEIGHT)
            if status == "missed":
                self.lives -= 1
                self._play_sound(self.miss_sound)
                self._start_shake(duration=0.10, strength=9.0)
                if self.lives <= 0:
                    self._trigger_game_over()
                continue

            if smash_hitbox is not None and not rat.squashed and rat.rect.colliderect(smash_hitbox):
                if rat.squash(now):
                    self.score += 1
                status = None

            if status == "remove":
                continue
            remaining_rats.append(rat)
        self.rats = remaining_rats

        self.impact_effects = [effect for effect in self.impact_effects if effect.is_alive(now)]

    def _draw(self, now: float) -> None:
        if self.state == STATE_TITLE:
            self._draw_title()
            return
        if self.state == STATE_GAME_OVER:
            self._draw_game_over()
            return
        if self.state == STATE_PLAYING:
            self._draw_playing(now)
            return

        self.screen.fill((0, 0, 0))

    def _draw_title(self) -> None:
        self.screen.blit(self.background, (0, 0))

        if self.title_image is not None:
            title_rect = self.title_image.get_rect(midtop=(SCREEN_WIDTH // 2, 60))
            self.screen.blit(self.title_image, title_rect)
        else:
            title_text = self.font_large.render("Tina the Destroyer", True, ACCENT_COLOR)
            title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 140))
            self.screen.blit(title_text, title_rect)

        prompt = self.font_medium.render("Press any key to start", True, HUD_TEXT_COLOR)
        self.screen.blit(prompt, prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 220)))

        controls = [
            "Move: A/D or Left/Right",
            "Smash: Space",
            "Restart: R",
            "Quit: Esc",
        ]
        y = SCREEN_HEIGHT - 176
        for line in controls:
            text = self.font_small.render(line, True, HUD_TEXT_COLOR)
            self.screen.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, y)))
            y += 28

        quit_text = self.font_small.render("Esc to quit", True, ACCENT_COLOR)
        self.screen.blit(quit_text, quit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 42)))

    def _draw_game_over(self) -> None:
        self.screen.blit(self.background, (0, 0))
        self._draw_playfield_overlay()

        game_over = self.font_large.render("Game Over", True, ACCENT_COLOR)
        self.screen.blit(game_over, game_over.get_rect(center=(SCREEN_WIDTH // 2, 170)))

        score_text = self.font_medium.render(f"Final Score: {self.score}", True, HUD_TEXT_COLOR)
        best_text = self.font_medium.render(f"Best Score: {self.best_score}", True, HUD_TEXT_COLOR)
        self.screen.blit(score_text, score_text.get_rect(center=(SCREEN_WIDTH // 2, 255)))
        self.screen.blit(best_text, best_text.get_rect(center=(SCREEN_WIDTH // 2, 300)))

        restart_text = self.font_small.render("Press R or Enter to restart", True, HUD_TEXT_COLOR)
        quit_text = self.font_small.render("Press Esc to quit", True, HUD_TEXT_COLOR)
        self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, 372)))
        self.screen.blit(quit_text, quit_text.get_rect(center=(SCREEN_WIDTH // 2, 404)))

    def _draw_playing(self, now: float) -> None:
        self.world_surface.blit(self.background, (0, 0))

        self.player.draw(self.world_surface)

        for rat in self.rats:
            rat.draw(self.world_surface)

        for effect in self.impact_effects:
            effect.draw(self.world_surface, now)

        offset_x, offset_y = self._get_shake_offset()
        self.screen.fill((0, 0, 0))
        self.screen.blit(self.world_surface, (offset_x, offset_y))
        self._draw_hud()

    def _draw_playfield_overlay(self) -> None:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

    def _draw_hud(self) -> None:
        score_text = self.font_small.render(f"Score: {self.score}", True, HUD_TEXT_COLOR)
        lives_text = self.font_small.render(f"Lives: {self.lives}", True, HUD_TEXT_COLOR)
        best_text = self.font_small.render(f"Best: {self.best_score}", True, HUD_TEXT_COLOR)

        self.screen.blit(score_text, (18, 14))
        self.screen.blit(best_text, best_text.get_rect(midtop=(SCREEN_WIDTH // 2, 14)))
        self.screen.blit(lives_text, lives_text.get_rect(topright=(SCREEN_WIDTH - 18, 14)))
