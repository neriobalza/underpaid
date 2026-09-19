"""Pausa, reloj y navegación usando el bucle de Gale y eventos SDL."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.input_handler import InputHandler
from gale.state import BaseState, StateStack
from gale.timer import Timer

import settings
from src.Underpaid import Underpaid
from src.entity.Player import Player
from src.states.game.GameOverState import GameOverState
from src.states.game.MainMenuState import MainMenuState
from src.states.game.PauseState import PauseState
from src.world.Box import Box


class PauseTests(unittest.TestCase):
    def setUp(self):
        Timer.clear()
        self.addCleanup(Timer.clear)
        patcher = patch("pygame.joystick.get_count", return_value=0)
        patcher.start()
        self.addCleanup(patcher.stop)
        pygame.init()
        pygame.font.init()
        self.game = Underpaid()
        self.addCleanup(self.game.quit)
        patcher = patch.object(self.game.controllers, "is_connected", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        players = {1: Player(settings.KEYBOARD_INPUT), 2: Player(71)}
        for number, player in players.items():
            player.select(number)
        self.game.state_machine.change("play", players=players)
        self.play = self.game.state_machine.current

    def key(self, key, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN if pressed else pygame.KEYUP,
            key=key, mod=0, unicode="",
        ))

    def key_tap(self, key):
        self.key(key)
        self.key(key, False)

    def button(self, button):
        for event_type in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            InputHandler.handle_input(pygame.event.Event(
                event_type, instance_id=71, button=button,
            ))

    def test_pause_uses_gale_stack_and_freezes_clock_until_same_game_resumes(self):
        self.play.active_dialog = None
        self.game._Game__update(60)
        self.assertEqual(self.play.clock_text, "9:00 AM")
        self.key_tap(pygame.K_ESCAPE)
        self.assertIsInstance(self.game.state_stack, StateStack)
        self.assertEqual(self.game.state_stack.states[0], self.play)
        self.assertIsInstance(self.game.state_stack.current, PauseState)
        self.assertTrue(Timer.paused)
        self.game._Game__update(settings.MATCH_DURATION * 2)
        self.assertEqual(self.play.clock_text, "9:00 AM")
        self.assertEqual(self.game.stars, settings.MAX_STARS)
        self.key_tap(pygame.K_ESCAPE)
        self.assertIs(self.game.state_stack.current, self.play)
        self.assertFalse(Timer.paused)
        self.game._Game__update(60)
        self.assertEqual(self.play.clock_text, "10:00 AM")

    def test_pause_works_during_intro_and_freezes_dialog(self):
        dialog = self.play.active_dialog
        self.game._Game__update(0.1)
        before = (dialog.char_index, dialog.portrait_timer, dialog.portrait_index)
        self.key_tap(pygame.K_ESCAPE)
        self.game._Game__update(10)
        self.assertEqual((dialog.char_index, dialog.portrait_timer, dialog.portrait_index), before)
        self.key_tap(pygame.K_RETURN)
        self.assertIs(self.play.active_dialog, dialog)
        self.game._Game__update(0.1)
        self.assertGreater(dialog.char_index, before[0])

    def test_pause_preserves_carried_box_and_lift_progress_and_clears_inputs(self):
        self.play.active_dialog = None
        player = self.play.players[1]
        box = Box(96, 128, "small")
        self.play.room.objects.append(box)
        player.lift(box)
        self.key(pygame.K_d)
        self.game._Game__update(0.1)
        before = (player.position.copy(), box.position.copy(), player.lift_elapsed)
        self.key_tap(pygame.K_ESCAPE)
        self.key(pygame.K_d, False)
        self.key_tap(pygame.K_d)
        self.game._Game__update(2)
        self.assertEqual((player.position, box.position, player.lift_elapsed), before)
        self.assertIs(player.carrying, box)
        self.key_tap(pygame.K_SPACE)
        self.assertIs(self.game.state_stack.current, self.play)
        self.game._Game__update(0.1)
        self.assertEqual(player.position, before[0])
        self.assertGreater(player.lift_elapsed, before[2])
        self.assertFalse(player.interact_requested)
        self.assertEqual(player.keyboard_keys, set())

    def test_held_escape_does_not_toggle_pause_repeatedly(self):
        self.key(pygame.K_ESCAPE)
        pause = self.game.state_stack.current
        self.key(pygame.K_ESCAPE)
        self.assertIs(self.game.state_stack.current, pause)
        self.key(pygame.K_ESCAPE, False)
        self.key_tap(pygame.K_ESCAPE)
        self.assertIs(self.game.state_stack.current, self.play)

    def test_controller_start_pauses_and_a_or_b_or_start_resumes(self):
        for button in (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_B,
                       pygame.CONTROLLER_BUTTON_START):
            with self.subTest(button=button):
                self.button(pygame.CONTROLLER_BUTTON_START)
                self.assertIsInstance(self.game.state_stack.current, PauseState)
                self.button(button)
                self.assertIs(self.game.state_stack.current, self.play)

    def test_mouse_button_resumes_using_scaled_coordinates(self):
        self.game.set_resolution(1)
        self.key_tap(pygame.K_ESCAPE)
        rect = self.game.state_stack.current.menu.rects[0]
        InputHandler.handle_input(pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=pygame.BUTTON_LEFT,
            pos=(rect.centerx * 3 // 2, rect.centery * 3 // 2),
        ))
        self.assertIs(self.game.state_stack.current, self.play)

    def test_main_menu_discards_pause_and_match_and_new_match_resets_clock(self):
        self.game._Game__update(30)
        self.key_tap(pygame.K_ESCAPE)
        self.key_tap(pygame.K_s)
        self.key_tap(pygame.K_RETURN)
        self.assertIsInstance(self.game.state_stack.current, MainMenuState)
        self.assertEqual(len(self.game.state_stack.states), 1)
        self.assertTrue(self.play.match_clock.to_remove)
        self.assertTrue(Timer.paused)
        self.game.state_machine.change("play", players=self.play.players)
        new = self.game.state_stack.current
        self.assertIsNot(new, self.play)
        self.assertEqual(new.clock_text, "8:00 AM")
        self.assertFalse(Timer.paused)
        self.game._Game__update(1)
        self.assertEqual(new.clock_text, "8:01 AM")

    def test_clock_finishes_only_after_remaining_play_time(self):
        self.play.active_dialog = None
        self.game._Game__update(settings.MATCH_DURATION - 1)
        self.key_tap(pygame.K_ESCAPE)
        self.game._Game__update(100)
        self.assertIsInstance(self.game.state_stack.current, PauseState)
        self.key_tap(pygame.K_ESCAPE)
        self.game._Game__update(1)
        self.assertIsInstance(self.game.state_stack.current, GameOverState)
        self.assertEqual(self.play.clock_text, "4:00 PM")
        self.assertTrue(Timer.paused)

    def test_pause_panel_is_transparent_and_world_is_rendered_below_it(self):
        self.play.active_dialog = None
        world = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT))
        self.game.render(world)
        self.key_tap(pygame.K_ESCAPE)
        paused = world.copy()
        self.game.render(paused)
        self.assertEqual(paused.get_at((40, 200)), world.get_at((40, 200)))
        point = (90, 210)
        self.assertNotEqual(paused.get_at(point), world.get_at(point))
        self.assertNotEqual(paused.get_at(point)[:3], settings.PANEL_COLOR)
        self.assertEqual(paused.get_at((110, 240))[:3], settings.ACCENT_COLOR)

    def test_quitting_paused_game_exits_all_states_and_cancels_clock(self):
        self.key_tap(pygame.K_ESCAPE)
        self.game.quit()
        self.assertEqual(self.game.state_stack.states, [])
        self.assertTrue(self.play.match_clock.to_remove)
        self.assertNotIn(self.game, InputHandler.listeners)
        self.assertFalse(Timer.paused)

    def test_unknown_transition_keeps_paused_stack_and_clock_intact(self):
        self.key_tap(pygame.K_ESCAPE)
        states = list(self.game.state_stack.states)
        with self.assertRaises(KeyError):
            self.game.state_stack.change("unknown")
        self.assertEqual(self.game.state_stack.states, states)
        self.assertTrue(Timer.paused)

    def test_failed_push_restores_play_and_timer(self):
        state = BaseState(self.game.state_stack)
        with patch.object(state, "enter", side_effect=ValueError("invalid scene")):
            with self.assertRaises(ValueError):
                self.game.state_stack.push(state)
        self.assertEqual(self.game.state_stack.states, [self.play])
        self.assertFalse(Timer.paused)


if __name__ == "__main__":
    unittest.main()
