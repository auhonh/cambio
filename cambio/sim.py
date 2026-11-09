"""Headless bot-vs-bot simulation (used by tests and for sanity checks)."""
from __future__ import annotations

import random
import sys
from collections import Counter

from . import actions as A
from .bot import Bot
from .engine import Game, Phase


def play_game(n_players: int, seed: int, level: str = "medium", max_steps: int = 4000) -> Game:
    g = Game(n_players, seed)
    rng = random.Random(seed + 1)
    bots = [Bot(i, level, rng) for i in range(n_players)]
    g.apply(0, A.Ready())
    steps = 0
    while g.phase != Phase.GAME_OVER:
        steps += 1
        if steps > max_steps:
            raise RuntimeError("game did not terminate")
        if g.jump_open:  # first (random) bot that remembers a match slams it
            order = list(range(n_players))
            rng.shuffle(order)
            for pid in order:
                slot = bots[pid].wants_jump(g.view(pid))
                if slot is not None:
                    g.apply(pid, A.JumpIn(slot))
                    break
        pid = g.current
        g.apply(pid, bots[pid].choose(g.view(pid)))
    return g


if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    for n in range(2, 6):
        turns, scores, wins = [], [], Counter()
        for seed in range(games):
            g = play_game(n, seed)
            turns.append(g.turn_count)
            scores += g.scores()
            wins.update(g.winners())
        print(f"{n} players: avg turns {sum(turns)/len(turns):.1f}, "
              f"avg score {sum(scores)/len(scores):.1f}, wins by seat {dict(sorted(wins.items()))}")
