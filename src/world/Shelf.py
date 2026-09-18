"""Repisa fija con existencias de un único tipo de producto."""

import pygame

import settings
from src.world.Product import Product


class Shelf:
    def __init__(self, x: float, y: float, product_type: int,
                 width: int = 32, height: int = 64) -> None:
        Product(product_type)
        if width <= 0 or height <= 0 or int(width) != width or int(height) != height:
            raise ValueError("Las dimensiones de la repisa deben ser píxeles enteros positivos")
        self.position = pygame.Vector2(x, y)
        self.width, self.height = int(width), int(height)
        self.product_type = product_type
        self.label_font = pygame.font.Font(None, 14)
        self.product_icon = pygame.transform.scale(Product(product_type).image, (16, 16))
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
        surface.blit(self.product_icon, (self.hitbox.centerx - 8, self.hitbox.top - 20))
        label = self.label_font.render(f"{settings.PRODUCT_NAMES[self.product_type]}: {self.quantity}",
                                      True, settings.TEXT_COLOR)
        rect = label.get_rect(midtop=(self.hitbox.centerx, self.hitbox.bottom + 2))
        pygame.draw.rect(surface, settings.PANEL_COLOR, rect.inflate(4, 2), border_radius=2)
        surface.blit(label, rect)
