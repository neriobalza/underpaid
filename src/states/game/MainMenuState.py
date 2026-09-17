"""Pantalla de inicio y navegación principal."""

from gale.state import BaseState

import settings
from src.gui.Menu import Menu, draw_text


class MainMenuState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self) -> None:
        self.menu = Menu(self.game, [
            ("Jugar", lambda: self.state_machine.change("player_select")),
            ("Configuración", lambda: self.state_machine.change("settings")),
            ("Salir", self.game.quit),
        ])

    def on_input(self, input_id, input_data) -> None:
        self.menu.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        draw_text(surface, "UNDERPAID", self.game.fonts["large"], 115,
                  settings.ACCENT_COLOR)
        draw_text(surface, "Menú principal", self.game.fonts["medium"], 160)
        self.menu.render(surface)
        draw_text(surface, "Flechas / W-S · Enter · Ratón · Mando: cruceta / A",
                  self.game.fonts["small"], 438, settings.MUTED_COLOR)
