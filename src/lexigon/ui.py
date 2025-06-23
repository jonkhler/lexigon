from __future__ import annotations

import math
from dataclasses import replace
from typing import ClassVar, Protocol

from nicegui import events, ui

from lexigon.game import GameState, Lexigon, Wordlist


class Renderable(Protocol):
    def render(self, game: GameState) -> None: ...


class ProgressBar:
    __slots__ = ("bar", "label")

    def __init__(self, progress_width: int = 400):
        with ui.element("div").classes("mt-2"):
            with ui.element("div").style(
                f"width: {progress_width}px; position: relative;"
            ):
                self.bar = ui.linear_progress(value=0, show_value=False).style(
                    "height: 20px; border-radius: 10px;"
                )

                self.label = ui.label("").classes(
                    "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white font-bold text-sm pointer-events-none"
                )

    def render(self, state: GameState):
        self.bar.value = (state.current_points - state.total_penalty) / state.max_points
        self.label.text = (
            f"{state.current_points - state.total_penalty} / {state.max_points}"
        )
        if state.completed:
            self.bar.style("background-color: green;")


class CandidateLabel:
    __slots__ = ("container", "entries")

    def __init__(self):
        with ui.element("div").classes("flex flex-wrap gap-2 justify-center mt-2"):
            self.container = ui.row().classes("gap-3 flex-wrap justify-center")
            self.entries: list[ui.element] = []

    def add(self, letter: str):
        with self.container:
            with ui.element("div") as entry:
                entry.classes(
                    "relative border border-gray-300 rounded px-2 py-1 bg-white shadow text-black"
                )
                ui.label(letter.upper()).classes("text-base font-semibold")
                self.entries.append(entry)

    def clear(self):
        for entry in self.entries:
            entry.delete()
        self.entries.clear()

    def render(self, game: GameState):
        self.clear()
        self.container.clear()
        for letter in game.candidate:
            self.add(letter)


class SubmitButton:
    __slots__ = ("button",)

    def __init__(self):
        with ui.element("div").classes("mt-1"):
            self.button = ui.button("Submit").classes(
                "bg-blue-500 text-white px-2 py-1 rounded"
            )

    def bind(self, handler):
        self.button.on("click", handler)
        return self

    def render(self, game: GameState):
        pass


class LexigonView:
    RADIUS: ClassVar[int] = 70
    BUTTON_SIZE: ClassVar[int] = 50
    __slots__ = ("_root", "_handler", "center_button", "ring_buttons", "container_size")

    def __init__(self, lexigon: Lexigon):
        self.container_size = 2 * (LexigonView.RADIUS + LexigonView.BUTTON_SIZE)
        self._root = ui.element("div")
        self._handler = None
        self._reset(lexigon)

    def _reset(self, lexigon: Lexigon):
        with self._root.classes("mt-1 relative").style(
            f"width: {self.container_size}px; height: {self.container_size}px"
        ):
            # Center button
            self.center_button = ui.button(lexigon.mandatory_letter, color="blue-8")
            self.center_button.style(
                f"position: absolute; "
                f"left: {self.container_size / 2 - LexigonView.BUTTON_SIZE / 2}px; "
                f"top: {self.container_size / 2 - LexigonView.BUTTON_SIZE / 2}px; "
                f"width: {LexigonView.BUTTON_SIZE}px; height: {LexigonView.BUTTON_SIZE}px"
            )
            self.center_button.classes("text-white rounded-full shadow")

            # Ring buttons
            self.ring_buttons = []
            n = len(lexigon.optional_letters)
            for i, letter in enumerate(lexigon.optional_letters):
                angle = 2 * math.pi * i / n
                x = math.cos(angle) * LexigonView.RADIUS
                y = math.sin(angle) * LexigonView.RADIUS
                button = ui.button(letter)
                button.style(
                    f"position: absolute; "
                    f"left: {self.container_size / 2 + x - LexigonView.BUTTON_SIZE / 2}px; "
                    f"top: {self.container_size / 2 + y - LexigonView.BUTTON_SIZE / 2}px; "
                    f"width: {LexigonView.BUTTON_SIZE}px; height: {LexigonView.BUTTON_SIZE}px"
                )
                button.classes("text-white rounded-full shadow")
                self.ring_buttons.append(button)

        if self._handler is not None:
            self._bind(self._handler)

    def render(self, game: GameState):
        self._root.clear()
        self._reset(game.lexigon)

    def _bind(self, handler):
        self.center_button.on("click", lambda: handler(self.center_button.text))
        for button in self.ring_buttons:
            button.on("click", lambda b=button: handler(b.text))
        return self

    def bind(self, handler):
        if not callable(handler):
            raise ValueError("Handler must be a callable function.")
        self._handler = handler
        return self._bind(handler)


