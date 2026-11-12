"""Cambio vs bots. Run: python main.py [--bots N] [--difficulty easy|medium|hard]"""
import argparse

from cambio.ui.app import App


def main():
    p = argparse.ArgumentParser(description="Cambio card game vs AI opponents")
    p.add_argument("--bots", type=int, choices=[1, 2, 3, 4], default=2, help="number of bot opponents")
    p.add_argument("--difficulty", choices=["easy", "medium", "hard", "cambio"], default="medium")
    p.add_argument("--start", action="store_true", help="skip the menu and start immediately")
    a = p.parse_args()
    App(bots=a.bots, level=a.difficulty, autostart=a.start).run()


if __name__ == "__main__":
    main()
