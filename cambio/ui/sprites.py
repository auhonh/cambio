"""Procedural pixel art: bitmap font, suits, card faces and backs.

Everything is drawn at the 480x270 logical resolution; the window scales it up
with nearest-neighbour so pixels stay crisp.
"""
from __future__ import annotations

import pygame

from ..cards import Card, SUITS

CARD_W, CARD_H = 34, 46

# palette
CREAM = (246, 238, 214)
CREAM_SHADE = (226, 214, 184)
OUTLINE = (28, 22, 38)
RED = (205, 52, 60)
BLACK = (34, 32, 54)
BACK_BASE = (176, 32, 48)
BACK_LATTICE = (228, 150, 152)
BACK_EDGE = (246, 238, 214)
GOLD = (255, 205, 70)
WHITE = (250, 248, 240)
INK = (20, 16, 30)

# ----------------------------------------------------------------- 3x5 font
_G = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011",
    "D": "110101101101110", "E": "111100110100111", "F": "111100110100100",
    "G": "011100101101011", "H": "101101111101101", "I": "111010010010111",
    "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "111101101101111",
    "P": "110101110100100", "Q": "010101101110011", "R": "110101110101101",
    "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111",
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111",
    "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
    "6": "011100111101111", "7": "111001010010010", "8": "111101111101111",
    "9": "111101111001110",
    "-": "000000111000000", "+": "000010111010000", ".": "000000000000010",
    ":": "000010000010000", "!": "010010010000010", "?": "110001010000010",
    "/": "001001010100100", ",": "000000000010100", "'": "010010000000000",
    "(": "010100100100010", ")": "010001001001010", "=": "000111000111000",
    ">": "100010001010100", "<": "001010100010001", "*": "101010111010101",
    "#": "101111101111101", "%": "101001010100101", " ": "000000000000000",
}
_glyph_cache: dict = {}


def _glyph(ch: str, color, scale: int) -> pygame.Surface:
    key = (ch, color, scale)
    s = _glyph_cache.get(key)
    if s is None:
        bits = _G.get(ch.upper(), _G["?"])
        s = pygame.Surface((3 * scale, 5 * scale), pygame.SRCALPHA)
        for i, b in enumerate(bits):
            if b == "1":
                s.fill(color, ((i % 3) * scale, (i // 3) * scale, scale, scale))
        _glyph_cache[key] = s
    return s


def text_width(text: str, scale: int = 1) -> int:
    return max(0, len(text) * (4 * scale) - scale)


def draw_text(surf, text, pos, color=WHITE, scale=1, shadow=None, align="left"):
    x, y = pos
    w = text_width(text, scale)
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    x, y = int(x), int(y)
    if shadow is not None:
        so = max(1, scale // 2)
        draw_text(surf, text, (x + so, y + so), shadow, scale)
    for i, ch in enumerate(text):
        surf.blit(_glyph(ch, color, scale), (x + i * 4 * scale, y))
    return w


# ------------------------------------------------------------------- suits
_SUIT7 = {
    "H": ["0110110", "1111111", "1111111", "1111111", "0111110", "0011100", "0001000"],
    "D": ["0001000", "0011100", "0111110", "1111111", "0111110", "0011100", "0001000"],
    "S": ["0001000", "0011100", "0111110", "1111111", "1111111", "0001000", "0011100"],
    "C": ["0011100", "0111110", "0011100", "1101011", "1111111", "0001000", "0011100"],
}
_SUIT5 = {
    "H": ["01010", "11111", "11111", "01110", "00100"],
    "D": ["00100", "01110", "11111", "01110", "00100"],
    "S": ["00100", "01110", "11111", "00100", "01110"],
    "C": ["01110", "01110", "11111", "00100", "01110"],
}


def suit_color(suit: str):
    return RED if suit in "HD" else BLACK


def _blit_bits(surf, rows, pos, color, scale=1):
    x0, y0 = pos
    for y, row in enumerate(rows):
        for x, b in enumerate(row):
            if b == "1":
                surf.fill(color, (x0 + x * scale, y0 + y * scale, scale, scale))


def draw_suit(surf, suit, pos, size=5, scale=1, color=None):
    rows = (_SUIT5 if size == 5 else _SUIT7)[suit]
    _blit_bits(surf, rows, pos, color or suit_color(suit), scale)


_CROWN = {"K": ["1010101", "1111111", "1111111"], "Q": ["0010100", "1010101", "0111110"], "J": ["0001000", "0011100", "0001000"]}

# pip layouts for number cards: (column, row) with columns L=0,C=1,R=2
_COLX = (7, 15, 22)
_ROWY = (15, 21, 27, 33, 39)
_PIPS = {
    2: [(1, 0), (1, 4)],
    3: [(1, 0), (1, 2), (1, 4)],
    4: [(0, 0), (2, 0), (0, 4), (2, 4)],
    5: [(0, 0), (2, 0), (1, 2), (0, 4), (2, 4)],
    6: [(0, 0), (2, 0), (0, 2), (2, 2), (0, 4), (2, 4)],
    7: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2), (0, 4), (2, 4)],
    8: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2), (1, 3), (0, 4), (2, 4)],
    9: [(0, 0), (2, 0), (0, 1), (2, 1), (1, 2), (0, 3), (2, 3), (0, 4), (2, 4)],
    10: [(0, 0), (2, 0), (1, 0.5), (0, 1), (2, 1), (0, 3), (2, 3), (1, 3.5), (0, 4), (2, 4)],
}


