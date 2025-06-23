from __future__ import annotations

import logging
import random
from dataclasses import dataclass, replace
from typing import ClassVar

logger = logging.Logger(__file__)


@dataclass(frozen=True)
class Lexigon:
    mandatory_letter: str
    optional_letters: tuple[str, ...]
    word_list: Wordlist

    NUM_OPTIONAL_LETTERS: ClassVar[int] = 6
    MIN_WORD_LENGTH: ClassVar[int] = 4
    ISOGRAM_BONUS: ClassVar[int] = 10

    def __post_init__(self):
        if len(self.mandatory_letter) != 1:
            raise ValueError("Mandatory letter must be a single character.")
        if not all(len(c) == 1 for c in self.optional_letters):
            raise ValueError("All optional letters must be single characters.")
        if self.mandatory_letter in self.optional_letters:
            raise ValueError("Mandatory letter cannot be in optional letters.")

    def _evaluate(self, word: str) -> int:
        if word in self.word_list.isograms:
            return Lexigon.ISOGRAM_BONUS
        return len(word) - Lexigon.MIN_WORD_LENGTH + 1

    def solve(self, word: str) -> int:
        if self.mandatory_letter not in word:
            raise ValueError(
                f"Word must contain the mandatory letter '{self.mandatory_letter}'."
            )
        if not all(c in self.optional_letters + (self.mandatory_letter,) for c in word):
            raise ValueError(f"Word {word} must only contain allowed letters")

        if word not in self.word_list:
            raise ValueError(f"Word {word} is not in the provided word list.")
        if len(word) < Lexigon.MIN_WORD_LENGTH:
            raise ValueError(f"Word {word} must be at least 4 characters long.")
        return self._evaluate(word)

    @property
    def possible_words(self):
        for w in self.word_list.words:
            try:
                self.solve(w)
                yield w
            except Exception:
                pass

    @property
    def max_points(self) -> int:
        return sum(self._evaluate(w) for w in self.possible_words)

    @staticmethod
    def generate_from_word_list(word_list: Wordlist) -> Lexigon:
        picked = list(random.choice(list(word_list.isograms)))
        random.shuffle(picked)
        mandatory_letter = picked[0]
        optional_letters = tuple(picked[1:])

        return Lexigon(
            mandatory_letter=mandatory_letter,
            optional_letters=optional_letters,
            word_list=word_list,
        )


@dataclass(frozen=True)
class Wordlist:
    words: set[str]
    isograms: set[str]

    @staticmethod
    def make(
        words: set[str],
    ) -> Wordlist:
        isograms = set(
            word
            for word in words
            if (
                len(set(word)) == len(word)
                and len(word) == Lexigon.NUM_OPTIONAL_LETTERS + 1
            )
        )
        if len(isograms) == 0:
            raise ValueError("No isograms found in the provided word list.")
        return Wordlist(
            words=words,
            isograms=isograms,
        )

    def __contains__(self, word: str) -> bool:
        return word in self.words

    def __repr__(self) -> str:
        return f"{{num_words: {len(self.words)}, num_isograms: {len(self.isograms)}}}"


@dataclass(frozen=True)
class Move:
    word: str
    points: int


@dataclass(frozen=True)
class PrefixTree:
    children: dict[str, PrefixTree]
    level: int = 0

    def insert(self, rest: str) -> PrefixTree:
        if len(rest) == 0:
            return self
        curr = rest[0]
        rest = rest[1:]
        child = self.children.get(curr, PrefixTree({}, level=self.level + 1))
        child = child.insert(rest)
        return PrefixTree({**self.children, **{curr: child}}, level=self.level)

    def __contains__(self, rest: str) -> bool:
        if len(rest) == 0:
            return True
        curr = rest[0]
        rest = rest[1:]
        if curr in self.children:
            return rest in self.children[curr]
        else:
            return False


@dataclass(frozen=True)
class Moves:
    moves: tuple[Move, ...]
    tree: PrefixTree

    def __contains__(self, word: str):
        return word in self.tree

    def insert(self, move: Move) -> Moves:
        return Moves(moves=self.moves + (move,), tree=self.tree.insert(move.word))

    def __iter__(self):
        for m in self.moves:
            yield m

    def __len__(self):
        return len(self.moves)


@dataclass
class Hint:
    word: str
    revealed: int

    @property
    def exhausted(self):
        return self.revealed >= len(self.word)

    @property
    def next(self) -> Hint:
        return Hint(self.word, self.revealed + 1)

    def __repr__(self) -> str:
        return self.word[: self.revealed]

    def __iter__(self):
        for c in repr(self):
            yield c


@dataclass(frozen=True)
class GameState:
    candidate: str
    lexigon: Lexigon
    moves: Moves
    max_points: int
    hint: Hint
    penalties: tuple[int, ...] = ()
    MAX_POINTS: ClassVar[int] = 50

    @staticmethod
    def create_from_wordlist(wordlist: Wordlist):
        return GameState.create_from_lexigon(Lexigon.generate_from_word_list(wordlist))

    @staticmethod
    def create_from_lexigon(lexigon: Lexigon) -> GameState:
        print(f"Lexigon {lexigon} supports a maximum of {lexigon.max_points}")
        return GameState(
            candidate="",
            lexigon=lexigon,
            moves=Moves((), PrefixTree({})),
            max_points=min(lexigon.max_points, GameState.MAX_POINTS),
            hint=Hint("", 0),
        )

    @property
    def current_points(self) -> int:
        return sum(m.points for m in self.moves)

    @property
    def completed(self) -> bool:
        return self.current_points >= self.max_points

    @property
    def leftover_words(self) -> set[str]:
        return set(w for w in self.lexigon.possible_words if w not in self.moves)

    def add_letter(self, letter: str) -> GameState:
        if len(letter) != 1:
            raise ValueError("Only single characters can be added.")
        return replace(self, candidate=self.candidate + letter)

    def _new_hint(self) -> Hint:
        return Hint(random.choice(tuple(self.leftover_words)), 0)

    @property
    def total_penalty(self) -> int:
        return sum(self.penalties)

    def request_hint(self) -> GameState:
        if self.hint.exhausted:
            hint = self._new_hint()
        else:
            hint = self.hint
        hint = hint.next
        penalties = self.penalties + (hint.revealed,)
        if self.current_points - sum(penalties) < 0:
            raise ValueError(
                f"You are missing {sum(penalties) - self.current_points} points for requesting the next letter."
            )
        return replace(self, hint=hint, penalties=penalties)

    def add_move(self):
        if self.candidate in self.moves:
            raise ValueError(
                f"Candidate {self.candidate} is already a prefix of a found word."
            )
        return replace(
            self,
            moves=self.moves.insert(
                Move(self.candidate, self.lexigon.solve(self.candidate))
            ),
            candidate="",
            hint=Hint("", 0),
            max_points=min(
                sum(self.lexigon._evaluate(w) for w in self.leftover_words),
                GameState.MAX_POINTS,
            ),
        )

    def reset(self) -> GameState:
        logger.info("resetting game state")
        return GameState.create_from_lexigon(
            Lexigon.generate_from_word_list(self.lexigon.word_list)
        )
