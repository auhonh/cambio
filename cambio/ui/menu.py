"""Title / setup screen: choose 1-4 bot opponents, difficulty."""
from __future__ import annotations

import math

import pygame

from ..cards import Card
from .fx import LOGICAL_H, LOGICAL_W, CardSprite
from .rules import RulesPanel
from .sprites import CREAM, GOLD, INK, RED, WHITE, draw_text, text_width

LEVELS = ["easy", "medium", "hard"]
N_ROWS = 4  # opponents, difficulty, start, rules


class MenuScene:
    def __init__(self, app, n_bots=2, level="medium"):
        self.app = app
        self.n_bots, self.level = n_bots, level
        self.row = 0
        self.t = 0.0
        self.deco = [CardSprite(Card(r, s), (0, 0), phase=i * 0.9)
                     for i, (r, s) in enumerate([(13, "H"), (1, "S"), (12, "D"), (11, "C"), (10, "H")])]
        for sp in self.deco:
            sp.face = sp.face_target = 1.0
        self.mouse = (0, 0)
        self.rules = None  # a RulesPanel while the rules page is open

    # rows: 0 opponents, 1 difficulty, 2 start, 3 rules
    def row_rect(self, i):
        return pygame.Rect(110, 126 + i * 28, 260, 22)

    def change(self, row, d):
        if row == 0:
            self.n_bots = max(1, min(4, self.n_bots + d))
        elif row == 1:
            self.level = LEVELS[(LEVELS.index(self.level) + d) % 3]

    def start(self):
        self.app.start_game(self.n_bots, self.level)

    def on_key(self, key):
        if self.rules:
            if self.rules.on_key(key):
                self.rules = None
            return
        if key in (pygame.K_UP, pygame.K_w):
            self.row = (self.row - 1) % N_ROWS
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.row = (self.row + 1) % N_ROWS
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.change(self.row, -1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.change(self.row, 1)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.row == 2:
                self.start()
            elif self.row == 3:
                self.rules = RulesPanel()
            else:
                self.change(self.row, 1)
        elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            self.n_bots = key - pygame.K_0
        elif key == pygame.K_r:
            self.rules = RulesPanel()
        elif key == pygame.K_ESCAPE:
            self.app.running = False

    def on_mouse(self, pos, button, shift=False):
        if self.rules:
            if self.rules.on_mouse(pos, button):
                self.rules = None
            return
        if button != 1:
            return
        for i in range(N_ROWS):
            r = self.row_rect(i)
            if r.collidepoint(pos):
                self.row = i
                if i == 2:
                    return self.start()
                if i == 3:
                    self.rules = RulesPanel()
                    return
                if i == 0:  # click directly on a number
                    for k in range(1, 5):
                        if self._num_rect(k).collidepoint(pos):
                            self.n_bots = k
                            return
                self.change(i, -1 if pos[0] < r.centerx - 10 and i != 0 else 1)

    def _num_rect(self, k):
        r = self.row_rect(0)
        return pygame.Rect(r.right - 4 * 24 - 4 + (k - 1) * 24, r.y, 20, r.h)

    def update(self, dt, mouse):
        self.t += dt
        self.mouse = mouse
        for i, sp in enumerate(self.deco):
            a = self.t * 0.8 + i * 1.3
            sp.x = 240 + (i - 2) * 46
            sp.y = 60 + math.sin(a) * 3 + abs(i - 2) * 2
            sp.rot = (i - 2) * -7
            sp.tx, sp.ty = sp.x, sp.y

    def draw(self, surf, atlas, felt):
        felt.draw(surf)
        for sp in self.deco:
            sp.draw(surf, atlas, self.t, idle=False)
        draw_text(surf, "CAMBIO", (240, 92), GOLD, 5, INK, "center")
        rows = [("OPPONENTS", None), ("DIFFICULTY", self.level.upper())]
        for i in range(N_ROWS):
            r = self.row_rect(i)
            sel = self.row == i
            pygame.draw.rect(surf, INK, r.inflate(2, 2), border_radius=3)
            pygame.draw.rect(surf, (36, 52, 60) if not sel else (70, 56, 40), r, border_radius=3)
            if sel:
                pygame.draw.rect(surf, GOLD, r, 1, border_radius=3)
            if i in (2, 3):
                label = "START GAME" if i == 2 else "RULES"
                draw_text(surf, label, (r.centerx, r.centery - 2), GOLD if sel else WHITE, 1, None, "center")
                continue
            draw_text(surf, rows[i][0], (r.x + 8, r.centery - 2), WHITE if sel else (190, 200, 196))
            if i == 0:
                for k in range(1, 5):
                    nr = self._num_rect(k)
                    on = k == self.n_bots
                    pygame.draw.rect(surf, GOLD if on else (50, 70, 76), nr, border_radius=2)
                    draw_text(surf, str(k), (nr.centerx, nr.centery - 2), INK if on else WHITE, 1, None, "center")
            else:
                draw_text(surf, f"< {rows[i][1]} >", (r.right - 8, r.centery - 2), GOLD if sel else WHITE, 1, None, "right")
        draw_text(surf, "ARROWS / MOUSE TO CHOOSE, ENTER TO START", (240, 247), (170, 200, 190), 1, INK, "center")
        if self.rules:
            self.rules.draw(surf, self.mouse)
