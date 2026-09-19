"""Selección con mando (A/B) o teclado (Enter/Delete)."""

import pygame
from gale.state import BaseState
from gale.input_handler import apply_deadzone

import settings
from src.entity.Player import Player
from src.gui.Menu import draw_text


class PlayerSelectState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players=None, message: str = "", resume_snapshot=None) -> None:
        # Sólo las elecciones confirmadas reservan un personaje.
        self.players = dict(players or {})
        self.participants = {p.input_source: p for p in self.players.values()}
        self.choices = {p.input_source: p.number for p in self.players.values()}
        self.stick_ready = {instance_id: True for instance_id in self.participants}
        for player in self.participants.values():
            player.stop()
        self.message = message
        self.resume_snapshot = resume_snapshot
        self.keyboard_keys: set[int] = set()

    def update(self, dt: float) -> None:
        for instance_id in list(self.participants):
            if not self.participants[instance_id].is_connected(self.game.controllers):
                player = self.participants.pop(instance_id)
                self.players.pop(player.number, None)
                self.choices.pop(instance_id)
                self.stick_ready.pop(instance_id)
                self.message = "Mando desconectado. A / Enter para entrar."

    def join(self, instance_id: int | str) -> None:
        if len(self.participants) >= 2:
            self.message = "Ya hay dos jugadores participando."
            return
        self.participants[instance_id] = Player(instance_id)
        self.choices[instance_id] = None
        self.stick_ready[instance_id] = True
        self.message = "Elige con joystick / flechas y confirma con A / Enter."

    def move_choice(self, instance_id: int | str, value: float) -> None:
        # Una inclinación avanza una posición; soltar rearma el joystick.
        value = apply_deadzone(value, settings.STICK_DEADZONE)
        if value == 0:
            self.stick_ready[instance_id] = True
            return
        if abs(value) < settings.SELECTION_THRESHOLD or not self.stick_ready[instance_id]:
            return
        self.stick_ready[instance_id] = False
        if self.participants[instance_id].number is not None:
            self.message = "Pulsa B / Delete para cambiar tu personaje."
            return
        positions = (1, None, 2)
        current = positions.index(self.choices[instance_id])
        destination = max(0, min(2, current + (-1 if value < 0 else 1)))
        choice = positions[destination]
        if choice in self.players:
            self.message = f"Player {choice} ya está confirmado por el otro jugador."
            return
        self.choices[instance_id] = choice
        self.message = "Pulsa A / Enter para confirmar." if choice else "Elige izquierda o derecha."

    def confirm(self, instance_id: int | str) -> None:
        player = self.participants[instance_id]
        if player.number is not None:
            return
        choice = self.choices[instance_id]
        if choice is None:
            self.message = "Elige un personaje antes de confirmar."
            return
        if choice in self.players:
            self.message = f"Player {choice} ya está confirmado por el otro jugador."
            return
        player.select(choice)
        self.players[choice] = player
        # Si ambos exploraban el mismo personaje, sólo el primero lo reserva.
        for other_id, other_choice in self.choices.items():
            if other_id != instance_id and other_choice == choice:
                self.choices[other_id] = None
        self.message = f"Player {choice} confirmado. B / Delete para volver a elegir."
        if len(self.players) == 2:
            self.state_machine.change(
                "play", players=self.players, snapshot=self.resume_snapshot,
            )

    def cancel(self, instance_id: int | str) -> None:
        player = self.participants[instance_id]
        self.players.pop(player.number, None)
        player.unselect()
        self.message = "Puedes seguir escogiendo. A / Enter confirma."

    def on_input(self, input_id, input_data) -> None:
        self.update(0)
        # Escape pertenece al primer esquema de teclado y Gale lo publica como
        # keyboard1_cancel. En esta pantalla también funciona como regreso
        # global, incluso cuando ese teclado todavía no se ha unido.
        if input_id in ("back", "keyboard1_cancel") and input_data.pressed:
            self.state_machine.change("main_menu")
            return

        # Keyboard inputs
        if input_id.startswith("keyboard1_") or input_id.startswith("keyboard2_"):
            source = input_id.split("_")[0]
            action = input_id.split("_")[1]
            
            if not input_data.pressed:
                # Cancel ready state when releasing keys to avoid accidental double movements
                if action in ("left", "right"):
                    self.stick_ready[source] = True
                return
                
            if action == "confirm":
                if source not in self.participants:
                    self.join(source)
                else:
                    self.confirm(source)
            elif source in self.participants:
                if action == "cancel":
                    self.cancel(source)
                elif action in ("left", "right"):
                    self.move_choice(source, -1 if action == "left" else 1)
                    self.stick_ready[source] = True
            return

        # Gamepad inputs
        instance_id = getattr(input_data, "gamepad_id", None)
        if instance_id is None or not self.game.controllers.is_connected(instance_id):
            return
        if input_id == "pad_a" and input_data.pressed:
            if instance_id not in self.participants:
                self.join(instance_id)
            else:
                self.confirm(instance_id)
        elif instance_id in self.participants:
            if input_id == "pad_b" and input_data.pressed:
                self.cancel(instance_id)
            elif input_id == "pad_x":
                self.move_choice(instance_id, input_data.value)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        for number, x in ((1, 20), (2, 380)):
            rect = pygame.Rect(x, 165, 240, 220)
            pygame.draw.rect(surface, settings.PANEL_COLOR, rect, border_radius=10)
            pygame.draw.rect(surface, settings.PLAYER_COLORS[number], rect, width=2, border_radius=10)
            label = "Confirmado" if number in self.players else "Disponible"
            image = self.game.fonts["small"].render(f"Player {number} · {label}", True, settings.PLAYER_COLORS[number])
            surface.blit(image, image.get_rect(center=(rect.centerx, 188)))
        draw_text(surface, "Elección de jugador", self.game.fonts["large"], 45,
                  settings.ACCENT_COLOR)
                  
        draw_text(surface, "[Teclado 1] Mover: WASD · Acción/Entrar: Espacio · Volver: Esc",
                  self.game.fonts["small"], 95)
        draw_text(surface, "[Teclado 2] Mover: Flechas · Acción/Entrar: Enter · Volver: Supr",
                  self.game.fonts["small"], 115, settings.MUTED_COLOR)
        draw_text(surface, "[Mando] Mover: Joystick/Cruceta · Acción/Entrar: A · Volver: B",
                  self.game.fonts["small"], 135)
        controller_number = 0
        for index, (instance_id, player) in enumerate(self.participants.items()):
            choice = self.choices[instance_id]
            x = {1: 160, None: 320, 2: 480}[choice]
            y = 245 + index * 90
            color = settings.PLAYER_COLORS.get(choice, settings.MUTED_COLOR)
            player.position.update(x, y)
            player.render(surface)
            if player.uses_keyboard:
                device = "Teclado 1" if player.input_source == "keyboard1" else "Teclado 2"
            else:
                controller_number += 1
                device = f"Mando {controller_number}"
            label = self.game.fonts["small"].render(device, True, color)
            surface.blit(label, label.get_rect(center=(x, y - 40)))
            if player.uses_keyboard:
                confirm_key = "Space" if player.input_source == "keyboard1" else "Enter"
                cancel_key = "Del" if player.input_source == "keyboard1" else "Back"
            else:
                confirm_key, cancel_key = "A", "B"
            status = f"Listo · {cancel_key}" if player.number else f"{confirm_key}: listo" if choice else "Elige lado"
            label = self.game.fonts["small"].render(status, True, color)
            surface.blit(label, label.get_rect(center=(x, y + 40)))
        color = settings.PLACEMENT_INVALID_COLOR if "desconectado" in self.message.lower() else settings.TEXT_COLOR
        draw_text(surface, self.message, self.game.fonts["small"], 418, color)
        draw_text(surface, "La partida comienza cuando ambos confirman · Esc: volver",
                  self.game.fonts["small"], 452, settings.MUTED_COLOR)
