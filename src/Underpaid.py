"""Juego y máquina de estados de Underpaid."""

import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.state import StateMachine

import settings
from src.states.game.MainMenuState import MainMenuState
from src.states.game.PlayState import PlayState
from src.states.game.SettingsState import SettingsState
from src.states.game.PlayerSelectState import PlayerSelectState
from src.input.ControllerManager import ControllerManager


class Underpaid(Game):
    def init(self) -> None:
        self.fonts = settings.create_fonts()
        self.controllers = ControllerManager()
        self.resolution_index = settings.DEFAULT_RESOLUTION_INDEX
        self.fullscreen = False
        if settings.FULLSCREEN:
            self.set_display(self.resolution_index, True)
        self.state_machine = StateMachine({
            "main_menu": lambda sm: MainMenuState(sm, self),
            "settings": lambda sm: SettingsState(sm, self),
            "play": lambda sm: PlayState(sm, self),
            "player_select": lambda sm: PlayerSelectState(sm, self),
        })
        self.state_machine.change("main_menu")

    def set_resolution(self, index: int) -> None:
        """Elige la resolución de ventana y conserva el modo actual."""
        self.set_display(index, self.fullscreen)

    def set_display(self, index: int, fullscreen: bool) -> None:
        """Aplica el modo de pantalla sin modificar la superficie virtual."""
        if not 0 <= index < len(settings.WINDOW_RESOLUTIONS):
            raise ValueError("Índice de resolución inválido")
        if fullscreen and self.fullscreen:
            # La resolución seleccionada sólo se usa al volver a ventana.
            self.resolution_index = index
            return
        # SCALED ocupa el escritorio, conserva 4:3 con bandas negras y
        # convierte los eventos del ratón a las coordenadas de la superficie.
        size = (
            (self.virtual_width, self.virtual_height)
            if fullscreen else settings.WINDOW_RESOLUTIONS[index]
        )
        flags = pygame.FULLSCREEN | pygame.SCALED if fullscreen else 0
        previous_size = self.screen.get_size()
        previous_flags = pygame.FULLSCREEN | pygame.SCALED if self.fullscreen else 0
        try:
            # Recrear la pantalla permite pasar de una superficie de ventana
            # al renderer de SCALED en los distintos controladores de SDL.
            if fullscreen != self.fullscreen:
                pygame.display.quit()
                pygame.display.init()
            screen = pygame.display.set_mode(size, flags)
        except pygame.error:
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode(previous_size, previous_flags)
            pygame.display.set_caption(self.title)
            raise
        self.screen = screen
        pygame.display.set_caption(self.title)
        self.window_width, self.window_height = screen.get_size()
        self.resolution_index = index
        self.fullscreen = fullscreen

    def to_virtual_position(self, position: tuple[int, int]) -> tuple[int, int]:
        width, height = self.screen.get_size()
        x, y = position
        return (
            int(x * self.virtual_width / width),
            int(y * self.virtual_height / height),
        )

    def update(self, dt: float) -> None:
        self.controllers.refresh()
        self.state_machine.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        self.state_machine.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "cancel" and isinstance(
            self.state_machine.current, (MainMenuState, SettingsState)
        ):
            input_id = "back"
        if input_id.startswith("keyboard_") and isinstance(
            self.state_machine.current, (MainMenuState, SettingsState)
        ):
            input_id = input_id.removeprefix("keyboard_")
        if input_id.startswith("pad_"):
            self.controllers.refresh()
            if not self.controllers.is_connected(input_data.gamepad_id):
                return
            # Los menús usan cruceta/A/B; selección y partida reciben el ID
            # original para conservar la propiedad de cada personaje.
            if isinstance(self.state_machine.current, (MainMenuState, SettingsState)):
                input_id = {
                    "pad_a": "confirm", "pad_b": "back",
                    "pad_up": "up", "pad_down": "down",
                    "pad_left": "left", "pad_right": "right",
                }.get(input_id)
                if input_id is None:
                    return
        self.state_machine.on_input(input_id, input_data)

    def quit(self) -> None:
        self.controllers.close()
        super().quit()
