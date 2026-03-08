# Tina the Destroyer
# Copyright (c) 2026 Jordi Corbilla.
# All rights reserved.

import json
from pathlib import Path
from typing import Callable, Iterable, Optional

import pygame


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def lerp(start: float, end: float, t: float) -> float:
    return start + (end - start) * t


def safe_init_mixer() -> bool:
    try:
        pygame.mixer.init()
        return True
    except pygame.error:
        return False


def safe_load_image(path: Path) -> Optional[pygame.Surface]:
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        return None


def scale_to_height(image: pygame.Surface, target_height: int) -> pygame.Surface:
    if target_height <= 0:
        return image.copy()
    width, height = image.get_size()
    if height <= 0:
        return image.copy()
    ratio = target_height / float(height)
    new_width = max(1, int(round(width * ratio)))
    return pygame.transform.scale(image, (new_width, target_height))


def scale_to_fit(image: pygame.Surface, max_width: int, max_height: int) -> pygame.Surface:
    width, height = image.get_size()
    if width <= 0 or height <= 0:
        return image.copy()
    scale = min(max_width / float(width), max_height / float(height), 1.0)
    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return pygame.transform.scale(image, new_size)


def load_scaled_image(
    candidates: Iterable[Path],
    placeholder_factory: Callable[[], pygame.Surface],
    target_height: int,
) -> pygame.Surface:
    image = None
    for candidate in candidates:
        if candidate.exists():
            image = safe_load_image(candidate)
            if image is not None:
                break
    if image is None:
        image = placeholder_factory()
    return scale_to_height(image, target_height)


def find_existing_path(candidates: Iterable[Path]) -> Optional[Path]:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def load_sound(candidates: Iterable[Path], mixer_ready: bool) -> Optional[pygame.mixer.Sound]:
    if not mixer_ready:
        return None
    for candidate in candidates:
        if not candidate.exists():
            continue
        try:
            return pygame.mixer.Sound(str(candidate))
        except pygame.error:
            continue
    return None


def load_best_score(path: Path) -> int:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        best_score = int(payload.get("best_score", 0))
        return max(0, best_score)
    except Exception:
        return 0


def save_best_score(path: Path, best_score: int) -> None:
    try:
        path.write_text(json.dumps({"best_score": int(best_score)}, indent=2), encoding="utf-8")
    except Exception:
        pass


def make_player_idle_placeholder() -> pygame.Surface:
    surface = pygame.Surface((48, 64), pygame.SRCALPHA)
    pygame.draw.rect(surface, (195, 52, 69), (16, 14, 16, 24))
    pygame.draw.rect(surface, (245, 215, 180), (14, 4, 20, 14))
    pygame.draw.rect(surface, (60, 30, 30), (12, 3, 24, 6))
    pygame.draw.rect(surface, (35, 35, 45), (14, 38, 9, 22))
    pygame.draw.rect(surface, (35, 35, 45), (25, 38, 9, 22))
    pygame.draw.rect(surface, (195, 52, 69), (8, 19, 8, 17))
    pygame.draw.rect(surface, (195, 52, 69), (32, 19, 8, 17))
    return surface


def make_player_smash_placeholder() -> pygame.Surface:
    surface = pygame.Surface((56, 52), pygame.SRCALPHA)
    pygame.draw.rect(surface, (195, 52, 69), (18, 13, 20, 20))
    pygame.draw.rect(surface, (245, 215, 180), (18, 4, 20, 12))
    pygame.draw.rect(surface, (60, 30, 30), (16, 3, 24, 5))
    pygame.draw.rect(surface, (35, 35, 45), (11, 30, 14, 18))
    pygame.draw.rect(surface, (35, 35, 45), (31, 30, 14, 18))
    pygame.draw.rect(surface, (195, 52, 69), (3, 24, 15, 10))
    pygame.draw.rect(surface, (195, 52, 69), (38, 24, 15, 10))
    return surface


def make_rat_placeholder() -> pygame.Surface:
    surface = pygame.Surface((54, 36), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (160, 160, 170), (4, 8, 42, 22))
    pygame.draw.circle(surface, (150, 150, 160), (44, 16), 10)
    pygame.draw.circle(surface, (90, 90, 100), (47, 14), 3)
    pygame.draw.line(surface, (140, 140, 150), (3, 20), (0, 30), 2)
    return surface


def make_rat_squashed_placeholder() -> pygame.Surface:
    surface = pygame.Surface((54, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (130, 130, 140), (2, 6, 50, 14))
    pygame.draw.line(surface, (60, 20, 20), (20, 10), (24, 14), 2)
    pygame.draw.line(surface, (60, 20, 20), (24, 10), (20, 14), 2)
    pygame.draw.line(surface, (60, 20, 20), (31, 10), (35, 14), 2)
    pygame.draw.line(surface, (60, 20, 20), (35, 10), (31, 14), 2)
    return surface


def make_impact_placeholder() -> pygame.Surface:
    surface = pygame.Surface((96, 64), pygame.SRCALPHA)
    points = [(48, 2), (58, 18), (86, 18), (64, 33), (74, 60), (48, 44), (22, 60), (32, 33), (10, 18), (38, 18)]
    pygame.draw.polygon(surface, (255, 225, 80), points)
    pygame.draw.polygon(surface, (255, 160, 0), points, 3)
    return surface
