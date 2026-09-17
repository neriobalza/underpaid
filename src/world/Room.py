"""Sala de suelo y paredes basada en el mapa de 06-princess."""

import math
import random

import pygame
import json
from gale.tilemap import load_tiled_map

import settings
from src.world.Box import Box


class Room:
    def __init__(self) -> None:
        size = settings.TILE_RENDER_SIZE
        
        map_path = settings.BASE_DIR / "assets" / "tilemaps" / "day1.json"
        self.tilemap = load_tiled_map(str(map_path))
        
        self.bounds = pygame.Rect(
            settings.MAP_RENDER_OFFSET_X, settings.MAP_RENDER_OFFSET_Y,
            self.tilemap.pixel_width, self.tilemap.pixel_height,
        )
        self.walkable_area = self.bounds.inflate(-2 * size, -2 * size)
        # Valores por defecto
        self.dispatch_area = pygame.Rect(self.walkable_area.right - size, self.bounds.top + 5 * size, size, 4 * size)
        self.unloading_area = pygame.Rect(self.bounds.x, self.bounds.y, size, size)
        self.objects = []
        
        with open(map_path) as f:
            map_data = json.load(f)
            for layer in map_data.get("layers", []):
                layer_type = layer.get("type")
                layer_name = layer.get("name")
                if layer_type == "objectgroup":
                    if layer_name == "dispatch_area":
                        if layer.get("objects"):
                            obj = layer["objects"][0]
                            self.dispatch_area = pygame.Rect(
                                self.bounds.x + obj.get("x", 0), self.bounds.y + obj.get("y", 0),
                                obj.get("width", 0), obj.get("height", 0)
                            )
                    elif layer_name == "unloading_area":
                        if layer.get("objects"):
                            obj = layer["objects"][0]
                            self.unloading_area = pygame.Rect(
                                self.bounds.x + obj.get("x", 0), self.bounds.y + obj.get("y", 0),
                                obj.get("width", 0), obj.get("height", 0)
                            )

        # Spawneamos las cajas como estaban en la rama main
        self.objects = [
            Box(self.bounds.x + col * size, self.bounds.y + row * size, box_type)
            for col, row, box_type in (
                (3, 3, "large"), (3, self.tilemap.rows - 4, "large"),
                (self.tilemap.cols - 4, 3, "medium"),
                (self.tilemap.cols - 4, self.tilemap.rows - 4, "small"),
            )
        ]

        # La sala es estática: se dibuja una vez y se reutiliza cada frame.
        self.background = pygame.Surface(self.bounds.size)
        self.background.fill(settings.BACKGROUND_COLOR)
        self.tilemap.render(self.background)

    def spawn_position(self, number: int) -> tuple[float, float]:
        fraction = 0.25 if number == 1 else 0.75
        return (
            self.walkable_area.left + self.walkable_area.width * fraction,
            self.walkable_area.centery,
        )

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, self.bounds)
        pygame.draw.rect(surface, settings.ACCENT_COLOR, self.dispatch_area, width=2)
        pygame.draw.rect(surface, (128, 128, 128), self.unloading_area, width=2)

    def count_deliveries(self) -> int:
        """Sólo las cajas de pedidos colocadas en despacho se entregan."""
        return sum(obj.is_order and obj.solid and self.dispatch_area.contains(obj.hitbox)
                   for obj in self.objects)

    @property
    def order_count(self) -> int:
        return sum(obj.is_order for obj in self.objects)

    def try_lift(self, player) -> bool:
        """Busca una caja próxima delante de los pies del jugador."""
        if player.carrying is not None:
            return False
        feet = player.hitbox
        reach = settings.TILE_RENDER_SIZE
        interaction = {
            "left": pygame.Rect(feet.left - reach, feet.top, reach, feet.height),
            "right": pygame.Rect(feet.right, feet.top, reach, feet.height),
            "up": pygame.Rect(feet.left, feet.top - reach, feet.width, reach),
            "down": pygame.Rect(feet.left, feet.bottom, feet.width, reach),
        }[player.facing]
        candidates = [obj for obj in self.objects if obj.solid and interaction.colliderect(obj.hitbox)]
        if not candidates:
            return False
        obj = min(candidates, key=lambda obj: pygame.Vector2(obj.hitbox.center).distance_squared_to(feet.center))
        player.lift(obj)
        return True

    def interact(self, player, players) -> bool:
        if player.carrying is None:
            return self.try_lift(player)
        return self.try_put_down(player, players)

    def placement_target(self, player) -> pygame.Rect:
        """Área de la caja alineada a la cuadrícula delante de los pies."""
        feet = player.hitbox
        size = settings.TILE_RENDER_SIZE
        width, height = (size, size) if player.carrying is None else (
            player.carrying.width, player.carrying.height,
        )
        # Las cajas pequeñas usan las cuatro subcasillas de cada tile.
        size = min(size, width, height)
        col = (feet.centerx - self.bounds.left) // size
        row = (feet.centery - self.bounds.top) // size
        if player.facing == "left":
            col = (feet.left - width - self.bounds.left) // size
        elif player.facing == "right":
            col = math.ceil((feet.right - self.bounds.left) / size)
        elif player.facing == "up":
            row = (feet.top - height - self.bounds.top) // size
        else:
            row = math.ceil((feet.bottom - self.bounds.top) / size)
        return pygame.Rect(self.bounds.left + col * size,
                           self.bounds.top + row * size, width, height)

    def can_place(self, player, target, players) -> bool:
        if player.carrying is None or player.lift_elapsed < settings.POT_LIFT_DURATION:
            return False
        if not self.walkable_area.contains(target):
            return False
        if any(other.solid and target.colliderect(other.hitbox) for other in self.objects):
            return False
        if any(target.colliderect(other.hitbox) for other in players):
            return False
        return True

    def render_placement(self, surface, players) -> None:
        players = tuple(players)
        for player in players:
            if player.carrying is None:
                continue
            target = self.placement_target(player)
            color = (settings.PLACEMENT_VALID_COLOR if self.can_place(player, target, players)
                     else settings.PLACEMENT_INVALID_COLOR)
            overlay = pygame.Surface(target.size, pygame.SRCALPHA)
            overlay.fill((*color, 90))
            pygame.draw.rect(overlay, color, overlay.get_rect(), 2)
            surface.blit(overlay, target)

    def try_put_down(self, player, players) -> bool:
        """Coloca la caja en la misma área que marca la vista previa."""
        target = self.placement_target(player)
        if not self.can_place(player, target, players):
            return False
        player.put_down(target.topleft)
        return True