def _base(fill, border=OUTLINE) -> pygame.Surface:
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(s, border, (0, 0, CARD_W, CARD_H), border_radius=4)
    pygame.draw.rect(s, fill, (1, 1, CARD_W - 2, CARD_H - 2), border_radius=3)
    return s


def make_face(card: Card) -> pygame.Surface:
    s = _base(CREAM)
    col = suit_color(card.suit)
    pygame.draw.rect(s, CREAM_SHADE, (3, 3, CARD_W - 6, CARD_H - 6), width=1, border_radius=2)
    label = card.label
    draw_text(s, label, (4, 4), col, scale=2)
    r = card.rank
    if r == 1:
        draw_suit(s, card.suit, (CARD_W // 2 - 10, CARD_H // 2 - 7), size=7, scale=3)
    elif r >= 11:
        pygame.draw.rect(s, CREAM_SHADE, (6, 16, 22, 26), width=1)
        _blit_bits(s, _CROWN[label], (14, 18), GOLD if r == 13 else col)
        draw_text(s, label, (13, 22), col, scale=3)
        draw_suit(s, card.suit, (15, 37), size=5)
    else:
        for c, row in _PIPS[r]:
            draw_suit(s, card.suit, (_COLX[c], int(_ROWY[0] + row * 6)), size=5)
    return s


def make_back() -> pygame.Surface:
    s = _base(BACK_EDGE)
    pygame.draw.rect(s, BACK_BASE, (3, 3, CARD_W - 6, CARD_H - 6), border_radius=2)
    for y in range(4, CARD_H - 4):  # diamond lattice
        for x in range(4, CARD_W - 4):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                s.set_at((x, y), BACK_LATTICE)
    cx, cy = CARD_W // 2, CARD_H // 2
    pygame.draw.rect(s, BACK_EDGE, (cx - 6, cy - 6, 12, 12), border_radius=2)
    pygame.draw.rect(s, BACK_BASE, (cx - 5, cy - 5, 10, 10), border_radius=2)
    draw_suit(s, "D", (cx - 3, cy - 3), size=5, color=CREAM)
    return s


def make_shadow() -> pygame.Surface:
    s = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 80), (0, 0, CARD_W, CARD_H), border_radius=4)
    return s


class Atlas:
    """Lazy cache of every card face plus the shared back and shadow."""

    def __init__(self):
        self.back = make_back()
        self.shadow = make_shadow()
        self._faces: dict[int, pygame.Surface] = {}

    def face(self, card: Card) -> pygame.Surface:
        s = self._faces.get(card.id)
        if s is None:
            s = self._faces[card.id] = make_face(card)
        return s


def outline_surface(surf: pygame.Surface, color) -> pygame.Surface:
    """Silhouette outline for hover/selection glow."""
    mask = pygame.mask.from_surface(surf)
    out = pygame.Surface((surf.get_width() + 4, surf.get_height() + 4), pygame.SRCALPHA)
    sil = mask.to_surface(setcolor=color, unsetcolor=(0, 0, 0, 0))
    for dx, dy in ((0, 1), (1, 0), (2, 1), (1, 2), (0, 0), (2, 0), (0, 2), (2, 2)):
        out.blit(sil, (dx + 1, dy + 1))
    return out
