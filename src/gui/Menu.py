"""Menú reutilizable con selección por teclado y ratón."""

from collections.abc import Callable

import pygame

import settings


def draw_text(surface, text, font, y, color=None):
    image = font.render(text, True, color or settings.TEXT_COLOR)
    surface.blit(image, image.get_rect(center=(settings.VIRTUAL_WIDTH // 2, y)))


class Menu:
    def __init__(self, game, items: list[tuple[str, Callable[[], None]]], y=220, x=100, width=440):
        self.game = game
        self.items = items
        self.selected = 0
        self.rects = [
            pygame.Rect(x, y + i * 56, width, 44)
            for i in range(len(items))
        ]

    def on_input(self, input_id, input_data) -> None:
        if input_id in ("mouse_move", "click"):
            if input_id == "click" and not input_data.pressed:
                return
            position = self.game.to_virtual_position(input_data.position)
            for index, rect in enumerate(self.rects):
                if rect.collidepoint(position):
                    self.selected = index
                    if input_id == "click":
                        self.items[index][1]()
                    break
            return

        if not input_data.pressed:
            return
        if input_id == "up":
            self.selected = (self.selected - 1) % len(self.items)
        elif input_id == "down":
            self.selected = (self.selected + 1) % len(self.items)
        elif input_id == "confirm":
            self.items[self.selected][1]()

    def render(self, surface: pygame.Surface) -> None:
        for index, ((label, _), rect) in enumerate(zip(self.items, self.rects)):
            selected = index == self.selected
            pygame.draw.rect(
                surface,
                settings.ACCENT_COLOR if selected else settings.PANEL_COLOR,
                rect,
                border_radius=8,
            )
            image = self.game.fonts["medium"].render(
                label, True, settings.BACKGROUND_COLOR if selected else settings.TEXT_COLOR,
            )
            surface.blit(image, image.get_rect(center=rect.center))
