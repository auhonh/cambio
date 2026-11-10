"""Pure-logic Cambio engine (no pygame).

Card memory is real: every Card is a unique persistent object, and the engine
tracks, per player, exactly which card ids that player has legitimately seen
(`known`). Knowledge follows the physical card, so if a card you peeked at is
blind-swapped elsewhere you still know where it went.

Players only ever see the game through `Game.view(pid)`.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from . import actions as A
from .actions import Pos
from .cards import Card, Deck

HAND_SIZE = 4
INITIAL_PEEK_SLOTS = (1, 3)  # the two "bottom" cards of the 2x2 grid
MIN_PLAYERS, MAX_PLAYERS = 2, 5


class IllegalAction(Exception):
    pass


class Phase(Enum):
    PEEK = auto()          # waiting for the human to finish the starting peek
    DRAW = auto()          # current player: draw, take discard, or call Cambio
    HOLDING = auto()       # current player holds a card
    POWER_SELF = auto()    # 7/8
    POWER_OPP = auto()     # 9/10
    POWER_JACK = auto()    # J blind swap
    POWER_QUEEN = auto()   # Q look at two
    QUEEN_DECIDE = auto()  # Q swap or keep
    GAME_OVER = auto()


@dataclass
class Event:
    kind: str
    pid: int = -1
    data: dict = field(default_factory=dict)


@dataclass
class View:
    """Everything one player is allowed to know."""
    pid: int
    n: int
    phase: Phase
    current: int
    held: Optional[Card]            # visible only to the holder, or if taken from discard
    held_from: Optional[str]
    occupied: list[list[bool]]      # occupied[owner][slot]
    known: dict[Pos, Card]          # cards this player has seen, by current location
    discard: tuple[Card, ...]       # public, in order (last = top)
    deck_count: int
    jump_open: bool
    cambio_caller: Optional[int]
    queen_pair: Optional[tuple[Pos, Pos]]
    turn_count: int


class Game:
    def __init__(self, n_players: int, seed: Optional[int] = None):
        if not MIN_PLAYERS <= n_players <= MAX_PLAYERS:
            raise ValueError("players must be 2..5")
        self.n = n_players
        self.rng = random.Random(seed)
        self.deck = Deck(self.rng)
        self.hands: list[list[Optional[Card]]] = [
            [self.deck.draw_pile.pop() for _ in range(HAND_SIZE)] for _ in range(n_players)
        ]
        self.known: list[set[int]] = [set() for _ in range(n_players)]
        for pid in range(n_players):
            for slot in INITIAL_PEEK_SLOTS:
                self.known[pid].add(self.hands[pid][slot].id)
        self.current = self.rng.randrange(n_players)
        self.phase = Phase.PEEK
        self.held: Optional[Card] = None
        self.held_from: Optional[str] = None
        self.jump_open = False
        self.cambio_caller: Optional[int] = None
        self.queen_pair: Optional[tuple[Pos, Pos]] = None
        self.turn_count = 0
        self.events: list[Event] = []

    # ------------------------------------------------------------------ info
    @property
    def discard(self) -> list[Card]:
        return self.deck.discard

    @property
    def top(self) -> Optional[Card]:
        return self.deck.discard[-1] if self.deck.discard else None

    def view(self, pid: int) -> View:
        known = {}
        for o, hand in enumerate(self.hands):
            for s, c in enumerate(hand):
                if c is not None and c.id in self.known[pid]:
                    known[(o, s)] = c
        show_held = self.held is not None and (self.current == pid or self.held_from == "discard")
        return View(
            pid=pid, n=self.n, phase=self.phase, current=self.current,
            held=self.held if show_held else None,
            held_from=self.held_from if self.held is not None else None,
            occupied=[[c is not None for c in hand] for hand in self.hands],
            known=known, discard=tuple(self.deck.discard),
            deck_count=len(self.deck.draw_pile), jump_open=self.jump_open,
            cambio_caller=self.cambio_caller, queen_pair=self.queen_pair,
            turn_count=self.turn_count,
        )

    def scores(self) -> list[int]:
        return [sum(c.value for c in hand if c is not None) for hand in self.hands]

    def winners(self) -> list[int]:
        s = self.scores()
        best = min(s)
        return [i for i, v in enumerate(s) if v == best]

    def all_cards(self) -> list[Card]:
        """Every card in existence (used by tests to check conservation)."""
        cards = list(self.deck.draw_pile) + list(self.deck.discard)
        cards += [c for h in self.hands for c in h if c is not None]
        if self.held is not None:
            cards.append(self.held)
        return cards

    # --------------------------------------------------------------- helpers
    def _emit(self, kind: str, pid: int = -1, **data) -> None:
        self.events.append(Event(kind, pid, data))

    def _card(self, pos: Pos) -> Optional[Card]:
        o, s = pos
        if 0 <= o < self.n and 0 <= s < len(self.hands[o]):
            return self.hands[o][s]
        return None

    def _targetable(self, pos: Pos) -> bool:
        return self._card(pos) is not None and pos[0] != self.cambio_caller

    def _draw_card(self) -> Optional[Card]:
        if not self.deck.draw_pile:
            if len(self.deck.discard) <= 1:
                return None
            moved = self.deck.reshuffle()
            for k in self.known:  # reshuffled cards are anonymous again
                for c in moved:
                    k.discard(c.id)
            self._emit("reshuffle")
        return self.deck.draw_pile.pop()

    def _to_discard(self, card: Card, pid: int, via: str) -> None:
        self.deck.discard.append(card)
        self.jump_open = True
        self._emit("discard", pid, card=card, via=via)

    def _end_turn(self) -> None:
        self.held = None
        self.held_from = None
        self.queen_pair = None
        self.phase = Phase.DRAW
        nxt = (self.current + 1) % self.n
        if self.cambio_caller is not None and nxt == self.cambio_caller:
            self._end_game()
            return
        self.current = nxt
        self.turn_count += 1

    def _end_game(self) -> None:
        self.phase = Phase.GAME_OVER
        for k in self.known:
            for hand in self.hands:
                k.update(c.id for c in hand if c is not None)
        self._emit("game_over", -1, scores=self.scores(), winners=self.winners())

    def _opp_targets(self, pid: int, swappable: bool) -> list[Pos]:
        out = []
        for o in range(self.n):
            if o == pid:
                continue
            for s, c in enumerate(self.hands[o]):
                if c is not None and (not swappable or o != self.cambio_caller):
                    out.append((o, s))
        return out

    def _own_slots(self, pid: int) -> list[int]:
        return [s for s, c in enumerate(self.hands[pid]) if c is not None]

    def _begin_power(self, pid: int, card: Card) -> None:
        r = card.rank
        own, opp = self._own_slots(pid), self._opp_targets(pid, False)
        if r in (7, 8) and own:
            self.phase = Phase.POWER_SELF
        elif r in (9, 10) and opp:
            self.phase = Phase.POWER_OPP
        elif r == 11 and self._swap_pool(pid) >= 2:
            self.phase = Phase.POWER_JACK
        elif r == 12 and own and self._opp_targets(pid, True):
            self.phase = Phase.POWER_QUEEN
        else:
            self._end_turn()

    def _swap_pool(self, pid: int) -> int:
        n = len(self._own_slots(pid)) if pid != self.cambio_caller else 0
        return n + len(self._opp_targets(pid, True))

    # ----------------------------------------------------------------- apply
    def apply(self, pid: int, action) -> None:
        if self.phase == Phase.GAME_OVER:
            raise IllegalAction("game over")
        if isinstance(action, A.JumpIn):
            return self._jump(pid, action.slot, action.target)
        if self.phase == Phase.PEEK:
            if isinstance(action, A.Ready):
                self.phase = Phase.DRAW
                return
            raise IllegalAction("waiting for ready")
        if pid != self.current:
            raise IllegalAction("not your turn")

        ph = self.phase
        if ph == Phase.DRAW:
            return self._do_draw(pid, action)
        if ph == Phase.HOLDING:
            return self._do_holding(pid, action)
        if ph == Phase.POWER_SELF:
            if isinstance(action, A.Skip):
                self._emit("skip", pid)
                return self._end_turn()
            if isinstance(action, A.LookSelf) and self._card((pid, action.slot)):
                c = self.hands[pid][action.slot]
                self.known[pid].add(c.id)
                self._emit("look", pid, owner=pid, slot=action.slot, card=c)
                return self._end_turn()
        elif ph == Phase.POWER_OPP:
            if isinstance(action, A.Skip):
                self._emit("skip", pid)
                return self._end_turn()
            if isinstance(action, A.LookOpp) and action.owner != pid and self._card((action.owner, action.slot)):
                c = self.hands[action.owner][action.slot]
                self.known[pid].add(c.id)
                self._emit("look", pid, owner=action.owner, slot=action.slot, card=c)
                return self._end_turn()
        elif ph == Phase.POWER_JACK:
            if isinstance(action, A.Skip):
                self._emit("skip", pid)
                return self._end_turn()
            if isinstance(action, A.BlindSwap):
                a, b = action.a, action.b
                if a != b and self._targetable(a) and self._targetable(b):
                    self._swap_positions(a, b)
                    self._emit("blind_swap", pid, a=a, b=b)
                    return self._end_turn()
        elif ph == Phase.POWER_QUEEN:
            if isinstance(action, A.Skip):
                self._emit("skip", pid)
                return self._end_turn()
            if isinstance(action, A.QueenLook):
                a, b = (pid, action.own_slot), action.opp
                if self._card(a) and b[0] != pid and self._targetable(b):
                    self.known[pid].add(self._card(a).id)
                    self.known[pid].add(self._card(b).id)
                    self.queen_pair = (a, b)
                    self.phase = Phase.QUEEN_DECIDE
                    self._emit("queen_look", pid, own=a, opp=b, cards=(self._card(a), self._card(b)))
                    return
        elif ph == Phase.QUEEN_DECIDE:
            if isinstance(action, A.QueenDecide):
                a, b = self.queen_pair
                if action.swap and self._targetable(a) and self._targetable(b):
                    self._swap_positions(a, b)
                    self._emit("queen_swap", pid, a=a, b=b)
                else:
                    self._emit("queen_keep", pid)
                return self._end_turn()
        raise IllegalAction(f"{action} not allowed in {ph.name}")

    def _swap_positions(self, a: Pos, b: Pos) -> None:
        ca, cb = self._card(a), self._card(b)
        self.hands[a[0]][a[1]], self.hands[b[0]][b[1]] = cb, ca

    def _do_draw(self, pid: int, action) -> None:
        if isinstance(action, A.DrawDeck):
            card = self._draw_card()
            if card is None:
                return self._end_game()
            self.held, self.held_from = card, "deck"
            self.phase = Phase.HOLDING
            self._emit("draw", pid)
            return
        if isinstance(action, A.TakeDiscard):
            if not self.deck.discard:
                raise IllegalAction("discard pile empty")
            if not self._own_slots(pid):
                raise IllegalAction("no card to swap with")
            card = self.deck.discard.pop()
            self.held, self.held_from = card, "discard"
            self.jump_open = False
            self.phase = Phase.HOLDING
            self._emit("take_discard", pid, card=card)
            return
        if isinstance(action, A.CallCambio):
            if self.cambio_caller is not None:
                raise IllegalAction("Cambio already called")
            self.cambio_caller = pid
            self._emit("cambio", pid)
            return self._end_turn()
        raise IllegalAction(f"{action} not allowed in DRAW")

    def _do_holding(self, pid: int, action) -> None:
        card = self.held
        if isinstance(action, A.Swap):
            old = self._card((pid, action.slot))
            if old is None:
                raise IllegalAction("empty slot")
            self.hands[pid][action.slot] = card
            if self.held_from == "discard":      # everyone saw it come off the pile
                for k in self.known:
                    k.add(card.id)
            else:
                self.known[pid].add(card.id)
            self._emit("swap", pid, slot=action.slot, old=old, new=card, src=self.held_from)
            self.held = None
            self._to_discard(old, pid, "swap")
            return self._end_turn()
        if isinstance(action, A.Discard):
            if self.held_from != "deck":
                raise IllegalAction("a card taken from the discard pile must be swapped in")
            self.held = None
            self._to_discard(card, pid, "discard")
            return self._begin_power(pid, card)
        raise IllegalAction(f"{action} not allowed while holding")

    def _jump(self, pid: int, slot: int, target: Optional[int] = None) -> None:
        if self.phase == Phase.PEEK:
            raise IllegalAction("not started")
        if not self.jump_open or self.top is None:
            raise IllegalAction("too late")
        if pid == self.cambio_caller:
            raise IllegalAction("locked after Cambio")
        owner = pid if target is None else target
        if not 0 <= owner < self.n:
            raise IllegalAction("no such player")
        if owner == self.cambio_caller:
            raise IllegalAction("locked after Cambio")
        card = self._card((owner, slot))
        if card is None:
            raise IllegalAction("empty slot")
        if card.rank == self.top.rank:
            self.hands[owner][slot] = None
            self.deck.discard.append(card)
            self.jump_open = False
            self._emit("jump_ok", pid, slot=slot, card=card, owner=owner)
            if owner != pid:  # slammed an opponent's card: they take the wrong-jump penalty
                self._penalty(owner)
        else:
            for k in self.known:  # the wrong card is flashed to the whole table
                k.add(card.id)
            self._emit("jump_fail", pid, slot=slot, card=card, owner=owner)
            self._penalty(pid)

    def _penalty(self, pid: int) -> None:
        pen = self._draw_card()
        if pen is not None:
            hand = self.hands[pid]
            new_slot = next((i for i, c in enumerate(hand) if c is None), None)
            if new_slot is None:
                hand.append(pen)
                new_slot = len(hand) - 1
            else:
                hand[new_slot] = pen
            self._emit("penalty", pid, slot=new_slot)
