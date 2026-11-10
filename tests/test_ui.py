"""Headless UI tests: drive GameScene with real click coordinates."""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import pytest

from cambio import actions as A
from cambio.cards import Card
from cambio.engine import Phase
from cambio.ui.fx import Felt, make_overlay
from cambio.ui.sprites import Atlas
from cambio.ui.table import DECK_POS, DISCARD_POS, GameScene


class FakeApp:
    def start_game(self, *a):
        self.started = a

    def go_menu(self):
        self.menu = True


@pytest.fixture(scope="module")
def gfx():
    pygame.init()
    screen = pygame.display.set_mode((480, 270))
    return screen, Atlas(), Felt()


def advance(s, felt, seconds=0.5, dt=1 / 30):
    for _ in range(int(seconds / dt)):
        felt.update(dt)
        s.update(dt, (0, 0))


def human_turn(s, felt):
    for _ in range(4000):
        if s.g.current == 0 and s.g.phase == Phase.DRAW and not s.busy():
            return
        advance(s, felt, 0.1)
    raise AssertionError("never reached the human's turn")


@pytest.mark.parametrize("bots", [1, 2, 3, 4])
def test_click_flow_and_render(gfx, bots):
    screen, atlas, felt = gfx
    s = GameScene(FakeApp(), bots, "hard", seed=bots)
    advance(s, felt, 2)
    s.on_button("ready")
    human_turn(s, felt)
    s.on_mouse(DECK_POS, 1)                      # click the deck -> holding a card
    assert s.g.phase == Phase.HOLDING and s.g.held_from == "deck"
    s.on_mouse(s.slot_pos(0, 2), 1)              # click own slot -> swap
    assert s.g.hands[0][2] is not None and s.g.phase != Phase.HOLDING or s.g.phase == Phase.DRAW
    for _ in range(30):
        advance(s, felt, 0.2)
        s.draw(screen, atlas, felt)
    assert s.g.view(0).n == bots + 1


def _put_on_discard(s, rank_match, slot_card):
    g = s.g
    pool = [c for c in g.deck.draw_pile if (c.rank == slot_card.rank) == rank_match]
    c = pool[0]
    g.deck.draw_pile.remove(c)
    g.deck.discard.append(c)
    g.jump_open = True


def test_right_click_jump_correct_and_wrong(gfx):
    screen, atlas, felt = gfx
    s = GameScene(FakeApp(), 2, "medium", seed=3)
    advance(s, felt, 2)
    s.on_button("ready")
    g = s.g
    card = g.hands[0][0]
    _put_on_discard(s, False, card)
    n = len(g.hands[0])
    s.on_mouse(s.slot_pos(0, 0), 3)                  # wrong rank -> penalty card
    assert len(g.hands[0]) == n + 1 and g.events[-1].kind == "penalty"
    card = g.hands[0][2]
    _put_on_discard(s, True, card)
    s.on_mouse(s.slot_pos(0, 2), 1, shift=True)      # shift-click, matching rank -> slot empties
    assert g.hands[0][2] is None and g.top == card
    assert len({c.id for c in g.all_cards()}) == 52
    s.on_mouse(s.slot_pos(0, 1), 3)                  # first jump already won -> too late, no penalty
    assert len(g.hands[0]) == n + 1


def test_pause_freezes_game_and_resumes(gfx):
    screen, atlas, felt = gfx
    app = FakeApp()
    s = GameScene(app, 2, "medium", seed=3)
    advance(s, felt, 2)
    s.on_button("ready")
    s.on_key(pygame.K_ESCAPE)
    assert s.paused
    n_events, t = len(s.g.events), s.t
    advance(s, felt, 8)                              # bots must not act while paused
    assert len(s.g.events) == n_events and s.t == t
    s.draw(screen, atlas, felt)
    s.on_mouse((240, 129), 1)                        # RESUME button
    assert not s.paused
    s.on_key(pygame.K_ESCAPE)
    s.on_key(pygame.K_ESCAPE)                        # esc again also resumes
    assert not s.paused
    s.on_key(pygame.K_ESCAPE)
    s.on_mouse((240, 153), 1)                        # MAIN MENU button
    assert getattr(app, "menu", False)


def test_felt_stays_opaque_over_a_full_cycle(gfx):
    screen, atlas, felt = gfx
    surf = pygame.Surface((480, 270))
    for _ in range(int(felt.FRAMES / felt.SPEED * 2 * 10)):  # two full cycles
        felt.update(0.1)
        surf.fill((0, 0, 0))
        felt.draw(surf)
        assert surf.get_at((240, 135))[1] > 60, "felt turned dark (stale alpha)"
