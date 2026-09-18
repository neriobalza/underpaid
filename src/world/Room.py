"""Almacén, inventarios y acciones para preparar y despachar pedidos."""

import math

import pygame
import json
from gale.tilemap import CollisionType, collision_type_at, load_tiled_map

import settings
from src.world.Shelf import Shelf
from src.world.Table import Table
from src.world.Box import Box
from src.world.BoxDispenser import BoxDispenser
from src.world.Order import generate_orders
from src.world.Truck import Truck

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
        self.orders = []
        self.incoming_truck = None
        self.outcoming_truck = None
        
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
                    elif layer_name == "incoming_truck":
                        if layer.get("objects"):
                            obj = layer["objects"][0]
                            tile_val = next((p["value"] for p in obj.get("properties", []) if p["name"] == "tile"), 1)
                            self.incoming_truck = Truck(
                                self.bounds.x + obj.get("x", 0), self.bounds.y + obj.get("y", 0),
                                obj.get("width", 0), obj.get("height", 0), tile_val
                            )
                    elif layer_name == "outcoming_truck":
                        if layer.get("objects"):
                            obj = layer["objects"][0]
                            tile_val = next((p["value"] for p in obj.get("properties", []) if p["name"] == "tile"), 1)
                            self.outcoming_truck = Truck(
                                self.bounds.x + obj.get("x", 0), self.bounds.y + obj.get("y", 0),
                                obj.get("width", 0), obj.get("height", 0), tile_val
                            )

        # Gale carga las posiciones y el tipo asignado desde la zona de repisas.
        self.shelves = [
            Shelf(self.bounds.x + obj.x, self.bounds.y + obj.y,
                  obj.properties.get("type", 0), obj.width, obj.height)
            for obj in self.tilemap.object_layers.get("shelfs", [])
        ]
        # Una mesa completa ocupa dos espacios de trabajo consecutivos.
        table_spaces = sorted(self.tilemap.object_layers.get("table", []), key=lambda obj: (obj.x, obj.y))
        self.tables = [
            Table(self.bounds.x + table_spaces[index].x, self.bounds.y + table_spaces[index].y,
                  2 * size, size)
            for index in range(0, len(table_spaces) - 1, 2)
        ]
        self.dispensers = [
            BoxDispenser(self.bounds.x + obj.x, self.bounds.y + obj.y,
                         obj.properties.get("box"), obj.width, obj.height)
            for obj in self.tilemap.object_layers.get("box_machine", [])
        ]

        # La sala es estática: se dibuja una vez y se reutiliza cada frame.
        self.background = pygame.Surface(self.bounds.size)
        self.background.fill(settings.BACKGROUND_COLOR)
        self.tilemap.render(self.background)

    def spawn_position(self, number: int) -> tuple[float, float]:
        fraction = 0.25 if number == 1 else 0.75
        preferred = pygame.Vector2(
            self.walkable_area.left + self.walkable_area.width * fraction,
            self.walkable_area.centery,
        )
        width, height = settings.PLAYER_COLLISION_WIDTH, settings.PLAYER_COLLISION_HEIGHT
        candidates = [
            pygame.Vector2(x + width / 2, y)
            for y in range(self.walkable_area.top, self.walkable_area.bottom - height + 1, settings.TILE_RENDER_SIZE)
            for x in range(self.walkable_area.left, self.walkable_area.right - width + 1, settings.TILE_RENDER_SIZE)
            if self.floor_contains(pygame.Rect(x, y, width, height))
            and not any(pygame.Rect(x, y, width, height).colliderect(obj.hitbox) for obj in self.obstacles if obj.solid)
        ]
        if not candidates:
            raise ValueError("El almacén no tiene un punto libre para el jugador")
        position = min(candidates, key=lambda point: point.distance_squared_to(preferred))
        return position.x, position.y

    @property
    def obstacles(self) -> list:
        return [obj for obj in self.objects if obj.table is None] + self.shelves + self.tables + self.dispensers

    def start_day(self, rng=None) -> None:
        """Genera los pedidos y exactamente sus productos en recepción."""
        orders = generate_orders(rng)
        if len({shelf.product_type for shelf in self.shelves}) != len(settings.PRODUCT_NAMES):
            raise ValueError("El almacén requiere una repisa para cada uno de los cinco productos")
        if not self.tables or {station.box_type for station in self.dispensers} != {"small", "medium"}:
            raise ValueError("El almacén requiere mesas y dispensadores de cajas pequeñas y medianas")
        width, height = settings.BOX_SIZES["large"]
        slots = [
            pygame.Rect(x, y, width, height)
            for y in range(self.unloading_area.top, self.unloading_area.bottom - height + 1, height)
            for x in range(self.unloading_area.left, self.unloading_area.right - width + 1, width)
            if self.floor_contains(pygame.Rect(x, y, width, height))
            and not any(pygame.Rect(x, y, width, height).colliderect(obj.hitbox) for obj in self.obstacles)
        ]
        if len(slots) < len(orders):
            raise ValueError("La zona de descarga no tiene espacio para los productos de la jornada")
        self.orders = orders
        self.objects = [Box(slot.x, slot.y, "large", order.requirements)
                        for slot, order in zip(slots, orders)]

    def render(self, surface: pygame.Surface) -> None:
        surface.blit(self.background, self.bounds)
        if self.incoming_truck:
            self.incoming_truck.render(surface)
        if self.outcoming_truck:
            self.outcoming_truck.render(surface)
        pygame.draw.rect(surface, settings.ACCENT_COLOR, self.dispatch_area, width=2)
        pygame.draw.rect(surface, (128, 128, 128), self.unloading_area, width=2)

    def count_deliveries(self) -> int:
        """Cada caja correcta cuenta para un único pedido pendiente."""
        return len(self.delivery_report()[0])

    def delivery_report(self) -> tuple[dict, list]:
        delivered = {}
        incorrect = []
        for box in self.objects:
            if not box.is_order or not box.solid or box.table is not None or not self.dispatch_area.contains(box.hitbox):
                continue
            order = next((order for order in self.orders
                          if order.number not in delivered and order.matches(box)), None)
            if order is None:
                incorrect.append(box)
            else:
                delivered[order.number] = box
        return delivered, incorrect

    @property
    def order_count(self) -> int:
        return len(self.orders)

    def try_lift(self, player) -> bool:
        """Busca una caja próxima delante de los pies del jugador."""
        if player.carrying is not None or player.held_product is not None:
            return False
        interaction = self.interaction_area(player)
        candidates = [obj for obj in self.objects
                      if obj.solid and obj.table is None and interaction.colliderect(obj.hitbox)]
        if not candidates:
            return False
        obj = min(candidates, key=lambda obj: pygame.Vector2(obj.hitbox.center).distance_squared_to(feet.center))
        player.lift(obj)
        return True

    def interaction_area(self, player) -> pygame.Rect:
        feet = player.hitbox
        reach = settings.TILE_RENDER_SIZE
        return {
            "left": pygame.Rect(feet.left - reach, feet.top, reach, feet.height),
            "right": pygame.Rect(feet.right, feet.top, reach, feet.height),
            "up": pygame.Rect(feet.left, feet.top - reach, feet.width, reach),
            "down": pygame.Rect(feet.left, feet.bottom, feet.width, reach),
        }[player.facing]

    def next_action(self, player) -> tuple[str, object]:
        if player.carrying is not None and player.lift_elapsed < settings.POT_LIFT_DURATION:
            return "", None
        area = self.interaction_area(player)
        nearby = sorted((obj for obj in self.obstacles if obj.solid and area.colliderect(obj.hitbox)),
                        key=lambda obj: pygame.Vector2(obj.hitbox.center).distance_squared_to(player.hitbox.center))
        for obj in nearby:
            if isinstance(obj, Shelf):
                if player.carrying is not None and player.carrying.contents.get(obj.product_type, 0):
                    return ("unload" if player.carrying.box_type == "large" else "return_contents"), obj
                if player.carrying is None:
                    if player.held_product is not None and player.held_product.product_type == obj.product_type:
                        return "return_product", obj
                    if player.held_product is None and obj.quantity > 0:
                        return "take_product", obj
            elif isinstance(obj, Table):
                if player.carrying is not None and player.carrying.is_order and obj.box is None:
                    if player.carrying.width <= obj.width and player.carrying.height <= obj.height:
                        return "put_table", obj
                if player.carrying is None and obj.box is not None:
                    if player.held_product is None:
                        return "take_table_box", obj
                    if obj.box.quantity < obj.box.capacity:
                        return "pack", obj
                    return "box_full", obj
            elif isinstance(obj, BoxDispenser):
                if player.carrying is None and player.held_product is None:
                    return "new_box", obj
            elif isinstance(obj, Box):
                if player.carrying is None and player.held_product is None:
                    return "take_box", obj
        return ("put_down", None) if player.carrying is not None else ("", None)

    def interact(self, player, players) -> bool:
        action, target = self.next_action(player)
        if action in ("unload", "return_contents"):
            box = player.carrying
            quantity = 1 if action == "unload" else box.contents[target.product_type]
            product = box.remove(target.product_type, quantity)
            target.add(product, quantity)
            if box.box_type == "large" and box.quantity == 0:
                player.put_down(box.floor_position)
                self.objects.remove(box)
        elif action == "return_product":
            target.add(player.held_product)
            player.held_product = None
        elif action == "take_product":
            player.held_product = target.remove()
        elif action == "put_table":
            box = player.carrying
            player.put_down(self.table_target(target, box).topleft)
            target.box = box
            box.table = target
        elif action == "pack":
            target.box.add(player.held_product)
            player.held_product = None
        elif action == "take_table_box":
            player.lift(target.box)
        elif action == "take_box":
            player.lift(target)
        elif action == "new_box":
            box = Box(target.position.x, target.position.y, target.box_type)
            self.objects.append(box)
            player.lift(box)
        elif action == "put_down":
            return self.try_put_down(player, players)
        else:
            return False
        return True

    def interaction_hint(self, player) -> str:
        action, target = self.next_action(player)
        if action == "unload":
            return f"Descargar {settings.PRODUCT_NAMES[target.product_type]} en esta repisa"
        if action == "take_product":
            return f"Tomar {settings.PRODUCT_NAMES[target.product_type]}"
        if action == "return_product":
            return f"Devolver {player.held_product.name}"
        if action == "return_contents":
            return f"Devolver todos: {settings.PRODUCT_NAMES[target.product_type]}"
        if action == "new_box":
            return "Tomar caja mediana" if target.box_type == "medium" else "Tomar caja pequeña"
        return {
            "put_table": "Colocar caja en mesa",
            "pack": "Empacar", "take_table_box": "Levantar caja",
            "take_box": "Levantar caja", "put_down": "Colocar caja",
            "box_full": "Caja llena: devuelve productos",
        }.get(action, "")

    def table_target(self, table, box) -> pygame.Rect:
        return pygame.Rect(table.hitbox.centerx - box.width // 2, table.hitbox.top - box.height // 2,
                           box.width, box.height)

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
        if not self.floor_contains(target):
            return False
        if any(other.solid and target.colliderect(other.hitbox) for other in self.obstacles):
            return False
        if any(target.colliderect(other.hitbox) for other in players):
            return False
        return True

    def floor_contains(self, target) -> bool:
        if not self.walkable_area.contains(target):
            return False
        # La pared superior de Tiled ocupa más de una fila. Comprobar
        # todos los tiles cubiertos por la caja, incluidas las subcasillas.
        tile_width, tile_height = self.tilemap.tile_width, self.tilemap.tile_height
        first_col = (target.left - self.bounds.left) // tile_width
        last_col = (target.right - self.bounds.left - 1) // tile_width
        first_row = (target.top - self.bounds.top) // tile_height
        last_row = (target.bottom - self.bounds.top - 1) // tile_height
        for row in range(first_row, last_row + 1):
            for col in range(first_col, last_col + 1):
                if collision_type_at(self.tilemap, "walls", row, col) == CollisionType.SOLID:
                    return False
        return True

    def render_placement(self, surface, players) -> None:
        players = tuple(players)
        for player in players:
            if player.carrying is None:
                continue
            target = self.placement_target(player)
            action, target_object = self.next_action(player)
            if action == "unload":
                color = settings.PLACEMENT_UNLOAD_COLOR
            elif action == "put_table":
                target = self.table_target(target_object, player.carrying)
                color = settings.PLACEMENT_VALID_COLOR
            else:
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
