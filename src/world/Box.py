"""Caja sólida y levantable para recepción de productos o pedidos."""

import pygame

import settings


class Box:
    def __init__(self, x: float, y: float, box_type: str = "medium") -> None:
        if box_type not in settings.BOX_SIZES:
            raise ValueError("Tipo de caja inválido: usa large, medium o small")
        self.box_type = box_type
        self.position = pygame.Vector2(x, y)
        self.floor_position = self.position.copy()
        self.width, self.height = settings.BOX_SIZES[box_type]
        self.carrier = None
        self.image = settings.load_box_image(box_type)

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
