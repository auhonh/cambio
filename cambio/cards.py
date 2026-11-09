"""Cards and the persistent, seedable deck.

Every card is a unique (rank, suit) pair from ONE 52-card deck, so identity is
never re-randomised: once a card has been seen, it can be tracked (counted).
"""
from __future__ import annotations

import random
from dataclasses import dataclass

SUITS = ("S", "H", "D", "C")  # spades, hearts, diamonds, clubs
RED_SUITS = ("H", "D")

# Point values. Everything is the face rank except where overridden here.
# Aces=1, J=11, Q=12, black king=13, red king=-1.
RED_KING_VALUE = -1
BLACK_KING_VALUE = 13

_LABELS = {1: "A", 11: "J", 12: "Q", 13: "K"}


@dataclass(frozen=True)
class Card:
    rank: int  # 1..13
    suit: str  # one of SUITS

    @property
    def id(self) -> int:
        return SUITS.index(self.suit) * 13 + self.rank - 1

    @property
    def is_red(self) -> bool:
        return self.suit in RED_SUITS

    @property
    def value(self) -> int:
        if self.rank == 13:
            return RED_KING_VALUE if self.is_red else BLACK_KING_VALUE
        return self.rank

    @property
    def label(self) -> str:
        return _LABELS.get(self.rank, str(self.rank))

    def __str__(self) -> str:
        return f"{self.label}{self.suit}"


def full_deck() -> list[Card]:
    return [Card(r, s) for s in SUITS for r in range(1, 14)]


def card_from_id(card_id: int) -> Card:
    return Card(card_id % 13 + 1, SUITS[card_id // 13])


class Deck:
    """One real deck: a draw pile and a public, ordered discard pile."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.draw_pile: list[Card] = full_deck()
        rng.shuffle(self.draw_pile)
        self.discard: list[Card] = []

    def reshuffle(self) -> list[Card]:
        """Shuffle the discard pile (minus its top card) into a new draw pile."""
        top = self.discard.pop()
        moved = self.discard
        self.rng.shuffle(moved)
        self.draw_pile = moved
        self.discard = [top]
        return list(moved)
