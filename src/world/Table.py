"""Mesa fija para la zona de trabajo de los empleados."""

import pygame

import settings


class Table:
    def __init__(self, x: float, y: float, width: int = 64, height: int = 32) -> None:
        if width <= 0 or height <= 0 or int(width) != width or int(height) != height:
            raise ValueError("Las dimensiones de la mesa deben ser píxeles enteros positivos")
        self.position = pygame.Vector2(x, y)
        self.width, self.height = int(width), int(height)
        self.image = pygame.transform.scale(settings.load_table_sprite(), (self.width, self.height))
        self.box = None

    @property
    def solid(self) -> bool:
        return True

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.position.x), round(self.position.y), self.width, self.height)

    def render(self, surface) -> None:
        surface.blit(self.image, (round(self.position.x), round(self.position.y)))
        if self.box is not None:
            self.box.render(surface)
