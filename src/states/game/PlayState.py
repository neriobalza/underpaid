"""Dos personajes animados con métodos de entrada independientes."""

import pygame
from gale.state import BaseState
from gale.timer import Timer

import settings
from src.gui.Menu import draw_text
from src.world.Room import Room


class PlayState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players) -> None:
        self.players = dict(players)
        self.room = Room()
        for player in self.players.values():
            player.stop()
            player.position.update(self.room.spawn_position(player.number))
        self.game_minutes = float(settings.CLOCK_START_HOUR * 60)
        # Gale actualiza Timer una vez por frame en su bucle de juego.
        self.match_clock = Timer.tween(
            settings.MATCH_DURATION,
            [(self, {"game_minutes": float(settings.CLOCK_END_HOUR * 60)})],
            on_finish=self._finish_match,
        )

    @property
    def clock_text(self) -> str:
        hours, minutes = divmod(int(self.game_minutes), 60)
        period = "AM" if hours % 24 < 12 else "PM"
        return f"{hours % 12 or 12}:{minutes:02d} {period}"

    def _finish_match(self) -> None:
        if self.state_machine.current is self:
            self.state_machine.change("main_menu")

    def update(self, dt: float) -> None:
        connected = {
            number: player for number, player in self.players.items()
            if player.is_connected(self.game.controllers)
        }
        if len(connected) != 2:
            self.state_machine.change("player_select", players=connected)
            return
        for player in self.players.values():
            player.update(dt, self.room.walkable_area, self.room.objects)
            if player.interact_requested:
                player.interact_requested = False
                self.room.interact(player, self.players.values())

    def exit(self) -> None:
        self.match_clock.remove()
        for player in self.players.values():
            player.clear_carrying()

    def on_input(self, input_id, input_data) -> None:
        if input_id == "back" and input_data.pressed:
            self.state_machine.change("main_menu")
            return
        for player in self.players.values():
            interaction = (
                player.uses_keyboard and input_id == "confirm"
                and getattr(input_data, "key", None) == pygame.K_RETURN
            ) or (
                not player.uses_keyboard and input_id == "pad_a"
                and getattr(input_data, "gamepad_id", None) == player.controller_id
            )
            if interaction:
                if input_data.pressed and not player.interact_held:
                    player.interact_requested = True
                player.interact_held = input_data.pressed
            player.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        self.room.render(surface)
        entities = list(self.players.values()) + [obj for obj in self.room.objects if obj.solid]
        for entity in sorted(entities, key=lambda entity: entity.hitbox.bottom):
            entity.render(surface)
        self.room.render_placement(surface, self.players.values())
        pygame.draw.rect(surface, settings.CLOCK_BAR_COLOR,
                         (0, 0, settings.VIRTUAL_WIDTH, settings.CLOCK_BAR_HEIGHT))
        draw_text(surface, self.clock_text, self.game.fonts["medium"],
                  settings.CLOCK_BAR_HEIGHT // 2, settings.BACKGROUND_COLOR)
