"""Pantalla de inicio y navegación principal."""

from gale.state import BaseState
import pygame

import settings
from src.gui.Menu import Menu, draw_text
from src.gui.WarehousePreview import WarehousePreview


class MainMenuState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self) -> None:
        self.preview = WarehousePreview()
        self.panel = pygame.Rect(24, 64, 264, 350)
        self.title = pygame.font.Font(None, 48).render("UNDERPAID", True, settings.ACCENT_COLOR)
        self.small_font = pygame.font.Font(None, 18)
        self.shade = pygame.Surface((settings.VIRTUAL_WIDTH, settings.VIRTUAL_HEIGHT), pygame.SRCALPHA)
        self.shade.fill((*settings.BACKGROUND_COLOR, 45))
        self.panel_image = pygame.Surface(self.panel.size, pygame.SRCALPHA)
        pygame.draw.rect(self.panel_image, (*settings.PANEL_COLOR, 235), self.panel_image.get_rect(), border_radius=12)
        items = [("Jugar", self.game.start_game)]
        if self.game.tutorial_completed:
            items.append(("Tutorial", self.game.start_tutorial))
        items.extend([
            ("Configuración", lambda: self.state_machine.change("settings")),
            ("Salir", self.game.quit),
        ])
        self.menu = Menu(self.game, items, x=44, y=210, width=224,
                         height=40, spacing=48)

    def update(self, dt: float) -> None:
        self.preview.update(dt)

    def on_input(self, input_id, input_data) -> None:
        self.menu.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        self.preview.render(surface)
        surface.blit(self.shade, (0, 0))
        surface.blit(self.panel_image, self.panel)
        pygame.draw.rect(surface, settings.ACCENT_COLOR, self.panel, width=1, border_radius=12)
        label = self.small_font.render("tlabaja, tiene que tlabajal", True, settings.MUTED_COLOR)
        surface.blit(label, label.get_rect(center=(self.panel.centerx, 91)))
        surface.blit(self.title, self.title.get_rect(center=(self.panel.centerx, 128)))
        label = self.game.fonts["small"].render(
            "Un almacén. Dos compañeros.", True, settings.TEXT_COLOR,
        )
        surface.blit(label, label.get_rect(center=(self.panel.centerx, 169)))
        if self.game.tutorial_progress_error:
            status, color = "Tutorial completado · Error al guardar", settings.PLACEMENT_INVALID_COLOR
        elif self.game.tutorial_completed:
            status, color = "Tutorial completado", settings.PLACEMENT_VALID_COLOR
        else:
            status, color = "Primera partida: tutorial", settings.ACCENT_COLOR
        label = self.small_font.render(status, True, color)
        surface.blit(label, label.get_rect(center=(self.panel.centerx, 191)))
        self.menu.render(surface)
        draw_text(surface, "El almacén sigue en marcha.", self.game.fonts["small"], 432, settings.TEXT_COLOR)
        pygame.draw.rect(surface, settings.PANEL_COLOR, (0, 450, settings.VIRTUAL_WIDTH, 30))
        draw_text(surface, "Flechas / W-S · Enter / Espacio · Ratón · Cruceta / A",
                  self.small_font, 465, settings.MUTED_COLOR)
