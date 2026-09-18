import unittest
import pygame
import settings
from src.Underpaid import Underpaid
from src.states.game.PlayerSelectState import PlayerSelectState
from src.states.game.PlayState import PlayState
from src.entity.Player import Player

class MockInput:
    def __init__(self, pressed, key=None, gamepad_id=None, value=1.0):
        self.pressed = pressed
        self.key = key
        self.gamepad_id = gamepad_id
        self.value = value

class TestControllerCapabilities(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Underpaid()
        self.game.init()
        
    def test_keyboard1_capabilities(self):
        state = PlayerSelectState(self.game.state_machine, self.game)
        state.enter()
        state.on_input("keyboard1_confirm", MockInput(True))
        self.assertIn("keyboard1", state.participants)
        state.on_input("keyboard1_cancel", MockInput(True))
        self.assertNotIn("keyboard1", state.players)
        
        p1 = Player("keyboard1")
        p1.select(1)
        p2 = Player("keyboard2")
        p2.select(2)
        self.game.state_machine.change("play", players={1: p1, 2: p2})
        play = self.game.state_machine.current
        
        play.on_input("keyboard1_right", MockInput(True))
        play.players[1].update(0.1, play.room)
        self.assertGreater(play.players[1].position.x, 160)
        
        play.on_input("keyboard1_orders", MockInput(True))
        self.assertTrue(play.show_orders_panel)
        
        self.game.on_input("keyboard1_cancel", MockInput(True))
        self.assertEqual(self.game.state_machine.current.__class__.__name__, "PauseState")

    def test_keyboard2_capabilities(self):
        state = PlayerSelectState(self.game.state_machine, self.game)
        state.enter()
        state.on_input("keyboard2_confirm", MockInput(True))
        self.assertIn("keyboard2", state.participants)
        
        p1 = Player("keyboard1")
        p1.select(1)
        p2 = Player("keyboard2")
        p2.select(2)
        self.game.state_machine.change("play", players={1: p1, 2: p2})
        play = self.game.state_machine.current
        
        play.on_input("keyboard2_left", MockInput(True))
        play.players[2].update(0.1, play.room)
        self.assertLess(play.players[2].position.x, 480)
        
        play.on_input("keyboard2_orders", MockInput(True))
        self.assertTrue(play.show_orders_panel)

    def test_gamepad_capabilities(self):
        state = PlayerSelectState(self.game.state_machine, self.game)
        state.enter()
        
        class MockController:
            def quit(self): pass
        self.game.controllers.controllers[0] = MockController()
        
        state.on_input("pad_a", MockInput(True, gamepad_id=0))
        self.assertIn(0, state.participants)
        
        p1 = Player(0)
        p1.select(1)
        p2 = Player("keyboard2")
        p2.select(2)
        self.game.state_machine.change("play", players={1: p1, 2: p2})
        play = self.game.state_machine.current
        
        play.on_input("pad_x", MockInput(True, gamepad_id=0, value=1.0))
        play.players[1].update(0.1, play.room)
        self.assertGreater(play.players[1].position.x, 160)
        
        play.on_input("pad_orders", MockInput(True, gamepad_id=0))
        self.assertTrue(play.show_orders_panel)

    def tearDown(self):
        self.game.quit()
        pygame.quit()

if __name__ == '__main__':
    unittest.main()
