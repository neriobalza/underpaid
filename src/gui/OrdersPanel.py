"""Lista personal de pedidos sobre el almacén, sin detener el reloj."""

import pygame

import settings
from src.world.Product import Product


class OrdersPanel:
    def __init__(self):
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 18)
        self.icons = tuple(pygame.transform.scale(image, (18, 18)) for image in settings.load_product_frames())

    def render(self, surface, room, owner) -> None:
        # Mostramos un único menú sin importar quién lo abra
        rect = pygame.Rect(20, 30, 600, 420)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((*settings.PANEL_COLOR, 235))
        surface.blit(panel, rect)
        pygame.draw.rect(surface, settings.TEXT_COLOR, rect, width=2, border_radius=6)
        title = self.font.render(f"Pedidos del Día (Compartido)", True, settings.TEXT_COLOR)
        surface.blit(title, (rect.x + 12, rect.y + 12))
        
        # Mostrar hora de los camiones
        dispatch_times_str = ""
        if hasattr(room, "strategy"):
            times = []
            for ev in room.strategy.dispatch_trucks:
                # Convert match_duration relative time to clock time
                # time goes from 0 to MATCH_DURATION, hours go from START to END
                ratio = ev["time"] / settings.MATCH_DURATION
                total_minutes = (settings.CLOCK_END_HOUR - settings.CLOCK_START_HOUR) * 60
                event_mins = settings.CLOCK_START_HOUR * 60 + ratio * total_minutes
                h, m = divmod(int(event_mins), 60)
                period = "AM" if h % 24 < 12 else "PM"
                h_str = f"{h % 12 or 12}:{m:02d} {period}"
                times.append(f"C{ev['id']}: {h_str}")
            dispatch_times_str = " · ".join(times)
            
        trucks_title = self.small_font.render(f"Salidas de Camiones: {dispatch_times_str}", True, settings.MUTED_COLOR)
        surface.blit(trucks_title, (rect.x + 12, rect.y + 36))
        
        delivered, _ = room.delivery_report()
        y_start = rect.y + 60
        y = y_start
        col = 0
        
        for order in room.orders:
            done = order.number in delivered
            status = "ENTREGADO" if done else "PENDIENTE"
            color = settings.PLACEMENT_VALID_COLOR if done else settings.TEXT_COLOR
            x_offset = rect.x + 12 + (col * 290)
            
            surface.blit(self.font.render(f"Pedido #{order.number} (Camión {order.truck_id}) · {status}", True, color), (x_offset, y))
            y += 22
            size = "Mediana" if order.box_type == "medium" else "Pequeña"
            surface.blit(self.small_font.render(f"{size} · {order.quantity} productos", True, settings.MUTED_COLOR), (x_offset, y))
            y += 20
            
            for product_type, quantity in sorted(order.requirements.items()):
                surface.blit(self.icons[product_type], (x_offset, y))
                label = self.font.render(f"{Product(product_type).name} × {quantity}", True, settings.TEXT_COLOR)
                surface.blit(label, (x_offset + 26, y))
                y += 20
            y += 14
            
            # Pasar a la segunda columna si nos acercamos al fondo
            if y > rect.bottom - 100:
                col += 1
                y = y_start
                
        surface.blit(self.small_font.render("Q / X: cerrar · Esc: pausa", True, settings.MUTED_COLOR),
                     (rect.x + 12, rect.bottom - 26))
