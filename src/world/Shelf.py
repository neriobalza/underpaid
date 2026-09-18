"""Repisa fija con existencias de un único tipo de producto."""

import pygame

import settings
from src.world.Product import Product


class Shelf:
    def __init__(self, x: float, y: float, product_type: int,
                 width: int = 32, height: int = 64) -> None:
        if type(product_type) is not int or product_type < 0:
            raise ValueError("La repisa requiere un tipo de producto válido")
        if width <= 0 or height <= 0 or int(width) != width or int(height) != height:
            raise ValueError("Las dimensiones de la repisa deben ser píxeles enteros positivos")
        self.position = pygame.Vector2(x, y)
        self.width, self.height = int(width), int(height)
        self.product_type = product_type
        self._product: Product | None = None
        self._quantity = 0
        self.frames = tuple(
            pygame.transform.scale(frame, (self.width, self.height))
            for frame in settings.load_shelf_frames()
        )

    @property
    def product(self) -> Product | None:
        return self._product

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def image(self) -> pygame.Surface:
        return self.frames[0 if self.quantity == 0 else 1]

    @property
    def solid(self) -> bool:
        return True

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.position.x), round(self.position.y), self.width, self.height)

    def add(self, product: Product, quantity: int = 1) -> None:
        if not isinstance(product, Product) or product.product_type != self.product_type:
            raise ValueError("La repisa sólo admite su tipo de producto asignado")
        self._validate_quantity(quantity)
        if self._product is None:
            self._product = product
        self._quantity += quantity

    def remove(self, quantity: int = 1) -> Product:
        self._validate_quantity(quantity)
        if quantity > self.quantity:
            raise ValueError("No hay suficientes productos en la repisa")
        product = self._product
        self._quantity -= quantity
        if self._quantity == 0:
            self._product = None
        return product

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("La cantidad debe ser un entero positivo")

    def render(self, surface) -> None:
        surface.blit(self.image, (round(self.position.x), round(self.position.y)))
