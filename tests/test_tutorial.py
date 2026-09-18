import unittest
from src.Underpaid import Underpaid
from src.states.game.PlayState import PlayState
from src.world.TutorialSchedule import TutorialSchedule
from src.world.DaySchedule import DaySchedule
from src.entity.Player import Player
import pygame

class TutorialTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.font.init()
        self.game = Underpaid()
        # Mock dependencies if necessary
        self.game.fonts = {
            "small": pygame.font.Font(None, 22), 
            "medium": pygame.font.Font(None, 30), 
            "large": pygame.font.Font(None, 64)
        }
        from gale.state import StateMachine
        self.play_state = PlayState(StateMachine({}), self.game)
        
        self.p1 = Player("keyboard1")
        self.p1.select(1)
        self.p2 = Player("keyboard2")
        self.p2.select(2)

    def test_day_0_loads_tutorial_schedule_and_no_timer(self):
        self.game.day = 0
        self.play_state.enter([(1, self.p1), (2, self.p2)])
        
        self.assertIsInstance(self.play_state.room.strategy, TutorialSchedule)
        self.assertIsNone(self.play_state.match_clock)
        self.assertIsNone(self.play_state.active_dialog)

    def test_day_1_loads_day_schedule_and_timer(self):
        self.game.day = 1
        self.play_state.enter([(1, self.p1), (2, self.p2)])
        
        self.assertIsInstance(self.play_state.room.strategy, DaySchedule)
        self.assertIsNotNone(self.play_state.match_clock)
        self.assertIsNotNone(self.play_state.active_dialog)

    def test_day_0_tutorial_schedule_progression_avoids_errors(self):
        self.game.day = 0
        self.play_state.enter([(1, self.p1), (2, self.p2)])
        schedule = self.play_state.room.strategy
        
        self.assertEqual(schedule.step, 0)
        
        # Advance wait_timer
        schedule.update(1.1)
        
        # Step 1: Dialog
        self.assertEqual(schedule.step, 1)
        self.play_state.active_dialog = None  # Simulate dialog dismissed
        schedule.update(0.1)
        
        # Step 2: Dialog
        self.assertEqual(schedule.step, 2)
        self.play_state.active_dialog = None
        schedule.update(0.1)
        
        # Step 3: Movement hints
        self.assertEqual(schedule.step, 3)
        self.assertTrue(schedule.custom_hints)
        
        # Simulate movement
        for p in (self.p1, self.p2):
            for d in ["up", "down", "left", "right"]:
                p.facing = d
                p.direction = pygame.Vector2(1, 0)
                schedule.update(0.1)
                
        # Step 4: Dialog
        self.assertEqual(schedule.step, 4)
        self.play_state.active_dialog = None
        schedule.update(0.1)
        
        # Step 5: Truck wait
        self.assertEqual(schedule.step, 5)
        # Advance wait_timer
        schedule.update(0.1)
        # Truck arrived
        schedule._spawn_tutorial_boxes() # simulate callback
        
        from src.world.Product import Product
        # Now we need to simulate the shelves being stocked
        for shelf in self.play_state.room.shelves:
            if shelf.product_type == 1:
                shelf.add(Product(1), 3)
            elif shelf.product_type == 3:
                shelf.add(Product(3), 5)
                
        schedule.update(0.1)
        
        # Advance wait_timer (the 1.0 set by Step 5 condition met)
        schedule.update(1.1)
        
        self.assertEqual(schedule.step, 6)

if __name__ == '__main__':
    unittest.main()
