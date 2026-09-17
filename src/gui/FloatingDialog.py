import pygame
import settings

class FloatingDialog:
    def __init__(self, text: str, font: pygame.font.Font, portrait_frames: list[pygame.Surface] = None, sound: pygame.mixer.Sound = None):
        self.full_text = text
        self.font = font
        # Escalar los frames del retrato (de 32x32 a 96x96 para que llene bien la caja)
        self.portrait_frames = [pygame.transform.scale(frame, (96, 96)) for frame in portrait_frames] if portrait_frames else None
        self.sound = sound
        
        self.char_index = 0.0
        self.chars_per_second = 30.0  # Velocidad de aparición del texto
        self.is_typing = True
        self.is_finished = False
        
        self.portrait_timer = 0.0
        self.portrait_index = 0
        
        # Sonido (para no saturar el canal de audio, podemos llevar cuenta del último índice reproducido)
        self.last_played_index = 0
        
        # Geometría de la caja
        margin = 20
        box_height = 120
        self.rect = pygame.Rect(
            margin,
            settings.VIRTUAL_HEIGHT - box_height - margin,
            settings.VIRTUAL_WIDTH - (margin * 2),
            box_height
        )

    def update(self, dt: float) -> None:
        if self.is_typing:
            self.char_index += self.chars_per_second * dt
            
            # Animación de la boca
            if self.portrait_frames and len(self.portrait_frames) > 1:
                self.portrait_timer += dt
                if self.portrait_timer > 0.15:  # Cambia de frame cada 0.15s
                    self.portrait_timer = 0.0
                    self.portrait_index = 1 if self.portrait_index == 0 else 0
            
            # Verificar si se reveló un nuevo carácter para reproducir sonido
            current_index = int(self.char_index)
            if current_index > self.last_played_index and current_index <= len(self.full_text):
                # Omitir sonido en espacios para dar efecto más natural
                if self.sound and self.full_text[self.last_played_index] != " ":
                    self.sound.play()
                self.last_played_index = current_index

            if self.char_index >= len(self.full_text):
                self.char_index = len(self.full_text)
                self.is_typing = False
        else:
            # Si terminó de hablar, boca cerrada (frame 0)
            self.portrait_index = 0

    def on_input(self, input_id: str, input_data) -> None:
        # Avanzar o cerrar si presionamos el botón de confirmar (teclado o mando)
        if input_id in ("confirm", "pad_a") and input_data.pressed:
            if self.is_typing:
                # Si está escribiendo, autocompletar todo de golpe
                self.char_index = len(self.full_text)
                self.is_typing = False
            else:
                # Si ya terminó de escribir, cerramos el diálogo
                self.is_finished = True

    def render(self, surface: pygame.Surface) -> None:
        # Fondo del cuadro
        pygame.draw.rect(surface, settings.PANEL_COLOR, self.rect)
        pygame.draw.rect(surface, settings.TEXT_COLOR, self.rect, width=2)
        
        inner_rect = self.rect.inflate(-20, -20)
        
        # Dibujar retrato a la izquierda si existe
        text_width_limit = inner_rect.width
        text_x_offset = inner_rect.left
        
        if self.portrait_frames:
            current_portrait = self.portrait_frames[self.portrait_index]
            portrait_rect = current_portrait.get_rect(topleft=inner_rect.topleft)
            surface.blit(current_portrait, portrait_rect)
            # Reducir el espacio para el texto y desplazar su inicio a la derecha
            text_width_limit -= (portrait_rect.width + 15)
            text_x_offset += (portrait_rect.width + 15)

        # Dibujar el texto revelado hasta el momento
        displayed_text = self.full_text[:int(self.char_index)]
        
        # Pequeño sistema manual para dividir el texto en varias líneas
        words = displayed_text.split(" ")
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if self.font.size(test_line)[0] > text_width_limit:
                lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        lines.append(current_line)

        # Dibujar las líneas
        y_offset = inner_rect.top
        for line in lines:
            if not line:
                continue
            text_surf = self.font.render(line, True, settings.TEXT_COLOR)
            surface.blit(text_surf, (text_x_offset, y_offset))
            y_offset += self.font.get_linesize()
