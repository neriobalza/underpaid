"""Pruebas del progreso persistente y del acceso al tutorial."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.timer import Timer

from src.TutorialProgress import TutorialProgress
from src.Underpaid import Underpaid
from src.states.game.MainMenuState import MainMenuState
from src.states.game.PlayerSelectState import PlayerSelectState
from src.states.game.PlayState import PlayState


class TutorialProgressTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        Timer.clear()
        self.temporary_directory = TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.progress_path = Path(self.temporary_directory.name) / "tutorial_progress.txt"
        self.games = []

    def tearDown(self):
        for game in reversed(self.games):
            game.quit()
        Timer.clear()
        pygame.quit()

    def create_game(self):
        game = Underpaid(tutorial_progress_path=self.progress_path)
        self.games.append(game)
        return game

    def test_missing_or_invalid_file_keeps_tutorial_pending(self):
        progress = TutorialProgress(self.progress_path)
        self.assertFalse(progress.load())

        self.progress_path.write_text("tutorial_completed=maybe\n", encoding="utf-8")

        self.assertFalse(progress.load())

    def test_completed_value_survives_a_new_game_instance(self):
        first_game = self.create_game()
        first_game.mark_tutorial_completed()

        self.assertEqual(
            self.progress_path.read_text(encoding="utf-8"),
            "tutorial_completed=true\n",
        )

        second_game = self.create_game()

        self.assertTrue(second_game.tutorial_completed)
        self.assertIn("Tutorial", [label for label, _ in second_game.state_machine.current.menu.items])

    def test_save_failure_does_not_interrupt_the_completed_match(self):
        invalid_path = Path(self.temporary_directory.name) / "directory"
        invalid_path.mkdir()
        game = Underpaid(tutorial_progress_path=invalid_path)
        self.games.append(game)

        game.mark_tutorial_completed()

        self.assertTrue(game.tutorial_completed)
        self.assertIsNotNone(game.tutorial_progress_error)
        self.assertFalse(invalid_path.with_suffix(".tmp").exists())

    def test_play_uses_tutorial_once_and_explicit_button_can_repeat_it(self):
        game = self.create_game()
        self.assertIsInstance(game.state_machine.current, MainMenuState)
        self.assertNotIn("Tutorial", [label for label, _ in game.state_machine.current.menu.items])

        game.start_game()

        self.assertIsInstance(game.state_machine.current, PlayerSelectState)
        self.assertEqual(game.day, 0)

        game.mark_tutorial_completed()
        game.state_machine.change("main_menu")
        self.assertIn("Tutorial", [label for label, _ in game.state_machine.current.menu.items])

        game.start_game()
        self.assertEqual(game.day, 1)

        game.state_machine.change("main_menu")
        game.start_tutorial()
        self.assertEqual(game.day, 0)

    def test_finishing_tutorial_marks_progress_before_showing_results(self):
        game = SimpleNamespace(
            day=0, delivered=0, score=0, stars=5,
            mark_tutorial_completed=Mock(),
        )
        state_machine = SimpleNamespace(current=None, change=Mock())
        state = PlayState(state_machine, game)
        state_machine.current = state
        state.players = {}
        state.room = SimpleNamespace(
            order_count=2,
            delivery_report=lambda: ({1: object(), 2: object()}, []),
        )

        state._finish_match()

        game.mark_tutorial_completed.assert_called_once_with()
        state_machine.change.assert_called_once()
        self.assertEqual(state_machine.change.call_args.args[0], "game_over")


if __name__ == "__main__":
    unittest.main()
