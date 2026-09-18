import pygame
from gale.timer import Timer
from src.world.Room import Room
from src.world.Box import Box
from src.Underpaid import Underpaid
from src.states.game.PlayState import PlayState
from src.entity.Player import Player
from src.input.ControllerManager import ControllerManager

pygame.init()
Timer.clear()
game = Underpaid()
game.controllers = ControllerManager()
game.fonts = {"small": pygame.font.Font(None, 22), "medium": pygame.font.Font(None, 30), "large": pygame.font.Font(None, 64)}
game.stars = 5.0
from gale.state import StateMachine
play = PlayState(StateMachine({}), game)
play.game = game

p1 = Player("keyboard")
p1.select(1)
p1.salary = 200
p2 = Player(1)
p2.select(2)
play.enter([(1, p1), (2, p2)])

room = play.room
schedule = room.strategy

def my_on_arrive():
    print("MY ON ARRIVE CALLED!")

room.dispatch_truck.arrive(on_finish=my_on_arrive)

print("Timer.paused before:", Timer.paused)
for _ in range(30): Timer.update(0.1)
print("Timer.paused after:", Timer.paused)

