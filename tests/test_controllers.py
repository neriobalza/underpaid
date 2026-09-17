"""Pruebas de propiedad y selección con eventos SDL y dispositivos simulados."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.input_handler import InputHandler
from gale.timer import Timer

from src.Underpaid import Underpaid
from src.states.game.PlayerSelectState import PlayerSelectState
from src.states.game.PlayState import PlayState
from src.states.game.GameOverState import GameOverState
from src.entity.Player import Player
from src.world.Box import Box
import settings


class Device:
    def __init__(self, instance_id):
        self.id = instance_id
        self.closed = False

    def get_instance_id(self):
        return self.id

    def quit(self):
        self.closed = True


class ControllerTests(unittest.TestCase):
    def setUp(self):
        Timer.clear()
        self.addCleanup(Timer.clear)
        self.devices = [Device(71), Device(203)]
        for target, replacement in (
            ("pygame.joystick.get_count", lambda: len(self.devices)),
            ("pygame.joystick.Joystick", lambda index: self.devices[index]),
            ("pygame._sdl2.controller.is_controller", lambda index: True),
            ("pygame._sdl2.controller.Controller", lambda index: self.devices[index]),
        ):
            patcher = patch(target, side_effect=replacement)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.game = Underpaid()
        self.addCleanup(self.game.quit)

    def button(self, instance_id, button=pygame.CONTROLLER_BUTTON_A, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.CONTROLLERBUTTONDOWN if pressed else pygame.CONTROLLERBUTTONUP,
            instance_id=instance_id, button=button,
        ))

    def axis(self, instance_id, value, axis=pygame.CONTROLLER_AXIS_LEFTX):
        InputHandler.handle_input(pygame.event.Event(
            pygame.CONTROLLERAXISMOTION, instance_id=instance_id,
            axis=axis, value=round(value * 32767),
        ))

    def key(self, key, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN if pressed else pygame.KEYUP,
            key=key, mod=0, unicode='',
        ))

    def key_tap(self, key):
        self.key(key)
        self.key(key, pressed=False)

    def keyboard_play(self, number=1):
        self.devices = self.devices[:1]
        self.selection()
        self.key_tap(pygame.K_RETURN)
        self.key_tap(pygame.K_LEFT if number == 1 else pygame.K_RIGHT)
        self.key_tap(pygame.K_RETURN)
        self.button(71)
        self.move_choice(71, 1 if number == 1 else -1)
        self.button(71)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        return self.game.state_machine.current

    def selection(self):
        self.button(71)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        return self.game.state_machine.current

    def move_choice(self, instance_id, value):
        self.axis(instance_id, 0)
        self.axis(instance_id, value)
        self.axis(instance_id, 0)

    def play(self, reverse=False):
        self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, 1 if reverse else -1)
        self.move_choice(203, -1 if reverse else 1)
        self.button(71)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        return self.game.state_machine.current

    def test_join_requires_a_on_selection_and_ignores_releases(self):
        state = self.selection()
        self.assertEqual(state.participants, {})
        self.axis(71, -1)
        self.button(71, pressed=False)
        self.assertEqual(state.participants, {})
        self.button(71)
        self.button(71)
        self.button(203)
        self.assertEqual(set(state.participants), {71, 203})
        self.assertEqual(state.players, {})
        self.assertTrue(all(p.position.x == 320 for p in state.participants.values()))

    def test_confirmed_side_cannot_be_taken_and_requires_b_to_change(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.button(71)
        self.move_choice(203, -1)
        self.assertEqual(state.players[1].controller_id, 71)
        self.assertIsNone(state.participants[203].number)
        self.move_choice(71, 1)
        self.assertEqual(state.players[1].controller_id, 71)
        self.assertNotIn(2, state.players)
        self.move_choice(203, 1)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)

    def test_either_controller_can_choose_either_player(self):
        state = self.play(reverse=True)
        self.assertEqual(state.players[1].controller_id, 203)
        self.assertEqual(state.players[2].controller_id, 71)

    def test_selection_ignores_drift_and_vertical_axis(self):
        state = self.selection()
        self.button(71)
        self.axis(71, 0.3)
        self.axis(71, 1, pygame.CONTROLLER_AXIS_LEFTY)
        self.assertEqual(state.players, {})

    def test_only_owner_moves_each_player_and_keyboard_does_not_move(self):
        state = self.play()
        p1, p2 = state.players[1], state.players[2]
        start1, start2 = p1.position.copy(), p2.position.copy()
        self.axis(71, 1)
        self.game.update(0.1)
        self.assertGreater(p1.position.x, start1.x)
        self.assertEqual(p2.position, start2)
        self.axis(71, 0)
        start1 = p1.position.copy()
        self.axis(203, -1, pygame.CONTROLLER_AXIS_LEFTY)
        self.game.update(0.1)
        self.assertEqual(p1.position, start1)
        self.assertLess(p2.position.y, start2.y)
        self.axis(203, 0, pygame.CONTROLLER_AXIS_LEFTY)
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN, key=pygame.K_RIGHT, mod=0, unicode='',
        ))
        start2 = p2.position.copy()
        self.game.update(0.1)
        self.assertEqual(p1.position, start1)
        self.assertEqual(p2.position, start2)

    def test_extra_or_unknown_controller_cannot_join_or_control(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.devices.append(Device(999))
        self.button(999)
        self.assertEqual(set(state.participants), {71, 203})
        self.axis(71, -1)
        self.axis(203, 1)
        self.button(71)
        self.button(203)
        players = self.game.state_machine.current.players
        positions = {n: p.position.copy() for n, p in players.items()}
        self.axis(999, 1)
        self.axis(12345, -1)
        self.game.update(0.1)
        self.assertEqual(positions, {n: p.position for n, p in players.items()})

    def test_deadzone_and_screen_boundaries(self):
        state = self.play()
        p1 = state.players[1]
        position = p1.position.copy()
        self.axis(71, 0.1)
        self.game.update(0.1)
        self.assertEqual(p1.position, position)
        self.axis(71, 1)
        self.axis(71, 1, pygame.CONTROLLER_AXIS_LEFTY)
        self.game.update(100)
        self.assertLess(p1.position.x, 640)
        self.assertLess(p1.position.y, 480)

    def test_room_uses_princess_floor_walls_and_corners(self):
        room = self.play().room
        grid = room.tilemap.get_layer('floor')
        self.assertEqual(grid[0][0], settings.TILE_TOP_LEFT_CORNER)
        self.assertEqual(grid[0][-1], settings.TILE_TOP_RIGHT_CORNER)
        self.assertEqual(grid[-1][0], settings.TILE_BOTTOM_LEFT_CORNER)
        self.assertEqual(grid[-1][-1], settings.TILE_BOTTOM_RIGHT_CORNER)
        for tile in grid[0][1:-1]:
            self.assertIn(tile, settings.TILE_TOP_WALLS)
        for tile in grid[-1][1:-1]:
            self.assertIn(tile, settings.TILE_BOTTOM_WALLS)
        for row in grid[1:-1]:
            self.assertIn(row[0], settings.TILE_LEFT_WALLS)
            self.assertIn(row[-1], settings.TILE_RIGHT_WALLS)
            for tile in row[1:-1]:
                self.assertIn(tile, settings.TILE_FLOORS)
                self.assertIsNotNone(room.tilemap.tileset_for_gid(tile))
        self.assertEqual(room.bounds, pygame.Rect(0, 32, 640, 448))

    def test_both_players_remain_inside_room_walls(self):
        state = self.play()
        bounds = state.room.walkable_area
        for player in state.players.values():
            self.assertTrue(bounds.collidepoint(player.position))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)):
                self.axis(player.controller_id, dx)
                self.axis(player.controller_id, dy, pygame.CONTROLLER_AXIS_LEFTY)
                self.game.update(100)
                self.assertTrue(bounds.contains(player.hitbox))
            self.axis(player.controller_id, 0)
            self.axis(player.controller_id, 0, pygame.CONTROLLER_AXIS_LEFTY)

    def test_players_reach_edge_floor_tiles_and_overlap_upper_wall(self):
        state = self.play()
        bounds = state.room.walkable_area
        top_wall = pygame.Rect(state.room.bounds.left, state.room.bounds.top,
                               state.room.bounds.width, settings.TILE_RENDER_SIZE)
        for player in state.players.values():
            for dx, dy, edge in ((-1, 0, 'left'), (1, 0, 'right'),
                                 (0, 1, 'bottom'), (0, -1, 'top')):
                self.axis(player.controller_id, dx)
                self.axis(player.controller_id, dy, pygame.CONTROLLER_AXIS_LEFTY)
                self.game.update(100)
                self.assertEqual(getattr(player.hitbox, edge), getattr(bounds, edge))
                self.assertTrue(bounds.contains(player.hitbox))
            frame = player.animation.get_current_frame()
            sprite_rect = frame.get_rect(center=player.position)
            visible_sprite = frame.get_bounding_rect().move(sprite_rect.topleft)
            self.assertTrue(visible_sprite.colliderect(top_wall))
            self.assertFalse(bounds.contains(sprite_rect))
            self.axis(player.controller_id, 0)
            self.axis(player.controller_id, 0, pygame.CONTROLLER_AXIS_LEFTY)

    def test_keyboard_player_can_reach_first_and_last_floor_rows(self):
        state = self.keyboard_play()
        player = state.players[1]
        bounds = state.room.walkable_area
        self.key(pygame.K_w)
        self.game.update(100)
        self.assertEqual(player.hitbox.top, bounds.top)
        self.key(pygame.K_w, pressed=False)
        self.key(pygame.K_s)
        self.game.update(100)
        self.assertEqual(player.hitbox.bottom, bounds.bottom)
        self.assertTrue(bounds.contains(player.hitbox))

    def test_room_background_is_visible_in_play(self):
        state = self.play()
        self.game._Game__render()
        background = state.room.background
        for point in ((40, 100), (320, 100), (320, 360)):
            local = (point[0] - state.room.bounds.x, point[1] - state.room.bounds.y)
            self.assertEqual(self.game.render_surface.get_at(point), background.get_at(local))

    def test_disconnect_frees_only_owner_slot_and_reconnect_requires_join(self):
        state = self.play()
        survivor = state.players[2]
        self.axis(203, 1)
        disconnected = self.devices.pop(0)
        self.game.update(0.1)
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.players, {2: survivor})
        self.assertEqual(survivor.direction.length_squared(), 0)
        self.assertTrue(disconnected.closed)
        self.devices.append(Device(407))
        self.game.update(0)
        self.axis(407, -1)
        self.assertNotIn(1, state.players)
        self.button(407)
        self.move_choice(407, 1)
        self.assertNotIn(1, state.players)
        self.move_choice(407, -1)
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)
        self.button(407)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertEqual(self.game.state_machine.current.players[1].controller_id, 407)

    def test_disconnect_waiting_controller_allows_replacement(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.devices.pop(0)
        self.devices.append(Device(407))
        self.button(407)
        self.assertEqual(set(state.participants), {203, 407})

    def test_selection_and_play_render_at_virtual_resolution(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.game._Game__render()
        self.axis(71, -1)
        self.game._Game__render()
        self.axis(203, 1)
        self.button(71)
        self.button(203)
        self.game._Game__render()
        self.assertEqual(self.game.render_surface.get_size(), (640, 480))

    def test_browsing_visits_both_characters_and_center_without_confirming(self):
        state = self.selection()
        self.button(71)
        for direction, expected in ((-1, 1), (1, None), (1, 2), (-1, None), (-1, 1)):
            self.move_choice(71, direction)
            self.assertEqual(state.choices[71], expected)
            self.assertEqual(state.players, {})
            self.assertIsNone(state.participants[71].number)

    def test_held_stick_does_not_skip_center(self):
        state = self.selection()
        self.button(71)
        self.move_choice(71, -1)
        self.axis(71, 0.8)
        self.axis(71, 0.9)
        self.axis(71, 1)
        self.assertIsNone(state.choices[71])
        self.move_choice(71, 1)
        self.assertEqual(state.choices[71], 2)

    def test_b_releases_character_and_allows_switching(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.button(71)
        self.button(203, pygame.CONTROLLER_BUTTON_B)
        self.assertIn(1, state.players)  # B only cancels its own selection.
        self.button(71, pygame.CONTROLLER_BUTTON_B, pressed=False)
        self.assertIn(1, state.players)
        self.button(71, pygame.CONTROLLER_BUTTON_B)
        self.assertEqual(state.players, {})
        self.assertIsNone(state.participants[71].number)
        self.move_choice(71, 1)
        self.assertIsNone(state.choices[71])
        self.move_choice(71, 1)
        self.assertEqual(state.choices[71], 2)
        self.button(71)
        self.move_choice(203, -1)
        self.button(203)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertEqual(self.game.state_machine.current.players[2].controller_id, 71)

    def test_two_previews_do_not_start_game_and_cannot_confirm_same_character(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.move_choice(71, -1)
        self.move_choice(203, -1)
        self.assertEqual(state.choices, {71: 1, 203: 1})
        self.assertEqual(state.players, {})
        self.button(71, pressed=False)
        self.assertEqual(state.players, {})
        self.button(71)
        self.assertIsNone(state.choices[203])
        self.button(203)
        self.assertEqual(set(state.players), {1})
        self.assertIsInstance(self.game.state_machine.current, PlayerSelectState)

    def test_play_draws_sprite_and_supports_all_movement_directions(self):
        state = self.play()
        p1 = state.players[1]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)):
            start = p1.position.copy()
            self.axis(71, dx)
            self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
            self.game.update(0.1)
            movement = p1.position - start
            self.assertEqual(movement.x > 0, dx > 0)
            self.assertEqual(movement.x < 0, dx < 0)
            self.assertEqual(movement.y > 0, dy > 0)
            self.assertEqual(movement.y < 0, dy < 0)
            # SDL representa el extremo positivo del eje como 32767/32768.
            self.assertAlmostEqual(movement.length(), settings.PLAYER_SPEED * 0.1, delta=0.001)
        surface = pygame.Surface((640, 480))
        surface.fill(settings.BACKGROUND_COLOR)
        p1.direction.update(0, 1)
        p1.update(0.01)
        p1.stop()
        p1.position.update(160, 240)
        p1.render(surface)
        expected = pygame.Surface((640, 480))
        expected.fill(settings.BACKGROUND_COLOR)
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'player_walk.png')
        expected.blit(sheet, (144, 208), pygame.Rect(0, 0, 32, 64))
        self.assertEqual(pygame.image.tobytes(surface, 'RGB'), pygame.image.tobytes(expected, 'RGB'))

    def test_walk_animation_is_independent_and_stops_in_last_direction(self):
        state = self.play()
        p1, p2 = state.players[1], state.players[2]
        self.axis(71, 1)
        self.game.update(settings.PLAYER_FRAME_INTERVAL)
        self.assertEqual(p1.facing, 'right')
        self.assertEqual(p1.animation.current_frame_index, 1)
        self.assertEqual(p2.facing, 'down')
        self.assertEqual(p2.animation.current_frame_index, 0)
        self.assertIsNot(p1.animation, p2.animation)
        self.axis(71, 0)
        self.game.update(settings.PLAYER_FRAME_INTERVAL * 2)
        self.assertEqual(p1.facing, 'right')
        self.assertEqual(p1.animation.current_frame_index, 0)

    def test_walk_uses_correct_spritesheet_row_for_each_direction(self):
        player = self.play().players[1]
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'player_walk.png')
        for dx, dy, facing, row in ((0, 1, 'down', 0), (1, 0, 'right', 1),
                                    (0, -1, 'up', 2), (-1, 0, 'left', 3)):
            self.axis(71, dx)
            self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
            self.game.update(settings.PLAYER_FRAME_INTERVAL)
            self.assertEqual(player.facing, facing)
            frame = player.animation.get_current_frame()
            expected = sheet.subsurface(pygame.Rect(32, row * 64, 32, 64))
            self.assertEqual(pygame.image.tobytes(frame, 'RGBA'), pygame.image.tobytes(expected, 'RGBA'))

    def test_enter_registers_keyboard_once_and_space_does_not_register(self):
        self.devices.clear()
        self.key_tap(pygame.K_RETURN)  # Open selection from main menu.
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.participants, {})
        self.key_tap(pygame.K_SPACE)
        self.key(pygame.K_RETURN, pressed=False)
        self.assertEqual(state.participants, {})
        self.key(pygame.K_RETURN)
        self.key(pygame.K_RETURN)  # Simulate repeated keydown while held.
        self.assertEqual(set(state.participants), {settings.KEYBOARD_INPUT})
        self.assertTrue(state.participants[settings.KEYBOARD_INPUT].uses_keyboard)
        self.assertEqual(state.players, {})

    def test_keyboard_arrows_browse_center_and_wasd_do_not_choose(self):
        state = self.selection()
        self.key_tap(pygame.K_RETURN)
        source = settings.KEYBOARD_INPUT
        self.key_tap(pygame.K_a)
        self.assertIsNone(state.choices[source])
        self.key_tap(pygame.K_LEFT)
        self.assertEqual(state.choices[source], 1)
        self.key(pygame.K_RIGHT)
        self.key(pygame.K_RIGHT)
        self.assertIsNone(state.choices[source])
        self.key(pygame.K_RIGHT, pressed=False)
        self.key_tap(pygame.K_RIGHT)
        self.assertEqual(state.choices[source], 2)
        self.assertEqual(state.players, {})

    def test_delete_cancels_only_keyboard_confirmation_and_frees_side(self):
        state = self.selection()
        self.key_tap(pygame.K_RETURN)
        self.key_tap(pygame.K_LEFT)
        self.key_tap(pygame.K_RETURN)
        self.button(71)
        self.move_choice(71, -1)
        self.assertIsNone(state.choices[71])
        self.button(71, pygame.CONTROLLER_BUTTON_B)
        self.assertIn(1, state.players)
        self.key(pygame.K_DELETE, pressed=False)
        self.assertIn(1, state.players)
        self.key_tap(pygame.K_DELETE)
        self.assertEqual(state.players, {})
        self.assertIsNone(state.participants[settings.KEYBOARD_INPUT].number)
        self.move_choice(71, -1)
        self.button(71)
        self.assertEqual(state.players[1].controller_id, 71)
        self.key_tap(pygame.K_RIGHT)
        self.key_tap(pygame.K_RIGHT)
        self.key_tap(pygame.K_RETURN)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertTrue(self.game.state_machine.current.players[2].uses_keyboard)

    def test_one_controller_and_keyboard_can_choose_either_character(self):
        for number in (1, 2):
            state = self.keyboard_play(number)
            self.assertTrue(state.players[number].uses_keyboard)
            self.assertEqual(state.players[3 - number].controller_id, 71)
            self.game.state_machine.change('main_menu')

    def test_wasd_moves_only_keyboard_player_and_release_stops_movement(self):
        state = self.keyboard_play()
        keyboard, gamepad = state.players[1], state.players[2]
        gamepad_position = gamepad.position.copy()
        for key, dx, dy in ((pygame.K_w, 0, -1), (pygame.K_a, -1, 0),
                            (pygame.K_s, 0, 1), (pygame.K_d, 1, 0)):
            position = keyboard.position.copy()
            self.key(key)
            self.game.update(0.1)
            self.assertEqual(keyboard.position - position, pygame.Vector2(dx, dy) * 18)
            self.assertEqual(gamepad.position, gamepad_position)
            self.key(key, pressed=False)
            position = keyboard.position.copy()
            self.game.update(0.1)
            self.assertEqual(keyboard.position, position)
        self.key_tap(pygame.K_RIGHT)
        self.game.update(0.1)
        self.assertEqual(keyboard.position, position)
        self.axis(71, 1)
        self.game.update(0.1)
        self.assertEqual(keyboard.position, position)
        self.assertGreater(gamepad.position.x, gamepad_position.x)

    def test_diagonal_speed_matches_axes_for_keyboard_and_controller(self):
        state = self.keyboard_play()
        dt = 0.1
        keyboard_keys = (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (-1, 1), (1, -1), (-1, -1)):
            with self.subTest(direction=(dx, dy)):
                for key in keyboard_keys:
                    self.key(key, pressed=False)
                for player in state.players.values():
                    player.position.update(320, 240)
                self.axis(71, dx)
                self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
                if dx:
                    self.key(pygame.K_d if dx > 0 else pygame.K_a)
                if dy:
                    self.key(pygame.K_s if dy > 0 else pygame.K_w)
                self.game.update(dt)
                for player in state.players.values():
                    distance = (player.position - pygame.Vector2(320, 240)).length()
                    self.assertAlmostEqual(distance, settings.PLAYER_SPEED * dt, delta=0.001)

    def test_carry_speed_by_box_type_for_keyboard_and_controller_and_restores_on_drop(self):
        state = self.keyboard_play()
        state.room.objects = []
        for box_type, speed in (('large', 90), ('medium', 120), ('small', 180)):
            for dx, dy in ((1, 0), (0, -1), (1, 1)):
                with self.subTest(box_type=box_type, direction=(dx, dy)):
                    for player in state.players.values():
                        player.stop()
                        player.position.update(320, 240)
                        player.lift(Box(64, 96, box_type))
                    self.axis(71, dx)
                    self.axis(71, dy, pygame.CONTROLLER_AXIS_LEFTY)
                    if dx:
                        self.key(pygame.K_d)
                    if dy:
                        self.key(pygame.K_s if dy > 0 else pygame.K_w)
                    self.game.update(settings.POT_LIFT_DURATION)
                    for player in state.players.values():
                        self.assertEqual(player.position, pygame.Vector2(320, 240))
                    self.game.update(0.1)
                    for player in state.players.values():
                        self.assertAlmostEqual(player.position.distance_to((320, 240)), speed * 0.1, delta=0.001)
                        position = player.position.copy()
                        player.put_down((64, 96))
                        player.update(0.1, state.room.walkable_area)
                        self.assertAlmostEqual(player.position.distance_to(position), 18, delta=0.001)

    def test_carry_slowdown_is_independent_and_preserves_analog_input(self):
        state = self.keyboard_play()
        state.room.objects = []
        keyboard, gamepad = state.players[1], state.players[2]
        keyboard.lift(Box(64, 96, 'large'))
        gamepad.lift(Box(64, 96, 'medium'))
        self.key(pygame.K_d)
        self.axis(71, 0.5)
        self.game.update(settings.POT_LIFT_DURATION)
        starts = {number: player.position.copy() for number, player in state.players.items()}
        self.game.update(0.1)
        self.assertAlmostEqual(keyboard.position.distance_to(starts[1]), 9)
        self.assertAlmostEqual(gamepad.position.distance_to(starts[2]), 6, delta=0.001)

    def test_boxes_block_every_direction_without_tunneling(self):
        state = self.play()
        obj = Box(304, 224)
        state.room.objects = [obj]
        player = state.players[1]
        cases = (
            ((240, 224), (1, 0), 'right', 'left'),
            ((400, 224), (-1, 0), 'left', 'right'),
            ((320, 144), (0, 1), 'bottom', 'top'),
            ((320, 320), (0, -1), 'top', 'bottom'),
        )
        for position, direction, player_edge, object_edge in cases:
            with self.subTest(direction=direction):
                player.position.update(position)
                self.axis(71, direction[0])
                self.axis(71, direction[1], pygame.CONTROLLER_AXIS_LEFTY)
                self.game.update(10)
                self.assertEqual(getattr(player.hitbox, player_edge), getattr(obj.hitbox, object_edge))
                self.assertFalse(player.hitbox.colliderect(obj.hitbox))

    def test_box_types_use_asset_and_fit_inside_room(self):
        state = self.play()
        filenames = {'large': 'big_box.png', 'medium': 'medium_box.png', 'small': 'small_box.png'}
        self.assertEqual([box.box_type for box in state.room.objects], ['large', 'large', 'medium', 'small'])
        for box in state.room.objects:
            sprite = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / filenames[box.box_type]).convert_alpha()
            self.assertTrue(state.room.walkable_area.contains(box.hitbox))
            self.assertEqual(box.image.get_size(), box.hitbox.size)
            expected = pygame.transform.scale(sprite, settings.BOX_SIZES[box.box_type])
            self.assertEqual(pygame.image.tobytes(box.image, 'RGBA'), pygame.image.tobytes(expected, 'RGBA'))
        with self.assertRaises(ValueError):
            Box(100, 100, 'unknown')

    def test_large_box_cannot_overlap_wall_or_obstacle_in_second_tile(self):
        state = self.play()
        player = state.players[1]
        box = Box(96, 128, 'large')
        state.room.objects = [box]
        player.lift(box)
        player.lift_elapsed = settings.POT_LIFT_DURATION
        player.position.update(327, 241)
        player.facing = 'right'
        target = state.room.placement_target(player)
        self.assertEqual(target, pygame.Rect(352, 256, 64, 64))
        self.assertTrue(state.room.can_place(player, target, state.players.values()))
        state.room.objects.append(Box(target.left + 32, target.top + 32, 'small'))
        self.assertFalse(state.room.try_put_down(player, state.players.values()))
        self.assertIs(player.carrying, box)
        state.room.objects.pop()
        player.position.x = state.room.walkable_area.right - 48
        target = state.room.placement_target(player)
        self.assertGreater(target.right, state.room.walkable_area.right)
        self.assertFalse(state.room.try_put_down(player, state.players.values()))

    def test_small_box_placement_matches_preview_in_all_directions(self):
        state = self.play()
        player = state.players[1]
        for facing in ('left', 'right', 'up', 'down'):
            with self.subTest(facing=facing):
                box = Box(96, 128, 'small')
                state.room.objects = [box]
                player.position.update(327, 241)
                player.facing = facing
                player.lift(box)
                player.lift_elapsed = settings.POT_LIFT_DURATION
                target = state.room.placement_target(player)
                self.assertEqual(target.size, (16, 16))
                self.assertFalse(target.colliderect(player.hitbox))
                surface = pygame.Surface((640, 480), pygame.SRCALPHA)
                state.room.render_placement(surface, state.players.values())
                self.assertEqual(surface.get_bounding_rect(), target)
                self.assertTrue(state.room.try_put_down(player, state.players.values()))
                self.assertEqual(box.hitbox, target)

    def test_four_small_boxes_fit_in_one_tile_using_keyboard_or_controller(self):
        state = self.keyboard_play()
        tile = pygame.Rect(320, 256, 32, 32)
        placements = (
            ((304, 248), 'right', (320, 256)),
            ((304, 264), 'right', (320, 272)),
            ((368, 248), 'left', (336, 256)),
            ((368, 264), 'left', (336, 272)),
        )
        for player in state.players.values():
            with self.subTest(input_source=player.input_source):
                state.room.objects = []
                for participant in state.players.values():
                    participant.stop()
                    participant.position.update(80, 80)
                for position, facing, destination in placements:
                    box = Box(64, 96, 'small')
                    state.room.objects.append(box)
                    player.position.update(position)
                    player.facing = facing
                    player.lift(box)
                    self.game.update(settings.POT_LIFT_DURATION)
                    target = pygame.Rect(*destination, 16, 16)
                    self.assertEqual(state.room.placement_target(player), target)
                    surface = pygame.Surface((640, 480), pygame.SRCALPHA)
                    state.room.render_placement(surface, state.players.values())
                    self.assertEqual(surface.get_bounding_rect(), target)
                    self.assertEqual(surface.get_at(destination)[:3], settings.PLACEMENT_VALID_COLOR)
                    if player.uses_keyboard:
                        self.key_tap(pygame.K_RETURN)
                    else:
                        self.button(player.controller_id, pressed=False)
                        self.button(player.controller_id)
                    self.game.update(0)
                    self.assertIsNone(player.carrying)
                    self.assertEqual(box.hitbox, target)
                self.assertEqual(sum(box.width * box.height for box in state.room.objects), tile.width * tile.height)
                for index, box in enumerate(state.room.objects):
                    self.assertTrue(tile.contains(box.hitbox))
                    self.assertFalse(any(box.hitbox.colliderect(other.hitbox)
                                         for other in state.room.objects[index + 1:]))

    def test_occupied_small_cell_blocks_small_medium_and_large_boxes(self):
        state = self.play()
        player = state.players[1]
        state.room.objects = [Box(336, 256, 'small')]
        for box_type in ('small', 'medium', 'large'):
            with self.subTest(box_type=box_type):
                box = Box(64, 96, box_type)
                player.position.update(336, 224)
                player.facing = 'down'
                player.lift(box)
                player.lift_elapsed = settings.POT_LIFT_DURATION
                target = state.room.placement_target(player)
                self.assertTrue(target.colliderect(state.room.objects[0].hitbox))
                surface = pygame.Surface((640, 480), pygame.SRCALPHA)
                state.room.render_placement(surface, state.players.values())
                self.assertEqual(surface.get_at(target.topleft)[:3], settings.PLACEMENT_INVALID_COLOR)
                self.assertFalse(state.room.try_put_down(player, state.players.values()))
                self.assertIs(player.carrying, box)
                player.clear_carrying()

    def test_large_reception_box_does_not_count_as_delivered_order(self):
        state = self.play()
        box = state.room.objects[0]
        state.room.dispatch_area.width = box.width
        box.position.update(state.room.dispatch_area.topleft)
        self.assertTrue(state.room.dispatch_area.contains(box.hitbox))
        self.assertEqual(state.room.count_deliveries(), 0)
        self.assertEqual(state.room.order_count, 2)

    def test_diagonal_movement_slides_along_box(self):
        state = self.play()
        obj = Box(304, 224)
        state.room.objects = [obj]
        player = state.players[1]
        player.position.update(288, 224)
        self.axis(71, 1)
        self.axis(71, 1, pygame.CONTROLLER_AXIS_LEFTY)
        self.game.update(0.1)
        self.assertEqual(player.position.x, 288)
        self.assertGreater(player.position.y, 224)
        self.assertFalse(player.hitbox.colliderect(obj.hitbox))

    def test_a_lifts_adjacent_box_from_all_four_directions(self):
        state = self.play()
        player = state.players[1]
        for position, facing in (((288, 224), 'right'), ((352, 224), 'left'),
                                  ((320, 192), 'down'), ((320, 256), 'up')):
            with self.subTest(facing=facing):
                obj = Box(304, 224)
                state.room.objects = [obj]
                player.position.update(position)
                player.facing = facing
                self.button(71, pressed=False)
                self.button(71)
                self.game.update(0)
                self.assertIs(player.carrying, obj)
                self.assertIs(obj.carrier, player)
                self.assertFalse(obj.solid)
                player.clear_carrying()

    def test_lifting_requires_box_in_front_and_in_reach(self):
        state = self.play()
        state.room.objects = [Box(304, 224)]
        player = state.players[1]
        for position, facing in (((288, 224), 'left'), ((240, 224), 'right')):
            player.position.update(position)
            player.facing = facing
            self.button(71, pressed=False)
            self.button(71)
            self.game.update(0)
            self.assertIsNone(player.carrying)

    def test_enter_lifts_only_keyboard_player_and_ignores_repeat_and_release(self):
        state = self.keyboard_play()
        obj = Box(304, 224)
        state.room.objects = [obj]
        keyboard, gamepad = state.players[1], state.players[2]
        keyboard.position.update(240, 224)
        keyboard.facing = 'right'
        gamepad.position.update(352, 224)
        gamepad.facing = 'left'
        self.key(pygame.K_RETURN, pressed=False)
        self.game.update(0)
        self.assertIsNone(keyboard.carrying)
        self.key(pygame.K_RETURN)
        self.game.update(0)  # Too far away on the first press.
        keyboard.position.update(288, 224)
        self.key(pygame.K_RETURN)
        self.game.update(0)
        self.assertIsNone(keyboard.carrying)
        self.key(pygame.K_RETURN, pressed=False)
        self.key_tap(pygame.K_RETURN)
        self.game.update(0)
        self.assertIs(keyboard.carrying, obj)
        self.assertIsNone(gamepad.carrying)

    def test_same_box_cannot_be_lifted_by_both_players(self):
        state = self.play()
        obj = Box(304, 224)
        state.room.objects = [obj]
        p1, p2 = state.players[1], state.players[2]
        p1.position.update(288, 224)
        p1.facing = 'right'
        p2.position.update(352, 224)
        p2.facing = 'left'
        self.button(71)
        self.button(203)
        self.game.update(0)
        self.assertIs(p1.carrying, obj)
        self.assertIsNone(p2.carrying)
        self.assertIs(obj.carrier, p1)

    def test_lift_moves_box_over_head_then_follows_player(self):
        state = self.play()
        obj = Box(304, 224)
        state.room.objects = [obj]
        player = state.players[1]
        player.position.update(288, 224)
        player.facing = 'right'
        self.button(71)
        self.game.update(0)
        self.axis(71, 1)
        self.game.update(settings.POT_LIFT_DURATION / 2)
        self.assertEqual(player.position, pygame.Vector2(288, 224))
        self.assertLess(obj.position.y, 224)
        self.game.update(settings.POT_LIFT_DURATION / 2)
        self.assertLess(obj.hitbox.bottom, player.hitbox.top)
        old_player, old_box = player.position.copy(), obj.position.copy()
        self.game.update(0.1)
        self.assertGreater(player.position.x, old_player.x)
        self.assertEqual(obj.position - old_box, player.position - old_player)
        self.assertEqual(player.animation.current_frame_index, 0)
        self.game.update(settings.PLAYER_FRAME_INTERVAL)
        self.assertNotEqual(player.animation.current_frame_index, 0)
        self.game._Game__render()

    def test_carrying_uses_raised_arms_spritesheet(self):
        state = self.play()
        player = state.players[1]
        obj = Box(304, 224)
        state.room.objects = [obj]
        player.position.update(320, 192)
        self.button(71)
        self.game.update(0)
        self.game.update(settings.POT_LIFT_DURATION)
        self.axis(71, 1)
        self.game.update(settings.PLAYER_FRAME_INTERVAL)
        self.assertEqual(player.facing, 'right')
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'player_pot_walk.png')
        expected = sheet.subsurface(pygame.Rect(32, 64, 32, 64))
        self.assertEqual(pygame.image.tobytes(player.animation.get_current_frame(), 'RGBA'),
                         pygame.image.tobytes(expected, 'RGBA'))

    def test_player_carries_one_box_and_leaving_play_clears_it(self):
        state = self.play()
        first, second = Box(304, 224), Box(304, 192)
        state.room.objects = [first, second]
        player = state.players[1]
        player.position.update(288, 224)
        player.facing = 'right'
        self.button(71)
        self.game.update(0)
        self.assertIs(player.carrying, first)
        self.assertFalse(state.room.try_lift(player))
        self.game.update(settings.POT_LIFT_DURATION)
        self.assertIs(player.carrying, first)
        self.assertIsNone(second.carrier)
        self.game.state_machine.change('main_menu')
        self.assertIsNone(player.carrying)
        self.assertTrue(first.solid)

    def test_a_places_pot_on_grid_in_all_directions_from_between_tiles(self):
        state = self.play()
        player = state.players[1]
        for facing, expected in (('left', (256, 256)), ('right', (352, 256)),
                                  ('up', (320, 192)), ('down', (320, 288))):
            with self.subTest(facing=facing):
                obj = Box(304, 224)
                state.room.objects = [obj]
                player.position.update(288, 224)
                player.lift(obj)
                self.game.update(settings.POT_LIFT_DURATION)
                player.position.update(327, 241)
                player.facing = facing
                self.button(71, pressed=False)
                self.button(71)
                self.game.update(0)
                self.assertIsNone(player.carrying)
                self.assertIsNone(obj.carrier)
                self.assertTrue(obj.solid)
                self.assertEqual(obj.position, pygame.Vector2(expected))
                self.assertEqual(obj.floor_position, obj.position)
                self.assertTrue(state.room.walkable_area.contains(obj.hitbox))
                self.assertIs(player.animation, player.animations[facing])

    def test_placement_preview_only_marks_facing_cell_while_carrying(self):
        state = self.play()
        player = state.players[1]
        surface = pygame.Surface((640, 480), pygame.SRCALPHA)
        state.room.render_placement(surface, state.players.values())
        self.assertEqual(pygame.mask.from_surface(surface).count(), 0)
        obj = state.room.objects[0]
        player.lift(obj)
        self.game.update(settings.POT_LIFT_DURATION)
        player.position.update(327, 241)
        for facing, expected in (('left', (224, 256)), ('right', (352, 256)),
                                  ('up', (320, 160)), ('down', (320, 288))):
            with self.subTest(facing=facing):
                surface.fill((0, 0, 0, 0))
                player.facing = facing
                state.room.render_placement(surface, state.players.values())
                self.assertEqual(surface.get_bounding_rect(), pygame.Rect(*expected, obj.width, obj.height))
                self.assertEqual(surface.get_at(expected)[:3], settings.PLACEMENT_VALID_COLOR)
        self.assertTrue(state.room.try_put_down(player, state.players.values()))
        surface.fill((0, 0, 0, 0))
        state.room.render_placement(surface, state.players.values())
        self.assertEqual(pygame.mask.from_surface(surface).count(), 0)

    def test_red_placement_preview_and_put_down_use_same_collision_rules(self):
        state = self.play()
        player, other = state.players[1], state.players[2]
        obj = Box(304, 224)
        state.room.objects = [obj]
        player.position.update(327, 241)
        player.facing = 'right'
        player.lift(obj)
        surface = pygame.Surface((640, 480), pygame.SRCALPHA)
        for blocker in ('lifting', 'wall', 'pot', 'player'):
            with self.subTest(blocker=blocker):
                player.position.update(327, 241)
                player.facing = 'right'
                other.position.update(464, 256)
                state.room.objects = [obj]
                player.lift_elapsed = settings.POT_LIFT_DURATION
                if blocker == 'lifting':
                    player.lift_elapsed = 0
                elif blocker == 'wall':
                    player.position.y = state.room.walkable_area.top
                    player.facing = 'up'
                elif blocker == 'pot':
                    state.room.objects.append(Box(352, 256))
                else:
                    other.position.update(368, 256)
                target = state.room.placement_target(player)
                surface.fill((0, 0, 0, 0))
                state.room.render_placement(surface, state.players.values())
                self.assertEqual(surface.get_at(target.topleft)[:3], settings.PLACEMENT_INVALID_COLOR)
                if blocker == 'wall':
                    self.game._Game__render()
                    self.assertEqual(self.game.render_surface.get_at((target.centerx, target.top))[:3],
                                     settings.PLACEMENT_INVALID_COLOR)
                self.assertFalse(state.room.try_put_down(player, state.players.values()))
                self.assertIs(player.carrying, obj)

    def test_each_carrying_player_gets_their_own_directional_preview(self):
        state = self.play()
        first, second = state.players.values()
        first.position.update(176, 160)
        second.position.update(464, 288)
        first.facing, second.facing = 'right', 'up'
        first.lift(state.room.objects[0])
        second.lift(state.room.objects[-1])
        self.game.update(settings.POT_LIFT_DURATION)
        surface = pygame.Surface((640, 480), pygame.SRCALPHA)
        state.room.render_placement(surface, state.players.values())
        self.assertEqual(pygame.mask.from_surface(surface).count(), sum(
            player.carrying.width * player.carrying.height
            - (player.carrying.width - 4) * (player.carrying.height - 4)
            for player in (first, second)
        ))
        for player in (first, second):
            target = state.room.placement_target(player)
            self.assertEqual(surface.get_at(target.topleft)[:3], settings.PLACEMENT_VALID_COLOR)

    def test_enter_places_pot_and_repeat_does_not_lift_it_again(self):
        state = self.keyboard_play()
        player = state.players[1]
        obj = Box(304, 224)
        state.room.objects = [obj]
        player.position.update(288, 224)
        player.facing = 'right'
        self.key_tap(pygame.K_RETURN)
        self.game.update(0)
        self.game.update(settings.POT_LIFT_DURATION)
        player.position.update(327, 241)
        self.key(pygame.K_RETURN)
        self.game.update(0)
        self.assertIsNone(player.carrying)
        self.assertEqual(obj.position, pygame.Vector2(352, 256))
        self.key(pygame.K_RETURN)
        self.game.update(0)
        self.assertIsNone(player.carrying)
        self.key(pygame.K_RETURN, pressed=False)
        self.key_tap(pygame.K_RETURN)
        self.game.update(0)
        self.assertIs(player.carrying, obj)

    def test_pot_cannot_be_placed_on_wall_other_pot_or_player(self):
        state = self.play()
        player, other = state.players[1], state.players[2]
        obj = Box(304, 224)
        state.room.objects = [obj]
        player.lift(obj)
        self.game.update(settings.POT_LIFT_DURATION)
        player.position.update(320, state.room.walkable_area.top)
        player.facing = 'up'
        self.button(71)
        self.game.update(0)
        self.assertIs(player.carrying, obj)
        player.position.update(327, 241)
        player.facing = 'right'
        state.room.objects.append(Box(343, 241))
        self.button(71, pressed=False)
        self.button(71)
        self.game.update(0)
        self.assertIs(player.carrying, obj)
        state.room.objects.pop()
        other.position.update(359, 241)
        self.button(71, pressed=False)
        self.button(71)
        self.game.update(0)
        self.assertIs(player.carrying, obj)
        self.assertFalse(obj.solid)

    def test_placed_pot_blocks_movement_and_other_player_can_lift_it(self):
        state = self.play()
        player, other = state.players[1], state.players[2]
        obj = Box(304, 224)
        state.room.objects = [obj]
        player.lift(obj)
        self.game.update(settings.POT_LIFT_DURATION)
        player.position.update(327, 241)
        player.facing = 'right'
        self.button(71)
        self.game.update(0)
        self.axis(71, 1)
        self.game.update(0.1)
        self.assertEqual(player.position.x, 336)
        other.position.update(391, 241)
        other.facing = 'left'
        self.button(203)
        self.game.update(0)
        self.assertIs(other.carrying, obj)
        self.assertIsNone(player.carrying)
        self.assertIs(obj.carrier, other)

    def test_work_clock_advances_with_gale_timer_and_finishes_at_four_pm(self):
        state = self.play()
        self.assertEqual(state.clock_text, '8:00 AM')
        self.game._Game__update(0.5)
        self.assertEqual(state.clock_text, '8:00 AM')
        self.game._Game__update(0.5)
        self.assertEqual(state.clock_text, '8:01 AM')
        self.game._Game__update(59)
        self.assertEqual(state.clock_text, '9:00 AM')
        self.game._Game__update(180)
        self.assertEqual(state.clock_text, '12:00 PM')
        self.game._Game__update(239.5)
        self.assertIs(self.game.state_machine.current, state)
        self.assertEqual(state.clock_text, '3:59 PM')
        self.game._Game__update(0.5)
        self.assertEqual(state.clock_text, '4:00 PM')
        self.assertIsInstance(self.game.state_machine.current, GameOverState)
        self.assertEqual(self.game.stars, settings.MAX_STARS - 1)
        self.assertNotIn(state.match_clock, Timer.items)

    def test_dispatch_counts_only_placed_objects_inside_area(self):
        state = self.play()
        area = state.room.dispatch_area
        box = next(obj for obj in state.room.objects if obj.is_order)
        box.position.update(area.topleft)
        box.floor_position.update(box.position)
        self.assertEqual(state.room.count_deliveries(), 1)
        state.players[1].lift(box)
        self.assertEqual(state.room.count_deliveries(), 0)
        state.players[1].put_down((area.left - 1, area.top))
        self.assertEqual(state.room.count_deliveries(), 0)

    def test_full_delivery_keeps_stars_and_accumulates_next_day(self):
        state = self.play()
        area = state.room.dispatch_area
        for index, box in enumerate(obj for obj in state.room.objects if obj.is_order):
            box.position.update(area.left, area.top + index * settings.TILE_RENDER_SIZE)
            box.floor_position.update(box.position)
        self.game._Game__update(settings.MATCH_DURATION)
        result = self.game.state_machine.current
        self.assertIsInstance(result, GameOverState)
        self.assertEqual(result.delivered, 2)
        self.assertEqual(result.total, 2)
        self.assertEqual(self.game.delivered, 2)
        self.assertEqual(self.game.stars, settings.MAX_STARS)
        self.game._Game__render()
        self.key_tap(pygame.K_RETURN)
        self.assertIsInstance(self.game.state_machine.current, PlayState)
        self.assertEqual(self.game.day, 2)
        self.assertEqual(self.game.delivered, 2)
        self.assertEqual(self.game.state_machine.current.clock_text, '8:00 AM')

    def test_five_incomplete_days_end_game_and_new_game_resets_score(self):
        self.play()
        for day in range(1, settings.MAX_STARS + 1):
            self.game._Game__update(settings.MATCH_DURATION)
            result = self.game.state_machine.current
            self.assertIsInstance(result, GameOverState)
            self.assertEqual(self.game.day, day)
            self.assertEqual(self.game.stars, settings.MAX_STARS - day)
            if self.game.stars:
                result.next_day()
        result.next_day()
        self.assertIs(self.game.state_machine.current, result)
        self.game._Game__render()
        self.key_tap(pygame.K_RETURN)
        self.assertEqual(type(self.game.state_machine.current).__name__, 'MainMenuState')
        self.key_tap(pygame.K_RETURN)
        self.assertEqual(self.game.stars, settings.MAX_STARS)
        self.assertEqual(self.game.delivered, 0)
        self.assertEqual(self.game.day, 1)

    def test_next_day_returns_to_selection_when_controller_disconnected(self):
        self.keyboard_play()
        self.game._Game__update(settings.MATCH_DURATION)
        self.devices.clear()
        self.game.controllers.refresh()
        self.game.state_machine.current.next_day()
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(set(state.participants), {settings.KEYBOARD_INPUT})

    def test_quit_cancels_clock_releases_devices_and_unregisters_listener(self):
        state = self.play()
        state.players[1].lift(state.room.objects[0])
        self.game.quit()
        self.assertTrue(state.match_clock.to_remove)
        self.assertIsNone(state.players[1].carrying)
        self.assertNotIn(self.game, InputHandler.listeners)
        self.assertEqual(InputHandler.gamepads, {})
        self.assertTrue(all(device.closed for device in self.devices))
        self.game.quit()

    def test_window_close_cleans_up_even_when_gale_raises_system_exit(self):
        state = self.play()
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        with self.assertRaises(SystemExit):
            self.game.exec()
        self.assertTrue(state.match_clock.to_remove)
        self.assertNotIn(self.game, InputHandler.listeners)
        self.assertEqual(InputHandler.gamepads, {})
        self.assertFalse(pygame.get_init())
        pygame.init()

    def test_controller_errors_do_not_break_refresh_or_cleanup(self):
        with patch('pygame.joystick.Joystick', side_effect=pygame.error('disconnected')):
            self.game.controllers.refresh()
        self.assertEqual(self.game.controllers.controllers, {})
        self.assertEqual(InputHandler.gamepads, {})
        self.game.controllers.refresh()
        with patch.object(self.devices[0], 'quit', side_effect=pygame.error('already closed')):
            self.game.controllers.close()
        self.assertEqual(self.game.controllers.controllers, {})
        self.assertEqual(InputHandler.gamepads, {})

    def test_gale_gamepads_follow_hotplug_instance_ids(self):
        self.assertEqual(set(InputHandler.gamepads), {71, 203})
        self.devices.append(Device(999))
        InputHandler.handle_input(pygame.event.Event(pygame.CONTROLLERDEVICEADDED, device_index=2))
        self.game.controllers.refresh()
        self.assertTrue(self.game.controllers.is_connected(999))
        self.assertIn(999, InputHandler.gamepads)
        self.devices.pop()
        InputHandler.handle_input(pygame.event.Event(pygame.CONTROLLERDEVICEREMOVED, instance_id=999))
        self.game.controllers.refresh()
        self.assertFalse(self.game.controllers.is_connected(999))
        self.assertNotIn(999, InputHandler.gamepads)

    def test_invalid_player_sources_and_duplicate_inputs_are_rejected(self):
        for source in (-1, 'unknown', None, True):
            with self.assertRaises(ValueError):
                Player(source)
        state = self.play()
        state.players[2].input_source = state.players[1].input_source
        with self.assertRaises(ValueError):
            self.game.state_machine.change('play', players=state.players)

    def test_failed_initialization_does_not_leave_input_listener(self):
        listeners = list(InputHandler.listeners)
        with patch('settings.create_fonts', side_effect=pygame.error('font unavailable')):
            with self.assertRaises(pygame.error):
                Underpaid()
        self.assertEqual(InputHandler.listeners, listeners)
        pygame.init()

    def test_keyboard_can_place_object_in_dispatch_using_existing_controls(self):
        state = self.keyboard_play()
        player = state.players[1]
        box = next(obj for obj in state.room.objects if obj.is_order)
        target = state.room.dispatch_area
        player.position.update(target.left - settings.PLAYER_COLLISION_WIDTH / 2,
                               target.top)
        player.facing = 'right'
        player.lift(box)
        self.game.update(settings.POT_LIFT_DURATION)
        self.key_tap(pygame.K_RETURN)
        self.game.update(0)
        self.assertIsNone(player.carrying)
        self.assertTrue(target.contains(box.hitbox))
        self.game._Game__update(settings.MATCH_DURATION)
        self.assertEqual(self.game.delivered, 1)
        self.assertEqual(self.game.stars, settings.MAX_STARS - 1)

    def test_exiting_match_cancels_clock_and_new_match_starts_at_eight_am(self):
        old = self.play()
        self.game._Game__update(100)
        self.game.state_machine.change('main_menu')
        self.assertTrue(old.match_clock.to_remove)
        new = self.play()
        self.assertEqual(new.clock_text, '8:00 AM')
        self.game._Game__update(380)
        self.assertIs(self.game.state_machine.current, new)
        self.assertEqual(new.clock_text, '2:20 PM')
        self.assertNotIn(old.match_clock, Timer.items)

    def test_clock_strip_is_above_room_and_does_not_shorten_bottom_edge(self):
        state = self.play()
        self.assertEqual(state.room.bounds.top, settings.TILE_RENDER_SIZE)
        self.assertEqual(state.room.bounds.bottom, settings.VIRTUAL_HEIGHT)
        self.game._Game__render()
        surface = self.game.render_surface
        self.assertEqual(surface.get_at((10, 16))[:3], settings.CLOCK_BAR_COLOR)
        # El centro de la franja incluye los píxeles del texto del reloj.
        rect = pygame.Rect(280, 0, 80, settings.CLOCK_BAR_HEIGHT)
        self.assertTrue(any(surface.get_at((x, y))[:3] != settings.CLOCK_BAR_COLOR
                            for x in range(rect.left, rect.right)
                            for y in range(rect.top, rect.bottom)))

    def test_keyboard_diagonals_and_opposing_keys(self):
        keyboard = self.keyboard_play().players[1]
        position = keyboard.position.copy()
        self.key(pygame.K_w)
        self.key(pygame.K_d)
        self.game.update(0.1)
        movement = keyboard.position - position
        self.assertLess(movement.y, 0)
        self.assertGreater(movement.x, 0)
        self.assertAlmostEqual(movement.length(), 18)
        self.key(pygame.K_a)
        self.assertEqual(keyboard.direction.x, 0)
        self.key(pygame.K_s)
        self.assertEqual(keyboard.direction, pygame.Vector2())
        self.key(pygame.K_d, pressed=False)
        self.assertEqual(keyboard.direction.x, -1)
        self.key(pygame.K_w, pressed=False)
        self.assertEqual(keyboard.direction.y, 1)

    def test_gamepad_disconnect_preserves_keyboard_player(self):
        state = self.keyboard_play()
        keyboard = state.players[1]
        self.key(pygame.K_w)
        self.devices.clear()
        self.game.update(0.1)
        state = self.game.state_machine.current
        self.assertIsInstance(state, PlayerSelectState)
        self.assertEqual(state.players, {1: keyboard})
        self.assertEqual(keyboard.direction, pygame.Vector2())
        self.game.update(0.1)
        self.assertIn(settings.KEYBOARD_INPUT, state.participants)
        self.key_tap(pygame.K_DELETE)
        self.assertEqual(state.players, {})

    def test_keyboard_cannot_join_when_two_controllers_are_participating(self):
        state = self.selection()
        self.button(71)
        self.button(203)
        self.key_tap(pygame.K_RETURN)
        self.assertEqual(set(state.participants), {71, 203})
        self.assertNotIn(settings.KEYBOARD_INPUT, state.choices)


if __name__ == "__main__":
    unittest.main()
