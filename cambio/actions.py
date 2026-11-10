"""Actions that players (human UI or bots) submit to the engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

Pos = tuple[int, int]  # (owner player id, slot index)


@dataclass(frozen=True)
class Ready:  # human is done memorising the starting peek
    pass


@dataclass(frozen=True)
class DrawDeck:
    pass


@dataclass(frozen=True)
class TakeDiscard:
    pass


@dataclass(frozen=True)
class CallCambio:
    pass


@dataclass(frozen=True)
class Swap:  # holding a card: put it in `slot`, old card goes to discard
    slot: int


@dataclass(frozen=True)
class Discard:  # holding a card drawn from the deck: discard it (may trigger power)
    pass


@dataclass(frozen=True)
class Skip:  # decline a power
    pass


@dataclass(frozen=True)
class LookSelf:  # 7/8
    slot: int


@dataclass(frozen=True)
class LookOpp:  # 9/10
    owner: int
    slot: int


@dataclass(frozen=True)
class BlindSwap:  # jack: swap any two cards without looking
    a: Pos
    b: Pos


@dataclass(frozen=True)
class QueenLook:  # queen: look at one own card and one opponent card
    own_slot: int
    opp: Pos


@dataclass(frozen=True)
class QueenDecide:  # queen: swap the two cards you just looked at, or not
    swap: bool


@dataclass(frozen=True)
class JumpIn:  # slam a card matching the discard top. Any time.
    slot: int
    target: Optional[int] = None  # whose card: None = your own, else an opponent's
