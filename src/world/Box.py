"""Objeto sólido y levantable que utiliza la vasija de 06-princess."""

import pygame

import settings


class Box:
    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        self.floor_position = self.position.copy()
        self.width = self.height = settings.TILE_RENDER_SIZE
        self.carrier = None
        tileset = settings.load_room_tileset()
        self.image = tileset.image.subsurface(tileset.rect_for(settings.POT_TILE))

    @property
    def solid(self) -> bool:
        return self.carrier is None

    @property
    def hitbox(self) -> pygame.Rect:
        return pygame.Rect(round(self.position.x), round(self.position.y), self.width, self.height)

    def render(self, surface) -> None:
        surface.blit(self.image, (round(self.position.x), round(self.position.y)))
