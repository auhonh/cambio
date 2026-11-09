# Cambio

Cambio card game vs 1-4 bots, made with pygame.

## Run

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Options: `--bots 1-4`, `--difficulty easy|medium|hard`, `--seed N`, `--start` (skip the menu).

## Controls

- Left click: deck, discard pile, cards
- Jump in: right click, shift-click, or hover + space
- Tab: discard tracker
- Esc: menu

## Rules

- 4 cards each, peek at your bottom two
- A=1, J=11, Q=12, red K=-1, black K=13
- 7/8 look at yours, 9/10 look at theirs, J blind swap, Q look at two then swap
- Jump in if a card matches the top of the discard pile. Wrong guess = penalty card
- Call Cambio to end the game after everyone gets one more turn. Lowest score wins

