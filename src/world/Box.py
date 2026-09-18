"""Caja sólida y levantable para recepción de productos o pedidos."""

import pygame
from collections import Counter
from collections.abc import Mapping

import settings
from src.world.Product import Product


class Box:
    def __init__(self, x: float, y: float, box_type: str = "medium", contents=None) -> None:
        if box_type not in settings.BOX_SIZES:
            raise ValueError("Tipo de caja inválido: usa large, medium o small")
        if contents is not None and not isinstance(contents, Mapping):
            raise ValueError("El contenido de la caja debe indicar el tipo y la cantidad de cada producto")
        self.box_type = box_type
        self.position = pygame.Vector2(x, y)
        self.floor_position = self.position.copy()
        self.width, self.height = settings.BOX_SIZES[box_type]
        self.carrier = None
        self.table = None
        self.image = settings.load_box_image(box_type)
        self.label_font = pygame.font.Font(None, 16)
        self._contents = Counter()
        for product_type, quantity in (contents or {}).items():
            self.add(Product(product_type), quantity)

    @property
    def contents(self) -> Counter:
        return self._contents.copy()

    @property
    def quantity(self) -> int:
        return sum(self._contents.values())

    @property
    def capacity(self) -> int | None:
        return settings.BOX_CAPACITIES[self.box_type]

    def add(self, product: Product, quantity: int = 1) -> None:
        if not isinstance(product, Product):
            raise ValueError("La caja sólo admite productos")
        self._validate_quantity(quantity)
        if self.capacity is not None and self.quantity + quantity > self.capacity:
            raise ValueError("La caja no tiene espacio para más productos")
        self._contents[product.product_type] += quantity

    def remove(self, product_type: int, quantity: int = 1) -> Product:
        product = Product(product_type)
        self._validate_quantity(quantity)
        if self._contents[product_type] < quantity:
            raise ValueError("La caja no contiene suficientes productos de ese tipo")
        self._contents[product_type] -= quantity
        if not self._contents[product_type]:
            del self._contents[product_type]
        return product

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if type(quantity) is not int or quantity <= 0:
            raise ValueError("La cantidad debe ser un entero positivo")

    @property
    def is_order(self) -> bool:
        return self.box_type in ("medium", "small")

    @property
    def solid(self) -> bool:
        return self.carrier is None

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.position.x), round(self.position.y), self.width, self.height)

    def render(self, surface) -> None:
        surface.blit(self.image, (round(self.position.x), round(self.position.y)))
        if self.quantity:
            label = self.label_font.render(str(self.quantity), True, settings.TEXT_COLOR)
            rect = label.get_rect(midbottom=(self.hitbox.centerx, self.hitbox.bottom))
            pygame.draw.rect(surface, settings.PANEL_COLOR, rect.inflate(4, 2), border_radius=2)
            surface.blit(label, rect)
