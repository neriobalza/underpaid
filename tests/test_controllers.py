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
        for facing, expected in (('left', (256, 256)), ('right', (352, 256)),
                                  ('up', (320, 192)), ('down', (320, 288))):
            with self.subTest(facing=facing):
                surface.fill((0, 0, 0, 0))
                player.facing = facing
                state.room.render_placement(surface, state.players.values())
                self.assertEqual(surface.get_bounding_rect(), pygame.Rect(*expected, 32, 32))
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
        self.assertEqual(pygame.mask.from_surface(surface).count(), 2 * (32 * 32 - 28 * 28))
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
        self.assertEqual(type(self.game.state_machine.current).__name__, 'MainMenuState')
        self.assertNotIn(state.match_clock, Timer.items)

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