class FoundElementList:
    __slots__ = ("container", "entries")

    def __init__(self):
        with ui.element("div").classes("flex flex-wrap mt-2 gap-2 justify-center"):
            self.container = ui.row().classes("gap-3 flex-wrap justify-center")
            self.entries: list[ui.element] = []

    def add(self, word: str, points: int):
        with self.container:
            with ui.element("div") as entry:
                entry.classes(
                    "relative border border-gray-300 rounded px-3 py-1 bg-white shadow text-black"
                )
                ui.label(word.upper()).classes("text-base font-semibold")
                ui.label(f"{points}").classes(
                    "absolute -top-2 -right-2 text-xs px-2 py-0.5 rounded-full bg-green-500 text-white shadow"
                )
                self.entries.append(entry)

    def add_penalty(self, penalty: int):
        with self.container:
            with ui.element("div") as entry:
                entry.classes(
                    "relative border border-gray-300 rounded px-2 py-0.5 text-s rounded-full bg-red shadow text-white shadow"
                )
                ui.label(f"-{penalty}").classes("font-semibold")
                self.entries.append(entry)

    def render(self, game: GameState):
        self.clear()
        for move in game.moves:
            self.add(move.word, move.points)
        if game.total_penalty > 0:
            self.add_penalty(game.total_penalty)

    def clear(self):
        self.container.clear()


class ResetButton:
    __slots__ = ("button",)

    def __init__(self):
        with ui.element("div").classes("mt-2"):
            self.button = ui.button("Reset").classes(
                "text-xs text-gray-500 border border-gray-300 bg-gray-50 opacity-50 hover:opacity-70 px-2 py-1 rounded"
            )

    def bind(self, handler):
        self.button.on("click", handler)
        return self

    def render(self, game: GameState):
        pass


class HintButton:
    __slots__ = "button"

    def __init__(self) -> None:
        with ui.element("div").classes("mt-2"):
            self.button = ui.button("Get Hint").classes(
                "text-xs text-gray-500 border border-gray-300 bg-gray-50 opacity-50 hover:opacity-70 px-2 py-1 rounded"
            )

    def bind(self, handler):
        self.button.on("click", handler)
        return self

    def render(self, game: GameState):
        pass


class HintLabel:
    __slots__ = ("container", "entries")

    def __init__(self):
        with ui.element("div").classes("flex flex-wrap gap-2 justify-center mt-2"):
            self.container = ui.row().classes("gap-3 flex-wrap justify-center")
            self.entries: list[ui.element] = []

    def add(self, letter: str, revealed: int = 0):
        with self.container:
            with ui.element("div") as entry:
                entry.classes(
                    "relative border border-gray-300 rounded px-2 py-1 bg-white shadow text-black"
                )
                ui.label(letter.upper()).classes("text-base font-semibold")
                ui.label(f"-{revealed}").classes(
                    "absolute -top-2 -right-2 text-xs px-2 py-0.5 rounded-full bg-red-500 text-white shadow"
                )
                self.entries.append(entry)

    def clear(self):
        for entry in self.entries:
            entry.delete()
        self.entries.clear()

    def render(self, game: GameState):
        self.clear()
        self.container.clear()
        for i, letter in enumerate(game.hint):
            self.add(letter, revealed=i + 1)


