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
        rect = pygame.Rect(10 if owner == 1 else 330, 48, 300, 390)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((*settings.PANEL_COLOR, 235))
        surface.blit(panel, rect)
        pygame.draw.rect(surface, settings.PLAYER_COLORS[owner], rect, width=2, border_radius=6)
        title = self.font.render(f"Jugador {owner} · Pedidos", True, settings.PLAYER_COLORS[owner])
        surface.blit(title, (rect.x + 12, rect.y + 12))
        delivered, _ = room.delivery_report()
        y = rect.y + 42
        for order in (order for order in room.orders if order.owner == owner):
            done = order.number in delivered
            status = "ENTREGADO" if done else "PENDIENTE"
            color = settings.PLACEMENT_VALID_COLOR if done else settings.TEXT_COLOR
            surface.blit(self.font.render(f"Pedido #{order.number} · {status}", True, color), (rect.x + 12, y))
            y += 22
            size = "Mediana" if order.box_type == "medium" else "Pequeña"
            surface.blit(self.small_font.render(f"{size} · {order.quantity} productos", True, settings.MUTED_COLOR),
                         (rect.x + 12, y))
            y += 20
            for product_type, quantity in sorted(order.requirements.items()):
                surface.blit(self.icons[product_type], (rect.x + 12, y))
                label = self.font.render(f"{Product(product_type).name} × {quantity}", True, settings.TEXT_COLOR)
                surface.blit(label, (rect.x + 38, y))
                y += 20
            y += 14
        surface.blit(self.small_font.render("Q / X: cerrar · Esc: pausa", True, settings.MUTED_COLOR),
                     (rect.x + 12, rect.bottom - 26))
