"""Selección de resolución de ventana y modo de pantalla."""

import pygame

from gale.state import BaseState

import settings
from src.gui.Menu import Menu, draw_text


class SettingsState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self) -> None:
        self.pending_index = self.game.resolution_index
        self.pending_fullscreen = self.game.fullscreen
        self.message = ""
        self.menu = Menu(self.game, [
            ("", lambda: self.cycle_resolution(1)),
            ("", self.toggle_fullscreen),
            ("Aplicar", self.apply_settings),
            ("Volver", lambda: self.state_machine.change("main_menu")),
        ], y=190)
        self.update_label()

    def update_label(self) -> None:
        width, height = settings.WINDOW_RESOLUTIONS[self.pending_index]
        self.menu.items[0] = (
            f"<  Ventana: {width} × {height}  >",
            lambda: self.cycle_resolution(1),
        )
        mode = "Pantalla completa" if self.pending_fullscreen else "Ventana"
        self.menu.items[1] = (f"<  Modo: {mode}  >", self.toggle_fullscreen)

    def toggle_fullscreen(self) -> None:
        self.pending_fullscreen = not self.pending_fullscreen
        self.message = ""
        self.update_label()

    def cycle_resolution(self, direction: int) -> None:
        self.pending_index = (
            self.pending_index + direction
        ) % len(settings.WINDOW_RESOLUTIONS)
        self.message = ""
        self.update_label()

    def apply_settings(self) -> None:
        try:
            self.game.set_display(self.pending_index, self.pending_fullscreen)
        except pygame.error:
            self.message = "No se pudo aplicar la configuración de pantalla."
        else:
            self.message = "Configuración aplicada."

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
        elif input_id in ("left", "right") and input_data.pressed:
            if self.menu.selected == 0:
                self.cycle_resolution(-1 if input_id == "left" else 1)
            elif self.menu.selected == 1:
                self.toggle_fullscreen()
        else:
            self.menu.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        draw_text(surface, "Configuración", self.game.fonts["large"], 100,
                  settings.ACCENT_COLOR)
        draw_text(surface, "Pantalla virtual: 640 × 480 · Proporción 4:3",
                  self.game.fonts["small"], 150, settings.MUTED_COLOR)
        self.menu.render(surface)
        draw_text(surface, self.message, self.game.fonts["small"], 420)
        draw_text(surface, "Izquierda / Derecha: cambiar · Esc: volver",
                  self.game.fonts["small"], 454, settings.MUTED_COLOR)
