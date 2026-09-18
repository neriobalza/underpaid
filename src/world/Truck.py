import pygame
from gale.timer import Timer

import settings

class Truck:
    def __init__(self, x: float, y: float, width: float, height: float, tile_id: int):
        self.parked_x = x
        self.parked_y = y
        self.width = width
        self.height = height
        self.tile_id = tile_id
        
        # Cargar la imagen del camión basada en el tile_id
        image_path = settings.BASE_DIR / "assets" / "graphics" / "truck" / f"{tile_id}.png"
        self.image = pygame.image.load(image_path).convert_alpha()
        
        orig_w, orig_h = self.image.get_size()
        
        if tile_id in (1, 3):
            # Adaptar alto basándose en el ancho definido en el mapa
            new_width = width
            new_height = new_width * (orig_h / orig_w)
        elif tile_id in (2, 4):
            # Adaptar ancho basándose en el alto definido en el mapa
            new_height = height
            new_width = new_height * (orig_w / orig_h)
        else:
            new_width = width
            new_height = height
            
        self.width = new_width
        self.height = new_height
        self.image = pygame.transform.scale(self.image, (int(self.width), int(self.height)))
        
        # Ajustar la posición de aparcamiento final para asomar solo el extremo
        if tile_id == 3:
            # El borde inferior del camión coincide con el borde inferior del objeto de Tiled
            self.parked_y = (y + height) - self.height
        elif tile_id == 4:
            # El borde derecho del camión coincide con el borde derecho del objeto de Tiled
            self.parked_x = (x + width) - self.width
            
        
        # Determinar posición fuera de la pantalla (offscreen)
        # Asumimos que si está cerca del borde superior, viene de arriba.
        # Si está cerca del borde derecho, viene de la derecha, etc.
        if self.parked_y <= settings.MAP_RENDER_OFFSET_Y + 10:
            # Viene de arriba
            self.offscreen_x = self.parked_x
            self.offscreen_y = -self.height
        elif self.parked_x >= settings.VIRTUAL_WIDTH - self.width - 10:
            # Viene de la derecha
            self.offscreen_x = settings.VIRTUAL_WIDTH
            self.offscreen_y = self.parked_y
        elif self.parked_x <= 10:
            # Viene de la izquierda
            self.offscreen_x = -self.width
            self.offscreen_y = self.parked_y
        else:
            # Viene de abajo por defecto
            self.offscreen_x = self.parked_x
            self.offscreen_y = settings.VIRTUAL_HEIGHT

        # Iniciar fuera de la pantalla
        self.x = self.offscreen_x
        self.y = self.offscreen_y
        
        self.active_tween = None

    def arrive(self, duration: float = 2.0, on_finish=None):
        if self.active_tween:
            self.active_tween.remove()
            
        self.active_tween = Timer.tween(
            duration,
            [(self, {"x": self.parked_x, "y": self.parked_y})],
            "out_quad",  # unaccelerate (ease-out)
            on_finish=on_finish
        )

    def depart(self, duration: float = 2.0, on_finish=None):
        if self.active_tween:
            self.active_tween.remove()
            
        self.active_tween = Timer.tween(
            duration,
            [(self, {"x": self.offscreen_x, "y": self.offscreen_y})],
            "in_quad",  # accelerate (ease-in)
            on_finish=on_finish
        )

    def render(self, surface: pygame.Surface):
        surface.blit(self.image, (self.x, self.y))
