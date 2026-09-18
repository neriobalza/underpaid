import random
from collections import Counter
import math
import pygame
from gale.timer import Timer

from src.world.Order import generate_orders
from src.world.Box import Box
import settings

class DaySchedule:
    def __init__(self, room, rng=None):
        self.room = room
        self.rng = rng or random.Random()
        self.time = 0.0
        self.match_duration = settings.MATCH_DURATION
        
        # 1. Definir los tiempos de los camiones de despacho
        self.dispatch_trucks = []
        num_dispatch_trucks = 4
        interval = self.match_duration / (num_dispatch_trucks + 1)
        
        for i in range(num_dispatch_trucks):
            self.dispatch_trucks.append({
                "id": i + 1,
                "time": interval * (i + 1),
                "done": False
            })
            
        mid_time = self.match_duration / 2
        early_truck_ids = {t["id"] for t in self.dispatch_trucks if t["time"] <= mid_time + 5.0}
        
        # 2. Generar órdenes y separar requerimientos (Temprano vs Tarde)
        self.orders = generate_orders(self.rng, num_trucks=num_dispatch_trucks)
        
        early_totals = Counter()
        late_totals = Counter()
        
        for order in self.orders:
            for p_type, q in order.requirements.items():
                if order.truck_id in early_truck_ids:
                    early_totals[p_type] += q
                else:
                    late_totals[p_type] += q
                    
        # 3. Aplicar 30% de margen y crear listas de items
        early_items = []
        for p_type, q in early_totals.items():
            early_items.extend([p_type] * int(math.ceil(q * 1.3)))
            
        late_items = []
        for p_type, q in late_totals.items():
            late_items.extend([p_type] * int(math.ceil(q * 1.3)))
            
        self.rng.shuffle(early_items)
        self.rng.shuffle(late_items)
        
        # 4. Balancear: Si hay más demanda tarde que temprano, mover items para que lleguen antes
        while len(late_items) > len(early_items):
            early_items.append(late_items.pop())
            
        self.rng.shuffle(early_items)
        
        # 5. Distribuir en las cajas (4 para Lote 1, 4 para Lote 2)
        self.batch1 = [Counter() for _ in range(4)]
        for i, item in enumerate(early_items):
            self.batch1[i % 4][item] += 1
            
        self.batch2 = [Counter() for _ in range(4)]
        for i, item in enumerate(late_items):
            self.batch2[i % 4][item] += 1
            
        # Unloading events
        self.unloading_events = [
            {"time": 2.0, "batch": self.batch1, "done": False},
            {"time": mid_time, "batch": self.batch2, "done": False}
        ]
            
        self.active_unloading = False
        self.active_dispatch = False
        
        # Assign orders to room so UI and mechanics can see them
        self.room.orders = self.orders
        self.room.active_dispatch_truck_id = None
        
    def spawn_batch(self, batch):
        width, height = settings.BOX_SIZES["large"]
        slots = [
            pygame.Rect(x, y, width, height)
            for y in range(self.room.unloading_area.top, self.room.unloading_area.bottom - height + 1, height)
            for x in range(self.room.unloading_area.left, self.room.unloading_area.right - width + 1, width)
            if self.room.floor_contains(pygame.Rect(x, y, width, height))
            and not any(pygame.Rect(x, y, width, height).colliderect(obj.hitbox) for obj in self.room.obstacles)
        ]
        
        for contents in batch:
            if not slots:
                break # No more space
            slot = slots.pop(0)
            box = Box(slot.x, slot.y, "large", contents)
            self.room.objects.append(box)
            
    def update(self, dt):
        self.time += dt
        
        if not self.active_unloading:
            for ev in self.unloading_events:
                if not ev["done"] and self.time >= ev["time"]:
                    ev["done"] = True
                    self.active_unloading = True
                    def on_arrive(batch=ev["batch"]):
                        self.spawn_batch(batch)
                        Timer.after(5.0, lambda: self.room.unloading_truck.depart(on_finish=lambda: setattr(self, "active_unloading", False)))
                    self.room.unloading_truck.arrive(on_finish=on_arrive)
                    break
                    
        if not self.active_dispatch:
            for ev in self.dispatch_trucks:
                if not ev["done"] and self.time >= ev["time"]:
                    ev["done"] = True
                    self.active_dispatch = True
                    self.room.active_dispatch_truck_id = ev["id"]
                    def on_dispatch_arrive():
                        Timer.after(10.0, self.depart_dispatch_truck)
                    self.room.dispatch_truck.arrive(on_finish=on_dispatch_arrive)
                    break
                    
    def depart_dispatch_truck(self):
        boxes_to_take = [box for box in self.room.objects 
                         if box.solid and box.table is None and self.room.dispatch_area.contains(box.hitbox)]
        
        for box in boxes_to_take:
            self.room.objects.remove(box)
            
        delivered, incorrect = self.evaluate_delivery(boxes_to_take, self.room.active_dispatch_truck_id)
        
        if hasattr(self.room, "on_dispatch_depart"):
            self.room.on_dispatch_depart(delivered, incorrect, boxes_to_take)
            
        self.room.dispatch_truck.depart(on_finish=self._on_dispatch_departed)
        
    def _on_dispatch_departed(self):
        self.active_dispatch = False
        self.room.active_dispatch_truck_id = None
        
    def evaluate_delivery(self, boxes, truck_id):
        delivered = {}
        incorrect = []
        truck_orders = [o for o in self.orders if o.truck_id == truck_id]
        
        for box in boxes:
            if not box.is_order:
                incorrect.append(box)
                continue
                
            order = next((order for order in truck_orders
                          if order.number not in delivered and order.matches(box)), None)
            if order is None:
                incorrect.append(box)
            else:
                delivered[order.number] = box
                
        return delivered, incorrect
