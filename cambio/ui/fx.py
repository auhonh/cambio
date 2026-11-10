"""Visual effects: swirling felt, vignette/scanlines, animated card sprites."""
from __future__ import annotations

import math
import random

import pygame

from .sprites import CARD_H, CARD_W, GOLD, Atlas, outline_surface

LOGICAL_W, LOGICAL_H = 480, 270

FELT = [(23, 72, 56), (25, 77, 60), (27, 82, 63), (29, 87, 66), (31, 92, 69), (33, 96, 72)]


class Felt:
    """Soft, slowly drifting swirl. Frames are cross-faded so nothing pops or flickers."""
    FRAMES = 8
    SPEED = 0.35  # frames per second

    def __init__(self, palette=FELT):
        w, h = LOGICAL_W // 4, LOGICAL_H // 4
        n = len(palette)
        self.frames = []
        for f in range(self.FRAMES):
            t = f / self.FRAMES * math.tau
            s = pygame.Surface((w, h))
            for y in range(h):
                for x in range(w):
                    dx, dy = (x - w / 2) / h, (y - h / 2) / h
                    d = math.hypot(dx, dy)
                    a = math.atan2(dy, dx)
                    v = math.sin(d * 11 + a * 2 + t) + 0.5 * math.sin(dx * 9 - dy * 7 - t)
                    s.set_at((x, y), palette[min(n - 1, int((v + 1.5) / 3 * n))])
            self.frames.append(pygame.transform.smoothscale(s, (LOGICAL_W, LOGICAL_H)).convert())
        self.t = 0.0

    def update(self, dt):
        self.t += dt

    def draw(self, surf):
        pos = self.t * self.SPEED
        i = int(pos) % self.FRAMES
        blend = pos - int(pos)
        base = self.frames[i]
        base.set_alpha(255)  # may still carry the alpha it had as the fade-in layer
        surf.blit(base, (0, 0))
        nxt = self.frames[(i + 1) % self.FRAMES]
        nxt.set_alpha(int(blend * 255))
        surf.blit(nxt, (0, 0))


def make_overlay() -> pygame.Surface:
    """Soft vignette, baked once."""
    ov = pygame.Surface((LOGICAL_W, LOGICAL_H), pygame.SRCALPHA)
    vw, vh = LOGICAL_W // 4, LOGICAL_H // 4
    vig = pygame.Surface((vw, vh), pygame.SRCALPHA)
    for y in range(vh):
        for x in range(vw):
            d = math.hypot((x / vw - 0.5) * 1.25, (y / vh - 0.5) * 1.5)
            a = max(0, min(150, int((d - 0.35) * 330)))
            vig.set_at((x, y), (6, 12, 14, a))
    ov.blit(pygame.transform.smoothscale(vig, (LOGICAL_W, LOGICAL_H)), (0, 0))
    return ov


def smooth(cur: float, target: float, rate: float, dt: float) -> float:
    return target + (cur - target) * math.exp(-rate * dt)


class CardSprite:
    """One persistent card: eases toward a target and flips between back/face."""

    def __init__(self, card, pos, phase=None):
        self.card = card
        self.x, self.y = pos
        self.tx, self.ty = pos
        self.tz = 0
        self.face = 0.0        # 0 = back showing, 1 = face showing
        self.face_target = 0.0
        self.lift = 0.0        # hover lift in px
        self.lift_target = 0.0
        self.tilt = 0.0        # degrees from hover/mouse
        self.rot_target = 0.0  # resting angle
        self.rot = 0.0
        self.phase = phase if phase is not None else random.random() * math.tau
        self.glow = None       # outline colour
        self.delay = 0.0       # seconds before this card starts moving (deal stagger)
        self.moving = False

    def set_target(self, x, y, z=0, rot=0.0):
        self.tx, self.ty, self.tz, self.rot_target = x, y, z, rot

    def update(self, dt):
        if self.delay > 0:
            self.delay -= dt
            self.moving = True
            return
        self.x = smooth(self.x, self.tx, 14, dt)
        self.y = smooth(self.y, self.ty, 14, dt)
        self.rot = smooth(self.rot, self.rot_target, 12, dt)
        self.face += max(-1, min(1, self.face_target - self.face)) * min(1.0, dt * 9)
        if abs(self.face - self.face_target) < 0.02:
            self.face = self.face_target
        self.lift = smooth(self.lift, self.lift_target, 20, dt)
        self.moving = (abs(self.x - self.tx) > 1.2 or abs(self.y - self.ty) > 1.2
                       or self.face != self.face_target)

    def contains(self, mx, my) -> bool:
        return abs(mx - self.tx) <= CARD_W / 2 and abs(my - (self.ty - self.lift_target)) <= CARD_H / 2

    def draw(self, surf, atlas: Atlas, t: float, mouse=None, hovered=False, idle=True):
        sx = abs(1 - 2 * self.face)
        img = atlas.face(self.card) if self.face > 0.5 else atlas.back
        w = max(2, int(round(CARD_W * sx)))
        if w != CARD_W:
            img = pygame.transform.scale(img, (w, CARD_H))
        bob = math.sin(t * 1.6 + self.phase) * 0.7 if idle else 0
        tilt = 0.0
        if hovered and mouse is not None:
            tilt = max(-1, min(1, (mouse[0] - self.x) / (CARD_W / 2))) * 7
        wob = math.sin(t * 1.1 + self.phase) * 1.1 if idle else 0
        self.tilt = smooth(self.tilt, tilt, 16, 1 / 60)
        ang = round(self.rot + wob + self.tilt)  # whole degrees: no shimmer
        y = self.y - self.lift + bob
        shadow = atlas.shadow
        if w != CARD_W:
            shadow = pygame.transform.scale(shadow, (w, CARD_H))
        surf.blit(shadow, shadow.get_rect(center=(self.x + 2 + self.lift * 0.4, y + 3 + self.lift * 0.6)))
        if self.glow is not None:
            g = outline_surface(img, self.glow)
            if abs(ang) > 0.2:
                g = pygame.transform.rotate(g, ang)
            surf.blit(g, g.get_rect(center=(self.x, y)))
        if abs(ang) > 0.2:
            img = pygame.transform.rotate(img, ang)
        surf.blit(img, img.get_rect(center=(self.x, y)))
