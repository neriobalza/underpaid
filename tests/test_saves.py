import unittest
import pygame
from pathlib import Path
from gale.state import StateMachine, BaseState
from src.Underpaid import Underpaid
from src.states.game.PlayState import PlayState
from src.entity.Player import Player
import settings

class DummyState(BaseState):
    def enter(self, **kwargs):
        pass

class SaveTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.save_path = Path("test_save.json")
        self.tut_path = Path("test_tut.txt")
        self.game = Underpaid(game_save_path=self.save_path, tutorial_progress_path=self.tut_path)
        self.game.fonts = {
            "small": pygame.font.Font(None, 22), 
            "medium": pygame.font.Font(None, 30), 
            "large": pygame.font.Font(None, 64)
        }
        self.state_machine = StateMachine({
            "play": lambda sm: PlayState(sm, self.game),
            "game_over": lambda sm: DummyState(sm)
        })
        self.play_state = PlayState(self.state_machine, self.game)
        self.state_machine.states["play"] = self.play_state
        self.state_machine.current = self.play_state
        
        self.p1 = Player("keyboard1")
        self.p1.select(1)
        self.p2 = Player("keyboard2")
        self.p2.select(2)
        
    def tearDown(self):
        self.save_path.unlink(missing_ok=True)
        self.tut_path.unlink(missing_ok=True)

    def test_autosave_on_win(self):
        self.game.day = 1
        self.game.stars = 3
        self.play_state.enter(players={1: self.p1, 2: self.p2})
        self.play_state.room.orders = []
        
        class MockBox:
            pass
            
        self.play_state.room.delivered_orders = {1: MockBox()} 
        
        self.play_state._finish_match()
        
        self.assertTrue(self.save_path.exists())
        save_data = self.game.game_save.load()
        self.assertEqual(save_data["game"]["day"], 2)
        self.assertEqual(self.game.day, 1)
        
    def test_autosave_delete_on_lose(self):
        self.save_path.write_text("{}")
        
        self.game.day = 1
        self.game.stars = 0
        self.play_state.enter(players={1: self.p1, 2: self.p2})
        class MockBox: pass
        self.play_state.room.orders = [MockBox()]
        self.play_state.room.delivered_orders = {}
        
        self.play_state._finish_match()
        
        self.assertFalse(self.save_path.exists())
        
    def test_reset_progress(self):
        self.save_path.write_text("{}")
        self.tut_path.write_text("tutorial_completed=true")
        
        self.game.day = 2
        self.game.stars = 1
        self.game.score = 500
        
        self.game.reset_progress()
        
        self.assertEqual(self.game.day, 0)
        self.assertEqual(self.game.stars, settings.MAX_STARS)
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.save_path.exists())
        self.assertFalse(self.tut_path.exists())
