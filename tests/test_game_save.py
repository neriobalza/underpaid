"""Persistencia de una jornada pausada y restauración desde el menú."""

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.timer import Timer

from src.Underpaid import Underpaid
from src.entity.Player import Player
from src.states.game.MainMenuState import MainMenuState
from src.states.game.PauseState import PauseState
from src.states.game.PlayState import PlayState
from src.states.game.PlayerSelectState import PlayerSelectState
from src.world.Box import Box
from src.world.Product import Product


class GameSaveTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        Timer.clear()
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.save_path = root / "saved_game.txt"
        self.progress_path = root / "tutorial_progress.txt"
        self.progress_path.write_text("tutorial_completed=true\n", encoding="utf-8")
        self.games = []

    def tearDown(self):
        for game in reversed(self.games):
            game.quit()
        Timer.clear()
        pygame.quit()

    def create_game(self):
        game = Underpaid(
            tutorial_progress_path=self.progress_path,
            game_save_path=self.save_path,
        )
        self.games.append(game)
        return game

    @staticmethod
    def players(source_1="keyboard1", source_2="keyboard2"):
        players = {1: Player(source_1), 2: Player(source_2)}
        for number, player in players.items():
            player.select(number)
        return players

    def test_pause_saves_and_new_instance_restores_complete_workday(self):
        game = self.create_game()
        game.day = 2
        game.stars = 4.5
        game.score = 350
        game.delivered = 3
        players = self.players()
        game.state_machine.change("play", players=players)
        play = game.state_machine.current
        play.active_dialog = None
        play.game_minutes = 615.5
        play.room.strategy.time = 135.5
        play.room.shelves[0].add(Product(play.room.shelves[0].product_type), 7)

        floor_box = Box(224, 256, "small", {0: 2})
        table_box = Box(0, 0, "medium", {1: 1})
        table = play.room.tables[0]
        table_box.position.update(play.room.table_target(table, table_box).topleft)
        table_box.floor_position.update(table_box.position)
        table_box.table = table
        table.box = table_box
        carried_box = Box(320, 256, "small", {2: 1})
        play.room.objects.extend([floor_box, table_box, carried_box])
        players[1].lift(carried_box)
        players[1].lift_elapsed = 0.2
        players[1].salary = 123
        players[2].salary = 177
        players[2].held_product = Product(4)

        play.room.strategy.dispatch_trucks[0]["done"] = True
        play.room.strategy.active_dispatch = True
        play.room.active_dispatch_truck_id = 1
        play.room.strategy.unloading_events[0]["done"] = True
        play.room.strategy.unloading_events[0]["spawned"] = False
        play.room.strategy.active_unloading = True

        game.state_stack.push(PauseState(game.state_machine, game), play_state=play)
        pause = game.state_stack.current
        self.assertEqual([label for label, _ in pause.menu.items],
                         ["Continuar", "Guardar y salir"])
        pause.save_and_exit()

        self.assertIsInstance(game.state_machine.current, MainMenuState)
        self.assertTrue(self.save_path.is_file())
        self.assertIn("Continuar partida",
                      [label for label, _ in game.state_machine.current.menu.items])
        game.quit()

        loaded_game = self.create_game()
        loaded_game.continue_game()
        restored = loaded_game.state_machine.current

        self.assertIsInstance(restored, PlayState)
        self.assertEqual((loaded_game.day, loaded_game.stars, loaded_game.score,
                          loaded_game.delivered), (2, 4.5, 350, 3))
        self.assertEqual(restored.game_minutes, 615.5)
        self.assertEqual(restored.room.strategy.time, 135.5)
        self.assertEqual(restored.room.shelves[0].quantity, 7)
        self.assertEqual(restored.players[1].salary, 123)
        self.assertEqual(restored.players[2].salary, 177)
        self.assertIsNotNone(restored.players[1].carrying)
        self.assertEqual(restored.players[2].held_product.product_type, 4)
        self.assertIsNotNone(restored.room.tables[0].box)
        self.assertFalse(restored.room.strategy.dispatch_trucks[0]["done"])
        self.assertFalse(restored.room.strategy.unloading_events[0]["done"])
        loaded_game._Game__update(1)
        self.assertAlmostEqual(restored.game_minutes, 616.5)
        self.assertAlmostEqual(restored.room.strategy.time, 136.5)

    def test_disconnected_saved_controls_can_be_reassigned(self):
        game = self.create_game()
        game.day = 1
        players = self.players(501, 502)
        players[1].salary = 140
        game.state_machine.change("play", players=players)
        play = game.state_machine.current
        play.active_dialog = None
        self.assertTrue(game.save_and_exit(play))
        game.state_machine.change("main_menu")
        game.quit()

        loaded_game = self.create_game()
        loaded_game.continue_game()
        selection = loaded_game.state_machine.current
        self.assertIsInstance(selection, PlayerSelectState)
        self.assertEqual(selection.players, {})

        selection.join("keyboard1")
        selection.choices["keyboard1"] = 1
        selection.confirm("keyboard1")
        selection.join("keyboard2")
        selection.choices["keyboard2"] = 2
        selection.confirm("keyboard2")

        restored = loaded_game.state_machine.current
        self.assertIsInstance(restored, PlayState)
        self.assertEqual(restored.players[1].salary, 140)
        self.assertEqual(restored.players[1].input_source, "keyboard1")
        self.assertEqual(restored.players[2].input_source, "keyboard2")

    def test_invalid_save_is_hidden_without_crashing_menu(self):
        self.save_path.write_text("{archivo dañado", encoding="utf-8")

        game = self.create_game()

        self.assertIsInstance(game.state_machine.current, MainMenuState)
        self.assertNotIn("Continuar partida",
                         [label for label, _ in game.state_machine.current.menu.items])
        self.assertIsNotNone(game.game_save_error)

    def test_save_error_keeps_pause_open_and_reports_failure(self):
        invalid_path = Path(self.directory.name) / "directory"
        invalid_path.mkdir()
        game = Underpaid(
            tutorial_progress_path=self.progress_path,
            game_save_path=invalid_path,
        )
        self.games.append(game)
        game.day = 1
        game.state_machine.change("play", players=self.players())
        play = game.state_machine.current
        play.active_dialog = None
        game.state_stack.push(PauseState(game.state_machine, game), play_state=play)
        pause = game.state_stack.current

        pause.save_and_exit()

        self.assertIs(game.state_stack.current, pause)
        self.assertEqual(pause.message, "No se pudo guardar la partida.")
        self.assertIsNotNone(game.game_save_error)

    def test_tutorial_strategy_progress_can_be_restored(self):
        game = self.create_game()
        game.day = 0
        game.state_machine.change("play", players=self.players())
        play = game.state_machine.current
        schedule = play.room.strategy
        play.active_dialog = None
        schedule.step = 3
        schedule.wait_timer = 0
        schedule.custom_hints = {1: "uno", 2: "dos"}
        schedule.moved_dirs = {1: {"up"}, 2: {"left", "right"}}

        self.assertTrue(game.save_and_exit(play))
        game.state_machine.change("main_menu")
        game.quit()

        loaded_game = self.create_game()
        loaded_game.continue_game()
        restored = loaded_game.state_machine.current.room.strategy

        self.assertEqual(restored.step, 3)
        self.assertEqual(restored.custom_hints, {1: "uno", 2: "dos"})
        self.assertEqual(restored.moved_dirs[2], {"left", "right"})


if __name__ == "__main__":
    unittest.main()
