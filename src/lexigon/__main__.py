import argparse

from nicegui import ui

from lexigon.game import GameState, Wordlist
from lexigon.ui import GameManager

if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(description="Lexigon Game")
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Path to the word list file (e.g., 'wordlist.txt')",
        default="data/german.txt",
    )
    parser.add_argument(
        "-P", "--port", type=int, default=8080, help="Port to run the game server on"
    )
    args = parser.parse_args()
    wordlist = Wordlist.make(
        words=set(
            line.strip().lower()
            for line in open(args.path, encoding="utf-8").readlines()
        )
    )
    manager = GameManager(GameState.create_from_wordlist(wordlist))
    ui.run(title="Lexigon", port=args.port, reload=True, show=False)
