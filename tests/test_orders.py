"""Conservación de inventario y ciclo de pedidos con los controles del juego."""

from collections import Counter
import os
import random
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_RENDER_DRIVER", "software")

import pygame
from gale.input_handler import InputHandler
from gale.timer import Timer

import settings
from src.Underpaid import Underpaid
from src.entity.Player import Player
from src.world.Box import Box
from src.world.Order import Order, generate_orders
from src.world.Product import Product
from src.world.Room import Room
from src.states.game.GameOverState import GameOverState
from src.states.game.PauseState import PauseState


class OrderTests(unittest.TestCase):
    def setUp(self):
        Timer.clear()
        self.addCleanup(Timer.clear)
        patcher = patch("pygame.joystick.get_count", return_value=0)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.game = Underpaid()
        self.addCleanup(self.game.quit)
        patcher = patch.object(self.game.controllers, "is_connected", side_effect=lambda source: source == 71)
        patcher.start()
        self.addCleanup(patcher.stop)
        players = {1: Player(settings.KEYBOARD_INPUT), 2: Player(71)}
        for number, player in players.items():
            player.select(number)
        with patch("src.world.Room.generate_orders", side_effect=lambda rng=None: generate_orders(random.Random(7))):
            self.game.state_machine.change("play", players=players)
        self.play = self.game.state_stack.current
        self.play.active_dialog = None
        self.room = self.play.room
        self.player = self.play.players[1]

    def key(self, key, pressed=True):
        InputHandler.handle_input(pygame.event.Event(
            pygame.KEYDOWN if pressed else pygame.KEYUP, key=key, mod=0, unicode="",
        ))

    def key_tap(self, key):
        self.key(key)
        self.key(key, False)

    def button(self, button, source=71):
        for event_type in (pygame.CONTROLLERBUTTONDOWN, pygame.CONTROLLERBUTTONUP):
            InputHandler.handle_input(pygame.event.Event(event_type, instance_id=source, button=button))

    def face(self, obj, player=None, below=True):
        player = player or self.player
        player.stop()
        y = obj.hitbox.bottom if below else obj.hitbox.top - settings.PLAYER_COLLISION_HEIGHT
        player.position.update(obj.hitbox.centerx, y)
        player.facing = "up" if below else "down"

    def settle(self, player=None):
        player = player or self.player
        player.update(settings.POT_LIFT_DURATION, self.room, self.room.obstacles, self.play.players.values())

    def act(self, player=None):
        self.assertTrue(self.room.interact(player or self.player, self.play.players.values()))

    def total_inventory(self):
        total = Counter()
        for box in self.room.objects:
            total.update(box.contents)
        for shelf in self.room.shelves:
            if shelf.quantity:
                total[shelf.product_type] += shelf.quantity
        for player in self.play.players.values():
            if player.held_product is not None:
                total[player.held_product.product_type] += 1
        return total

    def unload_all(self):
        for box in list(self.room.objects):
            self.player.lift(box)
            self.settle()
            for product_type, quantity in box.contents.items():
                shelf = next(shelf for shelf in self.room.shelves if shelf.product_type == product_type)
                self.face(shelf)
                for _ in range(quantity):
                    self.assertEqual(self.room.interaction_hint(self.player),
                                     f"Descargar {settings.PRODUCT_NAMES[product_type]} en esta repisa")
                    self.act()
        self.assertEqual(self.room.objects, [])

    def test_procedural_orders_have_two_to_five_products_and_individual_lists(self):
        signatures = set()
        for seed in range(100):
            orders = generate_orders(random.Random(seed))
            self.assertEqual(Counter(order.owner for order in orders), {1: 2, 2: 2})
            self.assertEqual(len({order.number for order in orders}), len(orders))
            for order in orders:
                self.assertIn(order.quantity, range(2, 6))
                self.assertTrue(set(order.requirements) <= set(range(5)))
                self.assertEqual(order.box_type, "small" if order.quantity <= 3 else "medium")
            signatures.add(tuple(tuple(sorted(order.requirements.items())) for order in orders))
        self.assertGreater(len(signatures), 90)

    def test_start_day_supplies_exact_order_inventory_at_eight_am(self):
        required = Counter()
        for order in self.room.orders:
            required.update(order.requirements)
        self.assertEqual(self.play.clock_text, "8:00 AM")
        self.assertEqual(len(self.room.objects), 4)
        self.assertEqual(self.total_inventory(), required)
        self.assertEqual({shelf.product_type for shelf in self.room.shelves}, set(range(5)))
        for box in self.room.objects:
            self.assertEqual(box.box_type, "large")
            self.assertTrue(self.room.unloading_area.contains(box.hitbox))
            self.assertTrue(self.room.floor_contains(box.hitbox))
        for player in self.play.players.values():
            self.assertTrue(self.room.floor_contains(player.hitbox))
            self.assertFalse(any(player.hitbox.colliderect(obj.hitbox) for obj in self.room.obstacles))

    def test_product_sprites_follow_the_five_frame_catalog(self):
        sheet = pygame.image.load(settings.BASE_DIR / "assets" / "graphics" / "products.png").convert_alpha()
        self.assertEqual(settings.PRODUCT_NAMES, ("Camisa", "Audífonos", "Pantalones", "Teléfono", "Zapatos"))
        for product_type in range(5):
            product = Product(product_type)
            expected = sheet.subsurface((product_type * 32, 0, 32, 32))
            self.assertEqual(pygame.image.tobytes(product.image, "RGBA"), pygame.image.tobytes(expected, "RGBA"))

    def test_container_capacity_and_invalid_removals_preserve_inventory(self):
        box = Box(0, 0, "small", {0: 2})
        for contents in ([], "camisa", 2):
            with self.assertRaises(ValueError):
                Box(0, 0, "small", contents)
        for quantity in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                box.add(Product(0), quantity)
            with self.assertRaises(ValueError):
                box.remove(0, quantity)
        with self.assertRaises(ValueError):
            box.add(Product(1), 2)
        with self.assertRaises(ValueError):
            box.remove(0, 3)
        with self.assertRaises(ValueError):
            box.remove(5)
        snapshot = box.contents
        snapshot[0] = 100
        self.assertEqual(box.contents, {0: 2})
        self.assertEqual(box.remove(0, 2).product_type, 0)
        self.assertEqual(box.quantity, 0)
        for product_type in (-1, 5, True):
            with self.assertRaises(ValueError):
                Product(product_type)
        for requirements in ({0: 1}, {0: 6}, {5: 2}, {0: True}, {0: -2}):
            with self.assertRaises(ValueError):
                Order(1, 1, requirements)

    def test_crates_unload_one_unit_at_a_time_only_into_matching_shelf(self):
        box = self.room.objects[0]
        box.add(Product(0), 2)
        initial = self.total_inventory()
        self.player.lift(box)
        self.settle()
        shelf = self.room.shelves[0]
        self.face(shelf)
        quantity = box.contents[0]
        preview = pygame.Surface((640, 480), pygame.SRCALPHA)
        self.room.render_placement(preview, self.play.players.values())
        self.assertEqual(preview.get_at(self.room.placement_target(self.player).topleft)[:3],
                         settings.PLACEMENT_UNLOAD_COLOR)
        self.act()
        self.assertEqual(shelf.quantity, 1)
        self.assertEqual(box.contents[0], quantity - 1)
        self.assertIsNone(self.player.held_product)
        wrong = next(shelf for shelf in self.room.shelves if not box.contents.get(shelf.product_type))
        self.face(wrong)
        self.assertNotEqual(self.room.next_action(self.player)[0], "unload")
        preview.fill((0, 0, 0, 0))
        self.room.render_placement(preview, self.play.players.values())
        self.assertEqual(preview.get_at(self.room.placement_target(self.player).topleft)[:3],
                         settings.PLACEMENT_INVALID_COLOR)
        self.assertEqual(wrong.quantity, 0)
        self.assertEqual(self.total_inventory(), initial)

    def test_empty_large_crates_disappear_and_inventory_is_conserved(self):
        initial = self.total_inventory()
        self.unload_all()
        self.assertEqual(self.total_inventory(), initial)
        self.assertIsNone(self.player.carrying)

    def test_only_one_product_can_be_carried_and_hand_can_return_to_shelf(self):
        self.unload_all()
        stocked = [shelf for shelf in self.room.shelves if shelf.quantity]
        shelf, other = stocked[:2]
        self.face(shelf)
        initial = self.total_inventory()
        count = shelf.quantity
        self.assertEqual(self.room.interaction_hint(self.player), f"Tomar {settings.PRODUCT_NAMES[shelf.product_type]}")
        self.act()
        self.assertEqual(shelf.quantity, count - 1)
        self.face(other)
        self.assertFalse(self.room.interact(self.player, self.play.players.values()))
        with self.assertRaises(ValueError):
            self.player.lift(Box(0, 0, "small"))
        self.face(shelf)
        self.act()
        self.assertIsNone(self.player.held_product)
        self.assertEqual(shelf.quantity, count)
        self.assertEqual(self.total_inventory(), initial)

    def test_dispenser_and_table_hold_one_box_and_pack_one_unit_per_action(self):
        self.unload_all()
        station = next(station for station in self.room.dispensers if station.box_type == "small")
        table = self.room.tables[0]
        self.face(station, below=False)
        self.act()
        box = self.player.carrying
        self.settle()
        self.face(table, below=False)
        preview = pygame.Surface((640, 480), pygame.SRCALPHA)
        self.room.render_placement(preview, self.play.players.values())
        self.assertEqual(preview.get_at(self.room.table_target(table, box).topleft)[:3], settings.PLACEMENT_VALID_COLOR)
        self.act()
        self.assertIs(table.box, box)
        self.assertIs(box.table, table)
        self.assertIsNone(self.player.carrying)
        self.assertNotIn(box, self.room.obstacles)
        shelf = next(shelf for shelf in self.room.shelves if shelf.quantity >= 2)
        for quantity in (1, 2):
            self.face(shelf)
            self.act()
            self.face(table, below=False)
            self.assertEqual(self.room.interaction_hint(self.player), "Empacar")
            self.act()
            self.assertIsNone(self.player.held_product)
            self.assertEqual(box.contents, {shelf.product_type: quantity})
        self.face(table, below=False)
        self.act()
        self.assertIs(self.player.carrying, box)
        self.assertIsNone(table.box)
        self.assertIsNone(box.table)

    def test_returning_wrong_items_removes_all_of_that_type_and_keeps_other_types(self):
        box = Box(96, 192, "medium", {0: 2, 1: 2, 2: 1})
        self.room.objects.append(box)
        self.player.lift(box)
        self.settle()
        shelf = self.room.shelves[0]
        self.face(shelf)
        initial = self.total_inventory()
        self.assertEqual(self.room.interaction_hint(self.player), "Devolver todos: Camisa")
        self.act()
        self.assertEqual(box.contents, {1: 2, 2: 1})
        self.assertEqual(shelf.quantity, 2)
        self.assertIs(self.player.carrying, box)
        self.assertEqual(self.total_inventory(), initial)

    def test_delivery_rejects_duplicates_wrong_size_missing_and_extra_products(self):
        self.room.orders = [Order(1, 1, {0: 2})]
        area = self.room.dispatch_area
        correct = Box(area.x, area.y, "small", {0: 2})
        duplicate = Box(area.x, area.y + 16, "small", {0: 2})
        wrong_size = Box(area.x, area.y + 32, "medium", {0: 2})
        extra = Box(area.x, area.y + 64, "small", {0: 2, 1: 1})
        missing = Box(area.x, area.y + 80, "small", {0: 1})
        self.room.objects = [correct, duplicate, wrong_size, extra, missing]
        matched, incorrect = self.room.delivery_report()
        self.assertEqual(matched, {1: correct})
        self.assertEqual(incorrect, [duplicate, wrong_size, extra, missing])
        self.player.lift(correct)
        self.assertEqual(self.room.delivery_report()[0], {1: duplicate})
        self.assertEqual(self.room.order_count, 1)

    def test_incorrect_deliveries_deduct_points_only_at_end_of_day(self):
        self.room.orders = [Order(1, 1, {0: 2}), Order(2, 2, {1: 4})]
        area = self.room.dispatch_area
        self.room.objects = [Box(area.x, area.y, "small", {0: 2}),
                             Box(area.x, area.y + 32, "medium", {0: 4})]
        self.assertEqual(self.game.score, 0)
        self.game._Game__update(settings.MATCH_DURATION)
        result = self.game.state_stack.current
        self.assertIsInstance(result, GameOverState)
        self.assertEqual((result.delivered, result.total, result.incorrect), (1, 2, 1))
        self.assertEqual(self.game.score, settings.POINTS_PER_ORDER - settings.INCORRECT_ORDER_PENALTY)
        self.assertEqual(self.game.stars, settings.MAX_STARS - 1)

    def test_personal_order_panels_use_q_and_x_and_keep_clock_running(self):
        self.key(pygame.K_q)
        self.key(pygame.K_q)
        self.assertEqual(self.play.order_panels, {1})
        self.key(pygame.K_q, False)
        self.button(pygame.CONTROLLER_BUTTON_X)
        self.assertEqual(self.play.order_panels, {1, 2})
        self.button(pygame.CONTROLLER_BUTTON_X, source=999)
        self.assertEqual(self.play.order_panels, {1, 2})
        self.game._Game__update(60)
        self.assertEqual(self.play.clock_text, "9:00 AM")
        surface = pygame.Surface((640, 480))
        self.game.render(surface)
        self.key_tap(pygame.K_ESCAPE)
        self.assertIsInstance(self.game.state_stack.current, PauseState)
        self.game._Game__update(60)
        self.assertEqual(self.play.clock_text, "9:00 AM")
        self.key_tap(pygame.K_ESCAPE)
        self.key_tap(pygame.K_q)
        self.assertEqual(self.play.order_panels, {2})

    def test_two_controllers_open_only_their_own_orders(self):
        first = Player(203)
        first.select(1)
        self.play.players[1] = first
        with patch.object(self.game.controllers, "is_connected", return_value=True):
            self.button(pygame.CONTROLLER_BUTTON_X, source=203)
            self.assertEqual(self.play.order_panels, {1})
            self.button(pygame.CONTROLLER_BUTTON_X, source=71)
            self.assertEqual(self.play.order_panels, {1, 2})
            self.button(pygame.CONTROLLER_BUTTON_X, source=203)
            self.assertEqual(self.play.order_panels, {2})
            self.key_tap(pygame.K_q)
            self.assertEqual(self.play.order_panels, {2})

    def test_day_rejects_missing_shelves_stations_or_delivery_space(self):
        for feature in ("shelves", "dispensers", "unloading_area"):
            room = Room()
            if feature == "shelves":
                room.shelves.pop()
            elif feature == "dispensers":
                room.dispensers = []
            else:
                room.unloading_area.size = (32, 32)
            with self.subTest(feature=feature), self.assertRaises(ValueError):
                room.start_day()
            self.assertEqual(room.objects, [])
            self.assertEqual(room.orders, [])

    def test_full_box_keeps_product_in_hand_until_returned_and_table_cannot_be_overwritten(self):
        table = self.room.tables[0]
        box = Box(96, 192, "small", {0: 3})
        self.room.objects.append(box)
        self.player.lift(box)
        self.settle()
        self.face(table, below=False)
        self.act()
        self.player.held_product = Product(1)
        self.assertEqual(self.room.interaction_hint(self.player), "Caja llena: devuelve productos")
        self.assertFalse(self.room.interact(self.player, self.play.players.values()))
        self.assertEqual(self.player.held_product.product_type, 1)
        self.assertEqual(box.contents, {0: 3})
        shelf = self.room.shelves[1]
        self.face(shelf)
        self.act()
        self.assertEqual(shelf.quantity, 1)
        other = self.play.players[2]
        station = self.room.dispensers[0]
        self.face(station, other, below=False)
        self.act(other)
        self.settle(other)
        self.face(table, other, below=False)
        self.assertFalse(self.room.interact(other, self.play.players.values()))
        self.assertIs(table.box, box)
        self.assertIsNotNone(other.carrying)

    def test_keyboard_action_and_controller_action_transfer_exactly_one_unit(self):
        shelf = self.room.shelves[0]
        shelf.add(Product(0), 3)
        self.face(shelf)
        self.key(pygame.K_RETURN)
        self.game.update(0)
        self.key(pygame.K_RETURN)
        self.game.update(0)
        self.assertEqual(shelf.quantity, 2)
        self.assertIsNotNone(self.player.held_product)
        self.key(pygame.K_RETURN, False)
        other = self.play.players[2]
        self.face(shelf, player=other)
        self.button(pygame.CONTROLLER_BUTTON_A)
        self.game.update(0)
        self.assertEqual(shelf.quantity, 1)
        self.assertEqual(other.held_product.product_type, 0)

    def test_full_workflow_finishes_early_after_both_players_orders_are_delivered(self):
        initial = self.total_inventory()
        self.unload_all()
        for index, order in enumerate(self.room.orders):
            player = self.play.players[order.owner]
            station = next(station for station in self.room.dispensers if station.box_type == order.box_type)
            table = self.room.tables[order.owner - 1]
            self.face(station, player, below=False)
            self.act(player)
            self.settle(player)
            self.face(table, player, below=False)
            self.act(player)
            for product_type, quantity in order.requirements.items():
                shelf = self.room.shelves[product_type]
                for _ in range(quantity):
                    self.face(shelf, player)
                    self.act(player)
                    self.face(table, player, below=False)
                    self.act(player)
            self.assertTrue(order.matches(table.box))
            self.act(player)
            self.settle(player)
            player.stop()
            player.position.update(self.room.dispatch_area.left - settings.PLAYER_COLLISION_WIDTH / 2,
                                   self.room.dispatch_area.top + index * 32)
            player.facing = "right"
            self.act(player)
            self.assertEqual(self.room.count_deliveries(), index + 1)
            self.assertEqual(self.total_inventory(), initial)
        self.game.update(0)
        result = self.game.state_stack.current
        self.assertIsInstance(result, GameOverState)
        self.assertEqual((result.delivered, result.total, result.incorrect), (4, 4, 0))
        self.assertEqual(self.play.clock_text, "8:00 AM")
        self.assertEqual(self.game.score, 4 * settings.POINTS_PER_ORDER)
        self.assertEqual(self.game.stars, settings.MAX_STARS)
        self.assertTrue(self.play.match_clock.to_remove)


if __name__ == "__main__":
    unittest.main()
