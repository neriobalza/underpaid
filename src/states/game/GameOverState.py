"""Resumen de jornada y derrota al perder todas las estrellas."""

from gale.state import BaseState

import settings
from src.gui.Menu import Menu, draw_text


class GameOverState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players, delivered: int, total: int, incorrect: int = 0, points: int = 0) -> None:
        self.players = dict(players)
        self.delivered = delivered
        self.total = total
        self.incorrect = incorrect
        self.points = points
        items = []
        if self.game.stars > 0:
            self.game.play_music("win", loops=0, intro_loop=False)
            items.append(("Siguiente jornada", self.next_day))
        items.append(("Menú principal", lambda: self.state_machine.change("main_menu")))
        self.menu = Menu(self.game, items, y=310)

    def next_day(self) -> None:
        if self.game.stars == 0:
            return
        self.game.day += 1
        connected = {
            number: player for number, player in self.players.items()
            if player.is_connected(self.game.controllers)
        }
        if len(connected) == 2:
            self.state_machine.change("play", players=connected)
        else:
            self.state_machine.change("player_select", players=connected)

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
        else:
            self.menu.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        title = "Fin del juego" if self.game.stars == 0 else "Fin de jornada"
        draw_text(surface, title, self.game.fonts["large"], 90, settings.ACCENT_COLOR)
        draw_text(surface, f"Día {self.game.day} · Entregados: {self.delivered}/{self.total}",
                  self.game.fonts["medium"], 160)
        draw_text(surface, f"Estrellas: {self.game.stars}/{settings.MAX_STARS} · Puntos: {self.game.score}",
                  self.game.fonts["medium"], 200)
        message = "No quedan estrellas." if self.game.stars == 0 else "Cada jornada incompleta pierde una estrella."
        draw_text(surface, f"Incorrectos: {self.incorrect} · Puntos de la jornada: {self.points:+d}",
                  self.game.fonts["small"], 240, settings.TEXT_COLOR)
        draw_text(surface, message, self.game.fonts["small"], 270, settings.MUTED_COLOR)
        self.menu.render(surface)
