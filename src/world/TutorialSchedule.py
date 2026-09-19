import pygame
from collections import Counter
from gale.timer import Timer
from src.world.Order import Order
from src.world.Box import Box
import settings
from src.gui.FloatingDialog import FloatingDialog

class TutorialSchedule:
    def __init__(self, room, play_state):
        self.room = room
        self.play_state = play_state
        self.custom_hints = {}
        self.dispatch_trucks = []
        self.step = 0
        
        self.moved_dirs = {1: set(), 2: set()}
        self.orders_opened = {1: False, 2: False}
        
        self.portrait_frames = settings.load_boss_frames()
        self.dialog_sound = settings.load_dialog_sound("boss")
        
        self.wait_timer = 1.0
        
    def play_dialog(self, text, frames=None):
        if frames is None:
            frames = self.portrait_frames[0]
            
        for player in self.play_state.players.values():
            player.stop()
            if hasattr(player, "active_directions"):
                player.active_directions.clear()
            player.interact_held = False
            
        self.play_state.active_dialog = FloatingDialog(
            text=text,
            font=self.play_state.game.fonts["medium"],
            portrait_frames=frames,
            sound=self.dialog_sound
        )
        
    def get_movement_hint(self, player):
        if player.input_source == "keyboard1":
            return "Usa WASD para moverte"
        elif player.input_source == "keyboard2":
            return "Usa Flechas para moverte"
        else:
            return "Usa Joystick para moverte"
            
    def get_orders_hint(self, player):
        if player.input_source == "keyboard1":
            return "Presiona Q para ver pedidos"
        elif player.input_source == "keyboard2":
            return "Presiona Retroceso para ver pedidos"
        else:
            return "Presiona X / Cuadrado para ver pedidos"

    def advance_step(self):
        self.step += 1
        
        if self.step == 1:
            self.play_dialog("¡Bienvenidos al almacén! Soy su nuevo jefe.")
        elif self.step == 2:
            self.play_dialog("El trabajo aquí es simple, pero requiere coordinación.\nYa pueden empezar a moverse.")
        elif self.step == 3:
            for player in self.play_state.players.values():
                self.custom_hints[player.number] = self.get_movement_hint(player)
        elif self.step == 4:
            self.play_dialog("¡Excelente!\nTodas las mañanas llegarán camiones dejando cajas.\nDeben descargarlas en sus respectivos estantes.")
        elif self.step == 5:
            self.room.unloading_truck.arrive(on_finish=self._spawn_tutorial_boxes)
        elif self.step == 6:
            self.play_dialog("¡Muy bien hecho!\nPronto vendrán a buscar pedidos.\nAbran su lista de pedidos ahora mismo.")
        elif self.step == 7:
            for player in self.play_state.players.values():
                self.custom_hints[player.number] = self.get_orders_hint(player)
            o1 = Order(1, 1, Counter({1: 3}), 1)
            o2 = Order(2, 2, Counter({3: 5}), 1)
            self.room.orders = [o1, o2]
            self.dispatch_trucks = [{"id": 1, "time": 0, "done": False}]
        elif self.step == 8:
            self.play_dialog("¡Apresúrense!\nDebemos empaquetarlos ahora mismo.\nAgarren cajas vacías de los dispensadores y trabajen sobre las mesas.")
        elif self.step == 9:
            pass
        elif self.step == 10:
            self.play_dialog("¡Los paquetes están listos!\nLleven esas cajas terminadas a la zona de despacho (área amarilla).")
        elif self.step == 11:
            pass
        elif self.step == 12:
            self.room.dispatch_truck.arrive(on_finish=self._truck_takes_boxes)
        elif self.step == 13:
            self.play_dialog("¡Buen trabajo equipo!\nNos vemos mañana a primera hora.")
        elif self.step == 14:
            self.play_state._finish_match()

    def _spawn_tutorial_boxes(self):
        self.tutorial_box1 = Box(self.room.unloading_area.x, self.room.unloading_area.y, "large", {1: 3})
        self.tutorial_box2 = Box(self.room.unloading_area.x + 64, self.room.unloading_area.y, "large", {3: 5})
        
        self.room.objects.extend([self.tutorial_box1, self.tutorial_box2])
        self.room.unloading_truck.depart()
        self.boxes_spawned = True

    def _truck_takes_boxes(self):
        boxes_to_take = [box for box in self.room.objects 
                         if box.solid and box.table is None and self.room.dispatch_area.contains(box.hitbox)]
        for box in boxes_to_take:
            self.room.objects.remove(box)
            order = next((o for o in self.room.orders if o.number not in self.room.delivered_orders and o.matches(box)), None)
            if order is not None:
                self.room.delivered_orders[order.number] = box
            else:
                self.room.incorrect_boxes.append(box)
                
        self.room.dispatch_truck.depart(on_finish=self.advance_step)

    def update(self, dt: float):
        if getattr(self.play_state, "active_dialog", None) is not None:
            return
            
        if self.wait_timer > 0:
            self.wait_timer -= dt
            if self.wait_timer <= 0:
                self.advance_step()
            return
            
        if self.step == 0:
            self.advance_step()
            
        elif self.step == 1:
            self.advance_step()
            
        elif self.step == 2:
            self.advance_step()
            
        elif self.step == 3:
            for player in self.play_state.players.values():
                if player.facing and player.direction.length_squared() > 0:
                    self.moved_dirs[player.number].add(player.facing)
                
                if len(self.moved_dirs[player.number]) >= 4:
                    self.custom_hints.pop(player.number, None)
                    
            if not self.custom_hints:
                self.advance_step()
                
        elif self.step == 4:
            self.advance_step()
            
        elif self.step == 5:
            if getattr(self, "boxes_spawned", False):
                has_large_boxes = any(getattr(obj, "box_type", None) == "large" for obj in self.room.objects)
                
                if not has_large_boxes:
                    self.wait_timer = 1.0
                    self.advance_step()
                
        elif self.step == 6:
            self.advance_step()
            
        elif self.step == 7:
            for player_num in self.play_state.orders_held:
                self.orders_opened[player_num] = True
                self.custom_hints.pop(player_num, None)
                
            if all(self.orders_opened.values()) and not self.play_state.show_orders_panel:
                self.advance_step()
                
        elif self.step == 8:
            self.advance_step()
            
        elif self.step == 9:
            order_boxes = [obj for obj in self.room.objects if isinstance(obj, Box) and obj.is_order]
            matched = 0
            for box in order_boxes:
                for order in self.room.orders:
                    if order.matches(box):
                        matched += 1
            if matched >= 2:
                self.advance_step()
                
        elif self.step == 10:
            self.advance_step()
            
        elif self.step == 11:
            dispatch_boxes = [box for box in self.room.objects 
                              if isinstance(box, Box) and box.solid and box.table is None 
                              and self.room.dispatch_area.contains(box.hitbox)]
            matched = 0
            for box in dispatch_boxes:
                for order in self.room.orders:
                    if order.matches(box):
                        matched += 1
            if matched >= 2:
                self.advance_step()
                
        elif self.step == 12:
            if getattr(self, "resume_processed_dispatch", False):
                self.resume_processed_dispatch = False
                self.step = 13
                self.play_dialog("¡Buen trabajo equipo!\nNos vemos mañana a primera hora.")
            
        elif self.step == 13:
            self.advance_step()

    def snapshot_state(self):
        return {
            "step": self.step,
            "wait_timer": self.wait_timer,
            "moved_dirs": {str(number): sorted(directions)
                           for number, directions in self.moved_dirs.items()},
            "orders_opened": {str(number): opened
                              for number, opened in self.orders_opened.items()},
            "custom_hints": {str(number): hint
                             for number, hint in self.custom_hints.items()},
            "dispatch_trucks": [dict(event) for event in self.dispatch_trucks],
            "boxes_spawned": getattr(self, "boxes_spawned", False),
        }

    def restore_state(self, data):
        self.step = int(data["step"])
        self.wait_timer = float(data["wait_timer"])
        self.moved_dirs = {int(number): set(directions)
                           for number, directions in data["moved_dirs"].items()}
        self.orders_opened = {int(number): bool(opened)
                              for number, opened in data["orders_opened"].items()}
        self.custom_hints = {int(number): hint
                             for number, hint in data["custom_hints"].items()}
        self.dispatch_trucks = [dict(event) for event in data["dispatch_trucks"]]
        self.boxes_spawned = bool(data["boxes_spawned"])

        # Si se guardó durante una animación, se repite sólo el paso pendiente.
        if self.step == 5 and not self.boxes_spawned:
            self.step = 4
        elif self.step == 12:
            if self.room.delivered_orders:
                self.resume_processed_dispatch = True
            else:
                self.step = 11
        self._reset_trucks()

    def _reset_trucks(self):
        for truck in (self.room.unloading_truck, self.room.dispatch_truck):
            if truck is None:
                continue
            if truck.active_tween is not None:
                truck.active_tween.remove()
                truck.active_tween = None
            truck.x = truck.offscreen_x
            truck.y = truck.offscreen_y

    def stop(self):
        self._reset_trucks()
