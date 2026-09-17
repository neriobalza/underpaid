"""Personaje vinculado exclusivamente a un mando o al teclado."""

import pygame
from gale.command import CommandBindings
from gale.animation import Animation
from gale.input_handler import apply_deadzone

import settings
from src.input.commands import MOVEMENT_COMMANDS


class Player:
    def __init__(self, input_source: int | str) -> None:
        if input_source != settings.KEYBOARD_INPUT and (
            type(input_source) is not int or input_source < 0
        ):
            raise ValueError("La entrada debe ser el teclado o un ID de instancia válido")
        self.input_source = input_source
        self.number: int | None = None
        self.position = pygame.Vector2(settings.VIRTUAL_WIDTH / 2, 260)
        self.direction = pygame.Vector2()
        self.keyboard_keys: set[int] = set()
        self.command_bindings = CommandBindings()
        for action, (press, release) in MOVEMENT_COMMANDS.items():
            self.command_bindings.bind(action, press=press, release=release)
        self.facing = "down"
        self.animations = {
            direction: Animation(frames, settings.PLAYER_FRAME_INTERVAL)
            for direction, frames in settings.load_player_frames().items()
        }
        self.animation = self.animations[self.facing]
        self.carry_animations = {
            direction: Animation(frames, settings.PLAYER_FRAME_INTERVAL)
            for direction, frames in settings.load_player_frames("player_pot_walk.png").items()
        }
        self.carrying = None
        self.lift_elapsed = 0.0
        self.lift_start = pygame.Vector2()
        self.interact_held = False
        self.interact_requested = False

    @property
    def uses_keyboard(self) -> bool:
        return self.input_source == settings.KEYBOARD_INPUT

    @property
    def controller_id(self) -> int | None:
        return None if self.uses_keyboard else self.input_source

    def is_connected(self, controllers) -> bool:
        return self.uses_keyboard or controllers.is_connected(self.controller_id)

    @property
    def hitbox(self) -> pygame.Rect:
        """Área de apoyo en el suelo; la cabeza puede sobresalir sobre paredes."""
        return pygame.Rect(
            round(self.position.x - settings.PLAYER_COLLISION_WIDTH / 2),
            round(self.position.y + settings.PLAYER_FRAME_HEIGHT / 2 - settings.PLAYER_COLLISION_HEIGHT),
            settings.PLAYER_COLLISION_WIDTH,
            settings.PLAYER_COLLISION_HEIGHT,
        )

    def select(self, number: int) -> None:
        if self.number is not None:
            raise ValueError("El jugador ya tiene un lado asignado")
        if number not in (1, 2):
            raise ValueError("Sólo existen los jugadores 1 y 2")
        self.number = number
        self.position.update(settings.VIRTUAL_WIDTH * (0.25 if number == 1 else 0.75), 260)
        self.stop()

    def stop(self) -> None:
        self.direction.update(0, 0)
        self.keyboard_keys.clear()
        self.animation.reset()

    def unselect(self) -> None:
        self.number = None
        self.stop()

    def lift(self, obj) -> None:
        if self.carrying is not None or not obj.solid:
            raise ValueError("El objeto o el jugador ya están ocupados")
        obj.carrier = self
        self.carrying = obj
        self.lift_elapsed = 0.0
        self.lift_start = obj.position.copy()
        self.animation = self.carry_animations[self.facing]
        self.animation.reset()

    def put_down(self, position) -> None:
        if self.carrying is not None:
            self.carrying.floor_position.update(position)
            self.carrying.position.update(position)
            self.carrying.carrier = None
            self.carrying = None
        self.lift_elapsed = 0.0
        self.animation = self.animations[self.facing]
        self.animation.reset()

    def clear_carrying(self) -> None:
        if self.carrying is not None:
            self.put_down(self.carrying.floor_position)
        self.interact_held = False
        self.interact_requested = False

    def _update_carried_object(self, dt: float) -> None:
        if self.carrying is None:
            return
        obj = self.carrying
        self.lift_elapsed = min(settings.POT_LIFT_DURATION, self.lift_elapsed + dt)
        target = pygame.Vector2(
            self.position.x - obj.width / 2,
            self.position.y - settings.PLAYER_FRAME_HEIGHT / 2 - obj.height + 12,
        )
        progress = self.lift_elapsed / settings.POT_LIFT_DURATION
        obj.position.update(self.lift_start.lerp(target, progress))

    def _move(self, movement, room, obstacles) -> None:
        half_width = settings.PLAYER_COLLISION_WIDTH / 2
        half_height = settings.PLAYER_FRAME_HEIGHT / 2
        top_offset = half_height - settings.PLAYER_COLLISION_HEIGHT
        
        solid_rects = [obj.hitbox for obj in obstacles if obj.solid]

        hitbox = self.hitbox
        tm_x = hitbox.left - room.bounds.left
        tm_y = hitbox.top - room.bounds.top
        
        from gale.tilemap import move_and_collide
        new_x, new_y, col_x, col_y = move_and_collide(
            room.tilemap, "walls",
            tm_x, tm_y, hitbox.width, hitbox.height,
            movement.x, movement.y,
            collision_property="collision"
        )
        
        target_x = new_x + room.bounds.left + half_width
        target_y = new_y + room.bounds.top - top_offset
        
        old_x = self.position.x
        self.position.x = target_x
        for rect in solid_rects:
            if self.position.y + half_height <= rect.top or self.position.y + top_offset >= rect.bottom:
                continue
            if target_x > old_x and old_x + half_width <= rect.left:
                self.position.x = min(self.position.x, rect.left - half_width)
            elif target_x < old_x and old_x - half_width >= rect.right:
                self.position.x = max(self.position.x, rect.right + half_width)

        old_y = self.position.y
        self.position.y = target_y
        for rect in solid_rects:
            if self.position.x + half_width <= rect.left or self.position.x - half_width >= rect.right:
                continue
            if target_y > old_y and old_y + half_height <= rect.top:
                self.position.y = min(self.position.y, rect.top - half_height)
            elif target_y < old_y and old_y + top_offset >= rect.bottom:
                self.position.y = max(self.position.y, rect.bottom - top_offset)

    def on_input(self, input_id, input_data) -> None:
        if self.number is None:
            return
        interaction = (
            self.uses_keyboard and input_id == "confirm"
            and getattr(input_data, "key", None) == pygame.K_RETURN
        ) or (
            not self.uses_keyboard and input_id == "pad_a"
            and getattr(input_data, "gamepad_id", None) == self.controller_id
        )
        if interaction:
            if input_data.pressed and not self.interact_held:
                self.interact_requested = True
            self.interact_held = input_data.pressed
            return
        if self.uses_keyboard:
            if not input_id.startswith("keyboard_") or not hasattr(input_data, "key"):
                return
            key = input_data.key
            if key not in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                return
            self.command_bindings.dispatch(self, input_id, input_data)
            return
        if getattr(input_data, "gamepad_id", None) != self.controller_id:
            return
        if input_id not in ("pad_x", "pad_y"):
            return
        value = apply_deadzone(input_data.value, settings.STICK_DEADZONE)
        if input_id == "pad_x":
            self.direction.x = value
        else:
            self.direction.y = value

    def update(self, dt: float, room, obstacles=()) -> None:
        if self.carrying is not None and self.lift_elapsed < settings.POT_LIFT_DURATION:
            self._update_carried_object(dt)
            return
        direction = self.direction.copy()
        # Limitar la longitud a 1 iguala la velocidad máxima en ejes y
        # diagonales, conservando el movimiento lento del joystick analógico.
        if direction.length_squared() > 1:
            direction.normalize_ip()
        self._move(direction * settings.PLAYER_SPEED * dt, room, obstacles)
        self._update_carried_object(dt)
        if direction.length_squared() == 0:
            self.animation.reset()
            return
        if abs(direction.x) > abs(direction.y):
            facing = "right" if direction.x > 0 else "left"
        else:
            facing = "down" if direction.y > 0 else "up"
        if facing != self.facing:
            self.facing = facing
            animations = self.carry_animations if self.carrying is not None else self.animations
            self.animation = animations[facing]
            self.animation.reset()
        self.animation.update(dt)

    def render(self, surface) -> None:
        frame = self.animation.get_current_frame()
        rect = frame.get_rect(center=(round(self.position.x), round(self.position.y)))
        surface.blit(frame, rect)
        if self.carrying is not None:
            self.carrying.render(surface)
