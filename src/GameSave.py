"""Snapshot JSON de la última jornada guardada."""

from collections import Counter
import json
from pathlib import Path

from gale.timer import Timer

import settings
from src.gui.FloatingDialog import FloatingDialog
from src.world.Box import Box
from src.world.Order import Order
from src.world.Product import Product


class GameSave:
    FORMAT_VERSION = 1

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        if not self.path.is_file():
            return False
        try:
            self.load()
        except (OSError, ValueError, json.JSONDecodeError):
            return False
        return True

    def save(self, game, play_state) -> None:
        data = self._snapshot(game, play_state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary_path.replace(self.path)
        except OSError:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def load(self) -> dict:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or data.get("format_version") != self.FORMAT_VERSION:
            raise ValueError("Formato de partida guardada incompatible")
        for section in ("game", "play", "players", "room", "strategy"):
            if not isinstance(data.get(section), dict):
                raise ValueError(f"Falta la sección {section} en la partida guardada")
        day = data["game"].get("day")
        if type(day) is not int or day < 0:
            raise ValueError("El día guardado no es válido")
        if set(data["players"]) != {"1", "2"}:
            raise ValueError("La partida guardada requiere dos jugadores")
        return data

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _counter_data(counter) -> dict[str, int]:
        return {str(product_type): quantity for product_type, quantity in counter.items()}

    @staticmethod
    def _counter_from(data) -> Counter:
        if not isinstance(data, dict):
            raise ValueError("Contenido de caja inválido")
        return Counter({int(product_type): int(quantity)
                        for product_type, quantity in data.items()})

    def _snapshot(self, game, play_state) -> dict:
        room = play_state.room
        boxes = []
        seen = set()

        def include(box):
            if box is not None and id(box) not in seen:
                seen.add(id(box))
                boxes.append(box)

        for box in room.objects:
            include(box)
        for table in room.tables:
            include(table.box)
        for player in play_state.players.values():
            include(player.carrying)
        for box in room.delivered_orders.values():
            include(box)
        for box in room.incorrect_boxes:
            include(box)

        box_ids = {id(box): index + 1 for index, box in enumerate(boxes)}
        box_data = []
        for box in boxes:
            box_data.append({
                "id": box_ids[id(box)],
                "box_type": box.box_type,
                "position": [box.position.x, box.position.y],
                "floor_position": [box.floor_position.x, box.floor_position.y],
                "contents": self._counter_data(box.contents),
                "last_carrier_number": box.last_carrier_number,
            })

        players = {}
        for number, player in play_state.players.items():
            players[str(number)] = {
                "input_source": player.input_source,
                "position": [player.position.x, player.position.y],
                "facing": player.facing,
                "salary": player.salary,
                "held_product": None if player.held_product is None else player.held_product.product_type,
                "carrying_box": None if player.carrying is None else box_ids[id(player.carrying)],
                "lift_elapsed": player.lift_elapsed,
                "lift_start": [player.lift_start.x, player.lift_start.y],
            }

        orders = [{
            "number": order.number,
            "owner": order.owner,
            "truck_id": order.truck_id,
            "requirements": self._counter_data(order.requirements),
        } for order in room.orders]

        dialog = None
        if getattr(play_state, "active_dialog", None) is not None:
            active_dialog = play_state.active_dialog
            dialog = {
                "text": active_dialog.full_text,
                "char_index": active_dialog.char_index,
                "is_typing": active_dialog.is_typing,
                "portrait_timer": active_dialog.portrait_timer,
                "portrait_index": active_dialog.portrait_index,
                "last_played_index": active_dialog.last_played_index,
            }

        strategy = room.strategy
        if not hasattr(strategy, "snapshot_state"):
            raise ValueError("La estrategia actual no admite guardado")

        return {
            "format_version": self.FORMAT_VERSION,
            "game": {
                "day": game.day,
                "stars": game.stars,
                "delivered": game.delivered,
                "score": game.score,
            },
            "play": {
                "game_minutes": play_state.game_minutes,
                "show_orders_panel": play_state.show_orders_panel,
                "dialog": dialog,
            },
            "players": players,
            "room": {
                "orders": orders,
                "shelves": {str(shelf.product_type): shelf.quantity for shelf in room.shelves},
                "boxes": box_data,
                "objects": [box_ids[id(box)] for box in room.objects],
                "tables": [None if table.box is None else box_ids[id(table.box)] for table in room.tables],
                "delivered_orders": {str(number): box_ids[id(box)]
                                     for number, box in room.delivered_orders.items()},
                "wrong_box_orders": sorted(room.wrong_box_orders),
                "incorrect_boxes": [box_ids[id(box)] for box in room.incorrect_boxes],
                "missed_orders": sorted(room.missed_orders),
            },
            "strategy": {
                "kind": type(strategy).__name__,
                "state": strategy.snapshot_state(),
            },
        }

    def restore(self, game, play_state, data: dict) -> None:
        room_data = data["room"]
        room = play_state.room
        game_data = data["game"]
        game.day = game_data["day"]
        game.stars = game_data["stars"]
        game.delivered = game_data["delivered"]
        game.score = game_data["score"]

        room.orders = [Order(
            order["number"], order["owner"],
            self._counter_from(order["requirements"]), order["truck_id"],
        ) for order in room_data["orders"]]

        for shelf in room.shelves:
            quantity = int(room_data["shelves"].get(str(shelf.product_type), 0))
            if quantity > 0:
                shelf.add(Product(shelf.product_type), quantity)

        boxes = {}
        for saved_box in room_data["boxes"]:
            box = Box(
                saved_box["position"][0], saved_box["position"][1],
                saved_box["box_type"], self._counter_from(saved_box["contents"]),
            )
            box.floor_position.update(saved_box["floor_position"])
            box.last_carrier_number = saved_box["last_carrier_number"]
            boxes[int(saved_box["id"])] = box

        room.objects = [boxes[int(box_id)] for box_id in room_data["objects"]]
        if len(room_data["tables"]) != len(room.tables):
            raise ValueError("La cantidad de mesas guardada no coincide con el mapa")
        for table, box_id in zip(room.tables, room_data["tables"]):
            table.box = None if box_id is None else boxes[int(box_id)]
            if table.box is not None:
                table.box.table = table

        room.delivered_orders = {
            int(number): boxes[int(box_id)]
            for number, box_id in room_data["delivered_orders"].items()
        }
        room.wrong_box_orders = set(room_data["wrong_box_orders"])
        room.incorrect_boxes = [boxes[int(box_id)] for box_id in room_data["incorrect_boxes"]]
        room.missed_orders = set(room_data["missed_orders"])

        for number, player in play_state.players.items():
            saved_player = data["players"][str(number)]
            player.position.update(saved_player["position"])
            player.facing = saved_player["facing"]
            player.salary = saved_player["salary"]
            held_product = saved_player["held_product"]
            player.held_product = None if held_product is None else Product(held_product)
            player.carrying = None
            player.lift_elapsed = float(saved_player["lift_elapsed"])
            player.lift_start.update(saved_player["lift_start"])
            box_id = saved_player["carrying_box"]
            if box_id is not None:
                box = boxes[int(box_id)]
                if box.carrier is not None:
                    raise ValueError("Una caja guardada pertenece a dos jugadores")
                box.table = None
                box.carrier = player
                player.carrying = box
                player.animation = player.carry_animations[player.facing]
            else:
                player.animation = player.animations[player.facing]
            player.animation.reset()

        strategy_data = data["strategy"]
        if type(room.strategy).__name__ != strategy_data["kind"]:
            raise ValueError("La estrategia guardada no corresponde al día")
        room.strategy.orders = room.orders
        room.strategy.restore_state(strategy_data["state"])

        play_state.game_minutes = float(data["play"]["game_minutes"])
        play_state.show_orders_panel = bool(data["play"]["show_orders_panel"])
        self._restore_dialog(play_state, data["play"]["dialog"])

        if getattr(play_state, "match_clock", None) is not None:
            play_state.match_clock.remove()
            start = settings.CLOCK_START_HOUR * 60
            end = settings.CLOCK_END_HOUR * 60
            ratio = (play_state.game_minutes - start) / (end - start)
            remaining = max(0.001, settings.MATCH_DURATION * max(0.0, 1.0 - ratio))
            play_state.match_clock = Timer.tween(
                remaining,
                [(play_state, {"game_minutes": float(end)})],
                on_finish=play_state._finish_match,
            )

    @staticmethod
    def _restore_dialog(play_state, data) -> None:
        if data is None:
            play_state.active_dialog = None
            return
        dialog = FloatingDialog(
            text=data["text"],
            font=play_state.game.fonts["medium"],
            portrait_frames=settings.load_boss_frames(),
            sound=settings.load_dialog_sound("boss"),
        )
        dialog.char_index = float(data["char_index"])
        dialog.is_typing = bool(data["is_typing"])
        dialog.portrait_timer = float(data["portrait_timer"])
        dialog.portrait_index = int(data["portrait_index"])
        dialog.last_played_index = int(data["last_played_index"])
        play_state.active_dialog = dialog
