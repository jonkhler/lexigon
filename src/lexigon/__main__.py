import argparse
from pathlib import Path

from nicegui import ui

from lexigon.game import GameState, Wordlist
from lexigon.ui import GameManager


def load_wordlists(path: str) -> dict[str, Wordlist]:
    """Load wordlists from the specified path."""
    wordlists = {}
    path_obj = Path(path)
    for file in path_obj.glob("*.txt"):
        with open(file, encoding="utf-8") as f:
            words = set(line.strip().lower() for line in f if line.strip())
            wordlists[file.stem] = Wordlist.make(words)
    return wordlists


if __name__ in {"__main__", "__mp_main__"}:
    parser = argparse.ArgumentParser(description="Lexigon Game")
    parser.add_argument(
        "-p",
        "--path",
        type=str,
        help="Path to the word list file (e.g., 'wordlist.txt')",
        default="data",
    )
    parser.add_argument(
        "-P", "--port", type=int, default=8080, help="Port to run the game server on"
    )
    parser.add_argument(
        "-H", "--host", type=str, default="0.0.0.0", help="Host for server"
    )
    args = parser.parse_args()
    # wordlist = Wordlist.make(
    #     words=set(
    #         line.strip().lower()
    #         for line in open(args.path, encoding="utf-8").readlines()
    #     )
    # )
    wordlists = load_wordlists(args.path)
    manager = GameManager(wordlists)
    ui.run(host=args.host, title="Lexigon", port=args.port, reload=True, show=False)