class WordlistSelector:
    __slots__ = ("selector", "options")

    def __init__(self, wordlists: list[str], default: str):
        with ui.element("div").classes("mt-2"):
            self.selector = ui.select(
                wordlists, label="Select Wordlist", value=default
            ).classes("w-64")
            self.options = wordlists

    def bind(self, handler):
        def _handler(event: events.ValueChangeEventArguments):
            self.selector.on_value_change(lambda _: None)  # Unbind previous handler
            handler(event)
            self.selector.set_value(str(event.value))
            # Rebind the handler
            self.selector.on_value_change(_handler)
            # self.selector.value = str(event.value)

        self.selector.on_value_change(_handler)
        return self

    def render(self, game: GameState):
        pass


class GameManager:
    __slots__ = ("components", "state", "wordlists")

    def __init__(self, wordlists: dict[str, Wordlist]):
        self.wordlists = wordlists
        initial_wordlist_key = next(iter(wordlists))
        initial_wordlist = wordlists[initial_wordlist_key]
        self.state = GameState.create_from_wordlist(initial_wordlist)
        ui.add_head_html("""
        <style>
        .nicegui-content {
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh; 
        }
        </style>
        """)
        with ui.element("div").classes(
            "flex flex-col items-center justify-start gap-y-2 overflow-y-auto"
        ):
            ui.image("static/logo-short.png").classes("w-50 mt-4mx-auto")
            self.components = (
                FoundElementList(),
                ProgressBar(),
                LexigonView(self.state.lexigon).bind(self.update_candidate),
                SubmitButton().bind(self.submit_candidate),
                CandidateLabel(),
                HintButton().bind(self.request_hint),
                HintLabel(),
                ResetButton().bind(self.reset),
                WordlistSelector(
                    list(self.wordlists.keys()), initial_wordlist_key
                ).bind(self.select_wordlist),
            )
            self.update_ui()

    def reset(self):
        self.state = self.state.reset()
        self.update_ui()
        ui.notify("Game reset successfully!", color="blue")

    def win(self):
        num_moves = len(self.state.moves)
        self.state = self.state.reset()
        self.update_ui()
        ui.notify(
            f"Congratulations: you won within {num_moves} moves!",
            color="blue",
        )

    def select_wordlist(self, event: events.ValueChangeEventArguments):
        wordlist_key = str(event.value)
        if wordlist_key not in self.wordlists:
            ui.notify(f"Wordlist '{wordlist_key}' not found.", color="red")
            return
        wordlist = self.wordlists[wordlist_key]
        self.state = GameState.create_from_wordlist(wordlist)
        self.update_ui()
        ui.notify(f"Switched to wordlist: {wordlist_key}", color="green")

    def request_hint(self):
        try:
            self.state = self.state.request_hint()
            self.update_ui()
        except ValueError as e:
            self.update_ui()
            ui.notify(f"Error: {str(e)}", color="red")

    def submit_candidate(self):
        try:
            candidate = self.state.candidate.strip()
            self.state = self.state.add_move()
            if self.state.completed:
                self.win()
            else:
                self.update_ui()
                ui.notify(
                    f"Candidate '{candidate}' submitted successfully!",
                    color="green",
                )
        except ValueError as e:
            self.state = replace(self.state, candidate="")
            self.update_ui()
            ui.notify(f"Error: {str(e)}", color="red")

    def update_candidate(self, letter: str):
        try:
            self.state = self.state.add_letter(letter)
            self.update_ui()
        except ValueError as e:
            ui.notify(f"Error: {str(e)}", color="red")

    def update_ui(self):
        for component in self.components:
            component.render(self.state)
