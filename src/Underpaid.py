"""Juego y máquina de estados de Underpaid."""

import pygame

from gale.game import Game
from gale.input_handler import InputData
from gale.timer import Timer

import settings
from src.states.game.MainMenuState import MainMenuState
from src.states.game.PlayState import PlayState
from src.states.game.SettingsState import SettingsState
from src.states.game.PlayerSelectState import PlayerSelectState
from src.states.game.GameOverState import GameOverState
from src.states.game.PauseState import PauseState
from src.states.game.SceneStack import SceneStack
from src.input.ControllerManager import ControllerManager
from src.TutorialProgress import TutorialProgress


class Underpaid(Game):
    def __init__(self, *args, tutorial_progress_path=None, **kwargs) -> None:
        self.closed = False
        self.back_held = False
        progress_path = tutorial_progress_path or settings.TUTORIAL_PROGRESS_PATH
        self.tutorial_progress = TutorialProgress(progress_path)
        self.tutorial_completed = self.tutorial_progress.load()
        self.tutorial_progress_error = None
        try:
            super().__init__(*args, **kwargs)
        except Exception:
            # Game registra el listener antes de ejecutar init().
            self.quit()
            pygame.quit()
            raise

    def init(self) -> None:
        self.fonts = settings.create_fonts()
        self.controllers = ControllerManager()
        self.resolution_index = settings.DEFAULT_RESOLUTION_INDEX
        self.fullscreen = False
        self.reset_score()
        if settings.FULLSCREEN:
            self.set_display(self.resolution_index, True)
        self.state_stack = SceneStack({
            "main_menu": lambda sm: MainMenuState(sm, self),
            "settings": lambda sm: SettingsState(sm, self),
            "play": lambda sm: PlayState(sm, self),
            "player_select": lambda sm: PlayerSelectState(sm, self),
            "game_over": lambda sm: GameOverState(sm, self),
        }, self.update_timer_state)
        # Las escenas conservan su API de transiciones por nombre.
        self.state_machine = self.state_stack
        self.state_machine.change("main_menu")

    def update_timer_state(self) -> None:
        if isinstance(self.state_stack.current, PlayState):
            Timer.resume()
        else:
            Timer.pause()

    def reset_score(self) -> None:
        self.stars = settings.MAX_STARS
        self.delivered = 0
        self.score = 0
        self.day = 0

    def start_game(self) -> None:
        self.reset_score()
        if self.tutorial_completed:
            self.day = 1
        self.state_machine.change("player_select")

    def start_tutorial(self) -> None:
        self.reset_score()
        self.state_machine.change("player_select")

    def mark_tutorial_completed(self) -> None:
        self.tutorial_completed = True
        self.tutorial_progress_error = None
        try:
            self.tutorial_progress.save_completed()
        except OSError as error:
            # La partida puede terminar aunque el sistema no permita escribir.
            self.tutorial_progress_error = str(error)

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
        if self.closed:
            return
        self.controllers.refresh()
        self.state_stack.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        if self.closed:
            return
        self.state_stack.render(surface)

    def on_input(self, input_id: str, input_data: InputData) -> None:
        if input_id == "back":
            if input_data.pressed and self.back_held:
                return
            self.back_held = input_data.pressed
        if (input_id.startswith("keyboard_") or input_id.startswith("keyboard1_") or input_id.startswith("keyboard2_")) and isinstance(
            self.state_machine.current, (MainMenuState, SettingsState, GameOverState, PauseState)
        ):
            action = input_id.split("_", 1)[1]
            if action in ("confirm", "cancel", "up", "down", "left", "right", "back"):
                input_id = action
        if input_id == "cancel" and isinstance(
            self.state_machine.current, (MainMenuState, SettingsState, GameOverState, PauseState)
        ):
            input_id = "back"
        if input_id.startswith("pad_"):
            self.controllers.refresh()
            if not self.controllers.is_connected(input_data.gamepad_id):
                return
            # Los menús usan cruceta/A/B; selección y partida reciben el ID
            # original para conservar la propiedad de cada personaje.
            if isinstance(self.state_machine.current, (MainMenuState, SettingsState, GameOverState, PauseState)):
                input_id = {
                    "pad_a": "confirm", "pad_b": "back",
                    "pad_up": "up", "pad_down": "down",
                    "pad_left": "left", "pad_right": "right",
                    "pad_pause": "back",
                }.get(input_id)
                if input_id is None:
                    return
        self.state_stack.on_input(input_id, input_data)

    def quit(self) -> None:
        if self.closed:
            return
        self.closed = True
        try:
            if hasattr(self, "state_stack"):
                self.state_stack.clear()
        finally:
            if hasattr(self, "controllers"):
                self.controllers.close()
            Timer.resume()
            super().quit()

    def exec(self) -> None:
        try:
            super().exec()
        finally:
            # Gale sale con SystemExit al cerrar la ventana de SDL.
            self.quit()
            pygame.quit()
