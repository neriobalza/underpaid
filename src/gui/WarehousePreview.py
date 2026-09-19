"""Almacén animado del menú, con un empleado y su propia escena."""

from collections import deque

import pygame

import settings
from src.entity.Player import Player
from src.world.Box import Box
from src.world.Product import Product
from src.world.Room import Room


class WarehousePreview:
    def __init__(self):
        self.room = Room(1)
        self.worker = Player("keyboard1")
        self.worker.select(1)
        self.delivered_box = None
        self.table = self.room.tables[0] if self.room.tables else None
        self.shelf = next((shelf for shelf in self.room.shelves
                           if shelf.position.x >= settings.VIRTUAL_WIDTH / 2), None)
        for shelf in self.room.shelves:
            shelf.add(Product(shelf.product_type), 3)
        size = settings.TILE_RENDER_SIZE
        width, height = settings.PLAYER_COLLISION_WIDTH, settings.PLAYER_COLLISION_HEIGHT
        self.cells = {
            (col, row): pygame.Vector2(self.room.bounds.x + col * size + width / 2,
                                      self.room.bounds.y + row * size)
            for row in range(self.room.tilemap.rows)
            for col in range(self.room.tilemap.cols)
            if self._is_free(pygame.Rect(self.room.bounds.x + col * size,
                                        self.room.bounds.y + row * size, width, height))
        }
        if not self.cells:
            raise ValueError("El mapa del menú requiere espacio libre para el empleado")
        start = self._nearest(self.room.spawn_position(2))
        self.worker.position.update(self.cells[start])
        self.stops = []
        if self.table is not None and self.shelf is not None:
            table_front = self._nearest((self.table.hitbox.centerx, self.table.hitbox.top - height))
            self.stops = [
                (table_front, "pickup"),
                (self._nearest((self.room.dispatch_area.left - width / 2, self.room.dispatch_area.centery)), "deliver"),
                (self._nearest((self.shelf.hitbox.centerx, self.shelf.hitbox.bottom)), "take_product"),
                (table_front, "pack"),
            ]
        self.stop_index = 0
        self.wait_remaining = 0.0
        self.path = deque()
        self._plan_route()

    def _is_free(self, rect) -> bool:
        return self.room.floor_contains(rect) and not any(
            obj.solid and rect.colliderect(obj.hitbox) for obj in self.room.obstacles
        )

    def _nearest(self, position):
        position = pygame.Vector2(position)
        return min(self.cells, key=lambda cell: (self.cells[cell].distance_squared_to(position), cell))

    def _plan_route(self) -> None:
        if not self.stops:
            return
        start = self._nearest(self.worker.position)
        goal = self.stops[self.stop_index][0]
        queue = deque([start])
        previous = {start: None}
        while queue and goal not in previous:
            col, row = queue.popleft()
            for cell in ((col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)):
                if cell in self.cells and cell not in previous:
                    previous[cell] = (col, row)
                    queue.append(cell)
        if goal not in previous:
            # Si Tiled separa las zonas, quedarse quieto en un punto seguro.
            self.stops = []
            self.worker.stop()
            return
        route = []
        cell = goal
        while cell != start:
            route.append(self.cells[cell])
            cell = previous[cell]
        self.path = deque(reversed(route))

    def _table_box(self):
        if self.table.box is None:
            box = Box(0, 0, "medium")
            box.position.update(self.room.table_target(self.table, box).topleft)
            box.floor_position.update(box.position)
            box.table = self.table
            self.table.box = box
        return self.table.box

    def _work(self) -> None:
        action = self.stops[self.stop_index][1]
        if action == "pickup":
            self.worker.lift(self._table_box())
        elif action == "deliver":
            self.delivered_box = self.worker.carrying
            self.worker.put_down((self.room.dispatch_area.left, self.room.dispatch_area.centery))
        elif action == "take_product":
            if not self.shelf.quantity:
                self.shelf.add(Product(self.shelf.product_type), 3)
            self.worker.held_product = self.shelf.remove()
        elif action == "pack":
            self._table_box().add(self.worker.held_product)
            self.worker.held_product = None
        self.wait_remaining = 0.7
        self.stop_index = (self.stop_index + 1) % len(self.stops)

    def update(self, dt: float) -> None:
        # Acotar saltos de tiempo conserva la velocidad y evita saltarse tareas.
        remaining = min(max(dt, 0), 0.25)
        while remaining > 0 and self.stops:
            step = min(remaining, 1 / settings.FPS)
            remaining -= step
            if self.wait_remaining > 0:
                self.worker.direction.update()
                self.worker.update(step, self.room, self.room.obstacles)
                self.wait_remaining = max(0, self.wait_remaining - step)
                if self.wait_remaining == 0:
                    self._plan_route()
                continue
            if not self.path:
                self.worker.stop()
                self._work()
                continue
            movement = self.path[0] - self.worker.position
            if movement.length_squared() < 0.01:
                self.worker.position.update(self.path.popleft())
                continue
            speed = settings.PLAYER_SPEED
            if self.worker.carrying is not None:
                speed *= settings.BOX_SPEED_MULTIPLIERS[self.worker.carrying.box_type]
            self.worker.direction.update(movement.normalize() * min(0.55, movement.length() / (speed * step)))
            self.worker.update(step, self.room, self.room.obstacles)

    def render(self, surface) -> None:
        self.room.render(surface)
        entities = [obj for obj in self.room.obstacles if obj.solid] + [self.worker]
        if self.delivered_box is not None:
            entities.append(self.delivered_box)
        for entity in sorted(entities, key=lambda entity: entity.hitbox.bottom):
            entity.render(surface)
