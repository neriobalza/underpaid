"""Existencias, apariencia y carga de las repisas del mapa de Tiled."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

import settings
from src.world.Product import Product
from src.world.Shelf import Shelf
from src.world.Room import Room


class ShelfTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        pygame.display.set_mode((640, 480))
        self.addCleanup(pygame.quit)

    def test_inventory_switches_first_and_second_sprites_and_returns_to_empty(self):
        shelf = Shelf(32, 192, 0)
        product = Product(0, "Libro")
        sheet = pygame.image.load(settings.BASE_DIR / 'assets' / 'graphics' / 'shelf.png').convert_alpha()
        empty = sheet.subsurface(pygame.Rect(0, 0, 32, 64))
        stocked = sheet.subsurface(pygame.Rect(32, 0, 32, 64))
        self.assertIsNone(shelf.product)
        self.assertEqual(shelf.quantity, 0)
        self.assertEqual(pygame.image.tobytes(shelf.image, 'RGBA'), pygame.image.tobytes(empty, 'RGBA'))
        shelf.add(product, 3)
        self.assertIs(shelf.product, product)
        self.assertEqual(shelf.quantity, 3)
        self.assertEqual(pygame.image.tobytes(shelf.image, 'RGBA'), pygame.image.tobytes(stocked, 'RGBA'))
        self.assertIs(shelf.remove(2), product)
        self.assertEqual(shelf.quantity, 1)
        self.assertIs(shelf.image, shelf.frames[1])
        self.assertIs(shelf.remove(), product)
        self.assertEqual(shelf.quantity, 0)
        self.assertIsNone(shelf.product)
        self.assertIs(shelf.image, shelf.frames[0])

    def test_rejects_wrong_product_type_and_invalid_quantities_without_changing_stock(self):
        shelf = Shelf(32, 192, 0)
        product = Product(0)
        shelf.add(product, 2)
        for other in (Product(1), None):
            with self.assertRaises(ValueError):
                shelf.add(other)
        for quantity in (0, -1, 1.5, True):
            with self.assertRaises(ValueError):
                shelf.add(product, quantity)
            with self.assertRaises(ValueError):
                shelf.remove(quantity)
        with self.assertRaises(ValueError):
            shelf.remove(3)
        self.assertEqual(shelf.quantity, 2)
        self.assertIs(shelf.product, product)
        shelf.remove(2)
        with self.assertRaises(ValueError):
            shelf.remove()
        with self.assertRaises(ValueError):
            shelf.add(Product(1))

    def test_each_shelf_has_independent_inventory(self):
        first = Shelf(32, 192, 0)
        second = Shelf(64, 192, 0)
        first.add(Product(0))
        self.assertEqual(first.quantity, 1)
        self.assertEqual(second.quantity, 0)
        self.assertIs(second.image, second.frames[0])

    def test_map_loads_shelf_position_dimensions_and_product_type(self):
        room = Room()
        definitions = room.tilemap.object_layers['shelfs']
        self.assertEqual(len(room.shelves), len(definitions))
        self.assertGreater(len(room.shelves), 0)
        for shelf, definition in zip(room.shelves, definitions):
            self.assertEqual(shelf.position, pygame.Vector2(room.bounds.x + definition.x,
                                                          room.bounds.y + definition.y))
            self.assertEqual(shelf.hitbox.size, (definition.width, definition.height))
            self.assertEqual(shelf.product_type, definition.properties['type'])
            self.assertEqual(shelf.quantity, 0)
            self.assertIn(shelf, room.obstacles)
            surface = pygame.Surface(room.bounds.size, pygame.SRCALPHA)
            shelf.add(Product(shelf.product_type))
            shelf.render(surface)
            self.assertEqual(pygame.image.tobytes(surface.subsurface(shelf.hitbox), 'RGBA'),
                             pygame.image.tobytes(shelf.image, 'RGBA'))

    def test_invalid_product_types_and_shelf_dimensions_are_rejected(self):
        for product_type in (-1, True, '0', None):
            with self.assertRaises(ValueError):
                Product(product_type)
            with self.assertRaises(ValueError):
                Shelf(32, 192, product_type)
        for width, height in ((0, 64), (32, -1), (32.5, 64)):
            with self.assertRaises(ValueError):
                Shelf(32, 192, 0, width, height)


if __name__ == "__main__":
    unittest.main()
