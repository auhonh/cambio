"""Rules page: a paged panel shared by the main menu and the pause menu."""
from __future__ import annotations

import pygame

from .sprites import GOLD, INK, WHITE, draw_text, text_width

PANEL = (14, 24, 26)
DIM = (150, 180, 170)
BODY = (214, 226, 220)

# Each page: (title, [paragraphs]). A paragraph starting with "- " is a bullet.
# Only characters the pixel font has: A-Z 0-9 - + . : ! ? / , ' ( ) = > < * # %
PAGES = [
    ("THE GOAL", [
        "Finish with the LOWEST total score.",
        "Everyone has 4 face-down cards. You peek at your bottom two before the game starts, so remember them!",
        "Card values: A=1, 2-10 = face value, J=11, Q=12, red K=-1, black K=13.",
        "The game ends once somebody calls Cambio and everyone else has had one last turn. Then all cards are revealed.",
    ]),
    ("YOUR TURN", [
        "Draw the top card of the deck, or take the top card of the discard pile.",
        "- A card from the deck: swap it with one of your cards (the old card goes on the pile), or discard it to use its power.",
        "- A card from the pile: you must swap it with one of your cards. It has no power.",
        "Call Cambio at the start of your turn, or right after your turn ends, as long as the next player has not acted yet. Everyone else then gets one last turn and the Cambio caller's cards are locked.",
    ]),
    ("POWERS", [
        "Powers only work on a card you discard straight from the deck:",
        "- 7 / 8: look at one of your own cards.",
        "- 9 / 10: look at one opponent's card.",
        "- J: swap two cards without looking. They must belong to two different players.",
        "- Q: look at one of yours and one of theirs, then choose to swap them or keep them.",
        "You can always skip a power. The Cambio caller's cards can't be targeted.",
    ]),
    ("JUMPING IN", [
        "Whenever a card is on top of the discard pile, anyone can jump in with a card of the same rank, at any time. Only the first jump-in counts.",
        "- Your own card, right: it goes on the pile and your hand shrinks by one.",
        "- Your own card, wrong: it's flashed to everyone and you draw a penalty card.",
        "- Opponent's card, right: it goes on the pile and they get a replacement AND a penalty card.",
        "- Opponent's card, wrong: it goes on the pile too, replaced by an unseen card, and you draw a penalty card.",
        "Whoever called Cambio can't jump in or be jumped on.",
    ]),
    ("CONTROLS", [
        "- Left click: deck, discard pile and cards.",
        "- Jump in: right click, shift-click, or hover a card and press space. It works on any card, yours or theirs.",
        "- Esc: pause. F11: fullscreen.",
        "- Menu: arrows or mouse to choose, enter to start.",
    ]),
]

PANEL_RECT = pygame.Rect(36, 14, 408, 242)
TEXT_W = PANEL_RECT.w - 28
CHARS = TEXT_W // 4
LINE_H = 8


def wrap(text: str, width: int) -> list[str]:
    indent = "  " if text.startswith("- ") else ""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if len(trial) > width and cur:
            lines.append(cur)
            cur = indent + w
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


class RulesPanel:
    """Paged rules. `on_key` / `on_mouse` return True when the panel should close."""

    def __init__(self):
        self.page = 0
        self.mouse = (0, 0)

    # button rects
    def _prev(self):
        return pygame.Rect(PANEL_RECT.x + 12, PANEL_RECT.bottom - 26, 70, 16)

    def _next(self):
        return pygame.Rect(PANEL_RECT.right - 82, PANEL_RECT.bottom - 26, 70, 16)

    def _back(self):
        return pygame.Rect(PANEL_RECT.centerx - 35, PANEL_RECT.bottom - 26, 70, 16)

    def turn(self, d):
        self.page = max(0, min(len(PAGES) - 1, self.page + d))

    def on_key(self, key) -> bool:
        if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            return True
        if key in (pygame.K_LEFT, pygame.K_a):
            self.turn(-1)
        elif key in (pygame.K_RIGHT, pygame.K_d, pygame.K_SPACE):
            self.turn(1)
        elif key == pygame.K_RETURN:
            if self.page == len(PAGES) - 1:
                return True
            self.turn(1)
        return False

    def on_mouse(self, pos, button) -> bool:
        if button != 1:
            return False
        if self._back().collidepoint(pos):
            return True
        if self._prev().collidepoint(pos):
            self.turn(-1)
        elif self._next().collidepoint(pos):
            self.turn(1)
        return False

    def _button(self, surf, rect, label, enabled=True, gold=False):
        hover = enabled and rect.collidepoint(self.mouse)
        base = (60, 84, 88) if enabled else (36, 48, 52)
        if gold:
            base = GOLD
        shade = tuple(min(255, c + 25) for c in base) if hover else base
        pygame.draw.rect(surf, INK, rect.inflate(2, 2), border_radius=3)
        pygame.draw.rect(surf, shade, rect, border_radius=3)
        col = INK if gold else (WHITE if enabled else DIM)
        draw_text(surf, label, (rect.centerx, rect.centery - 2), col, 1, None, "center")

    def draw(self, surf, mouse=None):
        if mouse is not None:
            self.mouse = mouse
        dim = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        dim.fill((6, 12, 14, 205))
        surf.blit(dim, (0, 0))
        pygame.draw.rect(surf, PANEL, PANEL_RECT, border_radius=5)
        pygame.draw.rect(surf, GOLD, PANEL_RECT, 1, border_radius=5)
        title, paras = PAGES[self.page]
        draw_text(surf, "RULES", (PANEL_RECT.x + 14, PANEL_RECT.y + 10), DIM, 1, None)
        draw_text(surf, f"{self.page + 1}/{len(PAGES)}", (PANEL_RECT.right - 14, PANEL_RECT.y + 10), DIM, 1, None, "right")
        draw_text(surf, title, (PANEL_RECT.centerx, PANEL_RECT.y + 8), GOLD, 2, INK, "center")
        y = PANEL_RECT.y + 32
        for p in paras:
            for line in wrap(p, CHARS):
                draw_text(surf, line, (PANEL_RECT.x + 14, y), BODY, 1, None)
                y += LINE_H
            y += 5
        last = self.page == len(PAGES) - 1
        self._button(surf, self._prev(), "< PREV", self.page > 0)
        self._button(surf, self._next(), "NEXT >", not last)
        self._button(surf, self._back(), "BACK", True, gold=True)
