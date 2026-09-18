"""Puesto que proporciona cajas vacías para preparar pedidos."""

import pygame

import settings


class BoxDispenser:
    def __init__(self, x, y, box_type, width=32, height=32):
        if box_type not in ("small", "medium"):
            raise ValueError("El dispensador requiere cajas pequeñas o medianas")
        if width <= 0 or height <= 0 or int(width) != width or int(height) != height:
            raise ValueError("Las dimensiones del dispensador deben ser enteros positivos")
        self.position = pygame.Vector2(x, y)
        self.width, self.height = int(width), int(height)
        self.box_type = box_type
        self.image = settings.load_box_image(box_type)

    @property
    def solid(self) -> bool:
        return True

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.position.x), round(self.position.y), self.width, self.height)

    def render(self, surface) -> None:
        pygame.draw.rect(surface, settings.PANEL_COLOR, self.hitbox, border_radius=4)
        pygame.draw.rect(surface, settings.ACCENT_COLOR, self.hitbox, width=1, border_radius=4)
        surface.blit(self.image, self.image.get_rect(center=self.hitbox.center))
