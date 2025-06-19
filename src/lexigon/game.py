from __future__ import annotations

import random
from dataclasses import dataclass, replace
from typing import ClassVar


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


@dataclass(frozen=True)
class Move:
    word: str
    points: int


@dataclass
class GameState:
    candidate: str
    lexigon: Lexigon
    moves: tuple[Move, ...]
    MAX_POINTS: ClassVar[int] = 100

    @staticmethod
    def create(wordlist_path: str) -> GameState:
        word_list = Wordlist.make(
            words=set(
                line.strip().lower()
                for line in open(wordlist_path, encoding="utf-8").readlines()
            )
        )
        lexigon = Lexigon.generate_from_word_list(word_list)
        return GameState(candidate="", lexigon=lexigon, moves=())

    @property
    def current_points(self) -> int:
        return sum(m.points for m in self.moves)

    @property
    def completed(self) -> bool:
        return self.current_points >= self.MAX_POINTS

    def add_letter(self, letter: str) -> GameState:
        if len(letter) != 1:
            raise ValueError("Only single characters can be added.")
        return replace(self, candidate=self.candidate + letter)

    def test_candidate(self):
        if self.candidate in set(m.word for m in self.moves):
            raise ValueError(f"Candidate '{self.candidate}' has already been used.")
        points = self.lexigon.solve(self.candidate)
        return replace(
            self,
            moves=self.moves + (Move(self.candidate, points),),
            candidate="",
        )

    def reset(self) -> GameState:
        return replace(
            self,
            candidate="",
            moves=(),
            lexigon=Lexigon.generate_from_word_list(self.lexigon.word_list),
        )
