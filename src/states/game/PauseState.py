"""Menú superpuesto que conserva la partida debajo en la pila de Gale."""

import pygame
from gale.state import BaseState

import settings
from src.gui.Menu import Menu, draw_text


class PauseState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, play_state) -> None:
        self.play_state = play_state
        self.play_state.reset_input()
        if self.play_state.active_dialog and self.play_state.active_dialog.sound:
            self.play_state.active_dialog.sound.stop()
        self.panel = pygame.Rect(80, 125, 480, 245)
        self.menu = Menu(self.game, [
            ("Continuar", self.resume),
            ("Menú principal", lambda: self.state_machine.change("main_menu")),
        ], y=230)

    def resume(self) -> None:
        self.state_machine.pop()

    def exit(self) -> None:
        self.play_state.reset_input()

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.resume()
            return
        self.menu.on_input(input_id, input_data)

    def render(self, surface) -> None:
        panel = pygame.Surface(self.panel.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*settings.PANEL_COLOR, 200), panel.get_rect(), border_radius=12)
        surface.blit(panel, self.panel)
        pygame.draw.rect(surface, settings.ACCENT_COLOR, self.panel, width=2, border_radius=12)
        draw_text(surface, "Pausa", self.game.fonts["large"], 175, settings.ACCENT_COLOR)
        self.menu.render(surface)
        draw_text(surface, "Esc: continuar", self.game.fonts["small"], 346, settings.MUTED_COLOR)
