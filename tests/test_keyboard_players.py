import unittest
import pygame
import settings
from src.Underpaid import Underpaid
from src.states.game.PlayerSelectState import PlayerSelectState

class MockInput:
    def __init__(self, pressed, key=None):
        self.pressed = pressed
        self.key = key

class TestKeyboardPlayers(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.game = Underpaid()
        self.game.init()
        self.state = PlayerSelectState(self.game.state_machine, self.game)
        self.state.enter()

    def test_both_keyboards_can_join_and_stay_connected(self):
        # Join keyboard1
        self.state.on_input("keyboard1_confirm", MockInput(pressed=True, key=pygame.K_SPACE))
        self.assertIn("keyboard1", self.state.participants)
        
        # Join keyboard2
        self.state.on_input("keyboard2_confirm", MockInput(pressed=True, key=pygame.K_RETURN))
        self.assertIn("keyboard2", self.state.participants)
        
        # Simulate an update (dt=0.1) which used to disconnect them
        self.state.update(0.1)
        
        # They should still be in participants
        self.assertIn("keyboard1", self.state.participants)
        self.assertIn("keyboard2", self.state.participants)

    def tearDown(self):
        self.game.quit()
        pygame.quit()

if __name__ == '__main__':
    unittest.main()
