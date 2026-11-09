"""pygame application shell: window, scene switching, post effects."""
from __future__ import annotations

import pygame

from .fx import LOGICAL_H, LOGICAL_W, Felt, make_overlay
from .menu import MenuScene
from .sprites import Atlas
from .table import GameScene


class App:
    def __init__(self, seed=None, bots=2, level="medium", autostart=False):
        pygame.init()
        pygame.display.set_caption("Cambio")
        flags = pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((LOGICAL_W, LOGICAL_H), flags, vsync=1)
        self.clock = pygame.time.Clock()
        self.atlas = Atlas()
        self.felt = Felt()
        self.overlay = make_overlay()
        self.seed = seed
        self.running = True
        self.menu = MenuScene(self, bots, level)
        self.scene = self.menu
        if autostart:
            self.menu.start()

    def start_game(self, n_bots, level, seed, tracker=True):
        self.menu.n_bots, self.menu.level, self.menu.tracker = n_bots, level, tracker
        self.scene = GameScene(self, n_bots, level, seed, tracker)

    def go_menu(self):
        self.scene = self.menu

    def run(self):
        while self.running:
            dt = min(self.clock.tick(60) / 1000.0, 0.05)
            mouse = pygame.mouse.get_pos()
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN:
                    self.scene.on_key(e.key)
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button in (1, 3):
                    shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)
                    self.scene.on_mouse(e.pos, e.button, shift)
            self.felt.update(dt)
            self.scene.update(dt, mouse)
            self.scene.draw(self.screen, self.atlas, self.felt)
            self.screen.blit(self.overlay, (0, 0))
            pygame.display.flip()
        pygame.quit()
