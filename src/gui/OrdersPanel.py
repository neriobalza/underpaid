"""Lista personal de pedidos sobre el almacén, sin detener el reloj."""

import pygame

import settings
from src.world.Product import Product


class OrdersPanel:
    def __init__(self):
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 18)
        self.icons = tuple(pygame.transform.scale(image, (18, 18)) for image in settings.load_product_frames())

    @staticmethod
    def status_parts(room, order):
        if order.number in room.delivered_orders:
            if order.number in getattr(room, "wrong_box_orders", set()):
                return (
                    ("ENTREGADO", settings.PLACEMENT_VALID_COLOR),
                    (" (CAJA INCORRECTA)", settings.PLACEMENT_INVALID_COLOR),
                )
            return (("ENTREGADO", settings.PLACEMENT_VALID_COLOR),)
        if order.number in getattr(room, "missed_orders", set()):
            return (("NO ENTREGADO", settings.PLACEMENT_INVALID_COLOR),)
        return (("PENDIENTE", settings.TEXT_COLOR),)

    def render(self, surface, room, owner) -> None:
        rect = pygame.Rect(20, 30, 600, 420)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((*settings.PANEL_COLOR, 235))
        surface.blit(panel, rect)
        pygame.draw.rect(surface, settings.TEXT_COLOR, rect, width=2, border_radius=6)
        title = self.font.render("Pedidos del Día (Agrupados por salida)", True, settings.TEXT_COLOR)
        surface.blit(title, (rect.x + 12, rect.y + 12))
        
        truck_times = {}
        if hasattr(room, "strategy") and hasattr(room.strategy, "dispatch_trucks"):
            for ev in room.strategy.dispatch_trucks:
                ratio = ev["time"] / settings.MATCH_DURATION
                total_minutes = (settings.CLOCK_END_HOUR - settings.CLOCK_START_HOUR) * 60
                event_mins = settings.CLOCK_START_HOUR * 60 + ratio * total_minutes
                h, m = divmod(int(event_mins), 60)
                period = "AM" if h % 24 < 12 else "PM"
                h_str = f"{h % 12 or 12}:{m:02d} {period}"
                truck_times[ev["id"]] = {"h_str": h_str, "time": ev["time"]}
                
        orders_by_truck = {}
        for order in room.orders:
            orders_by_truck.setdefault(order.truck_id, []).append(order)
            
        sorted_trucks = sorted(orders_by_truck.keys(), key=lambda t_id: truck_times.get(t_id, {}).get("time", 0))
        
        delivered, _ = room.delivery_report()
        y_start = rect.y + 45
        y = y_start
        col = 0
        x_offset = rect.x + 12 + (col * 290)
        
        for truck_id in sorted_trucks:
            if y > rect.bottom - 120:
                col += 1
                y = y_start
                x_offset = rect.x + 12 + (col * 290)
                
            time_str = truck_times.get(truck_id, {}).get("h_str", "--:--")
            truck_header = self.font.render(f"► Camión de Despacho - {time_str}", True, settings.MUTED_COLOR)
            surface.blit(truck_header, (x_offset, y))
            y += 24
            
            for order in orders_by_truck[truck_id]:
                done = order.number in delivered
                size = "Mediana" if order.box_type == "medium" else "Pequeña"
                status_parts = self.status_parts(room, order)
                if done and order.number in getattr(room, "wrong_box_orders", set()):
                    surface.blit(self.font.render(f"Pedido en Caja {size}", True, settings.TEXT_COLOR),
                                 (x_offset + 12, y))
                    y += 20
                    status_x = x_offset + 12
                    for text, color in status_parts:
                        image = self.font.render(text, True, color)
                        surface.blit(image, (status_x, y))
                        status_x += image.get_width()
                else:
                    status, color = status_parts[0]
                    surface.blit(self.font.render(f"Pedido en Caja {size} · {status}", True, color),
                                 (x_offset + 12, y))
                y += 20
                
                for product_type, quantity in sorted(order.requirements.items()):
                    surface.blit(self.icons[product_type], (x_offset + 12, y))
                    label = self.font.render(f"{Product(product_type).name} × {quantity}", True, settings.TEXT_COLOR)
                    surface.blit(label, (x_offset + 38, y))
                    y += 20
                y += 10
                
                if y > rect.bottom - 60:
                    col += 1
                    y = y_start
                    x_offset = rect.x + 12 + (col * 290)
                    
            y += 10 # Extra spacing after a truck group
                
        surface.blit(self.small_font.render("Q / X: cerrar · Esc: pausa", True, settings.MUTED_COLOR),
                     (rect.x + 12, rect.bottom - 26))
