from __future__ import annotations

import math
from dataclasses import replace
from typing import ClassVar, Protocol

from nicegui import ui

from lexigon.game import GameState, Lexigon


class Renderable(Protocol):
    def render(self, game: GameState) -> None: ...


class ProgressBar:
    __slots__ = ("bar", "label")

    def __init__(self, progress_width: int = 400):
        with ui.element("div").classes("mt-4"):
            with ui.element("div").style(
                f"width: {progress_width}px; position: relative;"
            ):
                self.bar = ui.linear_progress(value=0, show_value=False).style(
                    "height: 20px; border-radius: 10px;"
                )

                self.label = ui.label("").classes(
                    "absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white font-bold text-sm pointer-events-none"
                )

    def render(self, game: GameState):
        self.bar.value = game.current_points / game.MAX_POINTS
        self.label.text = f"{game.current_points} / {game.MAX_POINTS}"
        if game.completed:
            self.bar.style("background-color: green;")


class CandidateLabel:
    __slots__ = ("container", "entries")

    def __init__(self):
        with ui.element("div").classes("flex flex-wrap gap-2 justify-center mt-4"):
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
        with ui.element("div").classes("mt-4"):
            self.button = ui.button("Submit").classes("bg-blue-500 text-white rounded")

    def bind(self, handler):
        self.button.on("click", handler)
        return self

    def render(self, game: GameState):
        pass


class LexigonView:
    RADIUS: ClassVar[int] = 90
    BUTTON_SIZE: ClassVar[int] = 50
    __slots__ = ("_root", "_handler", "center_button", "ring_buttons", "container_size")

    def __init__(self, lexigon: Lexigon):
        self.container_size = 2 * (LexigonView.RADIUS + LexigonView.BUTTON_SIZE)
        self._root = ui.element("div")
        self._handler = None
        self._reset(lexigon)

    def _reset(self, lexigon: Lexigon):
        with self._root.classes("mt-4 relative").style(
            f"width: {self.container_size}px; height: {self.container_size}px"
        ):
            # Center button
            self.center_button = ui.button(lexigon.mandatory_letter).style(
                f"position: absolute; "
                f"left: {self.container_size / 2 - LexigonView.BUTTON_SIZE / 2}px; "
                f"top: {self.container_size / 2 - LexigonView.BUTTON_SIZE / 2}px; "
                f"width: {LexigonView.BUTTON_SIZE}px; height: {LexigonView.BUTTON_SIZE}px"
            )

            # Ring buttons
            self.ring_buttons = []
            n = len(lexigon.optional_letters)
            for i, letter in enumerate(lexigon.optional_letters):
                angle = 2 * math.pi * i / n
                x = math.cos(angle) * LexigonView.RADIUS
                y = math.sin(angle) * LexigonView.RADIUS
                button = ui.button(letter).style(
                    f"position: absolute; "
                    f"left: {self.container_size / 2 + x - LexigonView.BUTTON_SIZE / 2}px; "
                    f"top: {self.container_size / 2 + y - LexigonView.BUTTON_SIZE / 2}px; "
                    f"width: {LexigonView.BUTTON_SIZE}px; height: {LexigonView.BUTTON_SIZE}px"
                )
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
        with ui.element("div").classes("flex flex-wrap mt-4 gap-2 justify-center mt-4"):
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
                    "absolute -top-2 -right-2 text-xs px-2 py-0.5 rounded-full bg-red-500 text-white shadow"
                )
                self.entries.append(entry)

    def render(self, game: GameState):
        self.clear()
        for move in game.moves:
            self.add(move.word, move.points)

    def clear(self):
        self.container.clear()


class ResetButton:
    __slots__ = ("button",)

    def __init__(self):
        with ui.element("div").classes("mt-4"):
            self.button = ui.button("Reset").classes(
                "text-xs text-gray-500 border border-gray-300 bg-gray-50 opacity-50 hover:opacity-70 px-2 py-1 rounded"
            )

    def bind(self, handler):
        self.button.on("click", handler)
        return self

    def render(self, game: GameState):
        pass


class GameManager:
    __slots__ = ("components", "state")

    def __init__(self, state: GameState):
        self.state = state
        with ui.element("div").classes(
            "w-screen h-screen flex flex-col justify-center items-center"
        ):
            self.components = (
                FoundElementList(),
                ProgressBar(),
                LexigonView(state.lexigon).bind(self.update_candidate),
                ResetButton().bind(self.reset),
                SubmitButton().bind(self.submit_candidate),
                CandidateLabel(),
            )

    def reset(self):
        self.state = self.state.reset()
        self.update_ui()
        ui.notify("Game reset successfully!", color="blue")

    def submit_candidate(self):
        try:
            candidate = self.state.candidate.strip()
            self.state = self.state.test_candidate()
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
