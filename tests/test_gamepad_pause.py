import pygame
from src.Underpaid import Underpaid
from src.states.game.PlayState import PlayState
from src.entity.Player import Player

class MockInput:
    def __init__(self, pressed, gamepad_id=None):
        self.pressed = pressed
        self.gamepad_id = gamepad_id

pygame.init()
game = Underpaid()
game.init()

class MockController:
    def quit(self): pass
game.controllers.controllers[0] = MockController()

p1 = Player("keyboard1")
p1.select(1)
p2 = Player(0)
p2.select(2)

game.state_machine.change("play", players={1: p1, 2: p2})

game.on_input("pad_pause", MockInput(True, gamepad_id=0))

print("Current State:", game.state_machine.current.__class__.__name__)
game.quit()
pygame.quit()
