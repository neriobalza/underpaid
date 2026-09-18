"""Jornada cooperativa de recepción, empaquetado y entrega de pedidos."""

import pygame
from gale.state import BaseState
from gale.timer import Timer

import settings
from src.gui.Menu import draw_text
from src.world.Room import Room
from src.gui.FloatingDialog import FloatingDialog
from src.states.game.PauseState import PauseState
from src.gui.OrdersPanel import OrdersPanel


class PlayState(BaseState):
    def __init__(self, state_machine, game):
        super().__init__(state_machine)
        self.game = game

    def enter(self, players) -> None:
        self.players = dict(players)
        if set(self.players) != {1, 2} or any(
            player.number != number for number, player in self.players.items()
        ) or len({player.input_source for player in self.players.values()}) != 2:
            raise ValueError("La partida requiere dos personajes con entradas diferentes")
        self.room = Room()
        self.room.start_day()
        self.room.on_dispatch_depart = self.on_dispatch_depart
        self.show_orders_panel = False
        self.orders_held = set()
        self.orders_panel = OrdersPanel()
        for player in self.players.values():
            player.stop()
            player.position.update(self.room.spawn_position(player.number))
        self.game_minutes = float(settings.CLOCK_START_HOUR * 60)
        # Gale actualiza Timer una vez por frame en su bucle de juego.
        self.match_clock = Timer.tween(
            settings.MATCH_DURATION,
            [(self, {"game_minutes": float(settings.CLOCK_END_HOUR * 60)})],
            on_finish=self._finish_match,
        )
        
        portrait_frames = settings.load_boss_frames()
        
        self.active_dialog = FloatingDialog(
            text="Q / X: consulta tus pedidos.\nDescarga las cajas en repisas.\nEmpaca y entrega en amarillo.",
            font=self.game.fonts["medium"],
            portrait_frames=portrait_frames,
            sound=settings.load_dialog_sound("boss")
        )

    @property
    def clock_text(self) -> str:
        hours, minutes = divmod(int(self.game_minutes), 60)
        period = "AM" if hours % 24 < 12 else "PM"
        return f"{hours % 12 or 12}:{minutes:02d} {period}"

    def on_dispatch_depart(self, delivered, incorrect, taken_boxes):
        self.room.delivered_orders.update(delivered)
        self.room.incorrect_boxes.extend(incorrect)
        
        for box in incorrect:
            self.game.stars = max(0, self.game.stars - 0.05)
            if box.last_carrier_number and box.last_carrier_number in self.players:
                player = self.players[box.last_carrier_number]
                player.salary -= 5
                self.spawn_penalty_text(player, "-5¢")

    def spawn_penalty_text(self, player, text):
        import types
        if not hasattr(self, "penalties"):
            self.penalties = []
        pen = types.SimpleNamespace(text=text, x=float(player.position.x), y=float(player.position.y - 60), alpha=255.0)
        def finish():
            if pen in getattr(self, "penalties", []):
                self.penalties.remove(pen)
        pen.tween = Timer.tween(2.0, [(pen, {"y": pen.y - 30, "alpha": 0.0})], on_finish=finish)
        self.penalties.append(pen)

    def _finish_match(self) -> None:
        if self.state_machine.current is self:
            matched, incorrect = self.room.delivery_report()
            delivered = len(matched)
            points = delivered * settings.POINTS_PER_ORDER - len(incorrect) * settings.INCORRECT_ORDER_PENALTY
            self.game.delivered += delivered
            self.game.score += points
            if delivered < self.room.order_count:
                self.game.stars = max(0, self.game.stars - 1)
            self.state_machine.change("game_over", players=self.players, delivered=delivered,
                                      total=self.room.order_count, incorrect=len(incorrect), points=points)

    def update(self, dt: float) -> None:
        if getattr(self, "active_dialog", None):
            self.active_dialog.update(dt)
            if self.active_dialog.is_finished:
                self.active_dialog = None
            return

        connected = {
            number: player for number, player in self.players.items()
            if player.is_connected(self.game.controllers)
        }
        if len(connected) != 2:
            self.state_machine.change("player_select", players=connected)
            return
            
        self.room.update(dt)
        for player in self.players.values():
            if self.show_orders_panel:
                continue
            player.update(dt, self.room, self.room.obstacles, self.players.values())
            if player.interact_requested:
                player.interact_requested = False
                self.room.interact(player, self.players.values())
        if self.room.order_count and self.room.count_deliveries() == self.room.order_count:
            self._finish_match()

    def exit(self) -> None:
        if hasattr(self, "match_clock"):
            self.match_clock.remove()
        for player in getattr(self, "players", {}).values():
            player.stop()
            player.clear_carrying()

    def reset_input(self) -> None:
        self.orders_held.clear()
        for player in self.players.values():
            player.direction.update(0, 0)
            player.keyboard_keys.clear()
            player.interact_held = False
            player.interact_requested = False

    def on_input(self, input_id, input_data) -> None:
        if input_id in ("back", "pad_pause") and input_data.pressed:
            self.state_machine.push(PauseState(self.state_machine, self.game), play_state=self)
            return
        if input_id in ("keyboard_orders", "pad_orders"):
            owner = next((player.number for player in self.players.values()
                          if (input_id == "keyboard_orders" and player.uses_keyboard)
                          or (input_id == "pad_orders" and player.controller_id == input_data.gamepad_id)), None)
            if owner is not None:
                if input_data.pressed and owner not in self.orders_held:
                    self.show_orders_panel = not self.show_orders_panel
                    for p in self.players.values():
                        p.stop()
                        p.interact_held = False
                        p.interact_requested = False
                if input_data.pressed:
                    self.orders_held.add(owner)
                else:
                    self.orders_held.discard(owner)
            return
        if getattr(self, "active_dialog", None):
            self.active_dialog.on_input(input_id, input_data)
            return

        for player in self.players.values():
            if not self.show_orders_panel:
                player.on_input(input_id, input_data)

    def render(self, surface) -> None:
        surface.fill(settings.BACKGROUND_COLOR)
        self.room.render(surface)
        entities = list(self.players.values()) + [obj for obj in self.room.obstacles if obj.solid]
        for entity in sorted(entities, key=lambda entity: entity.hitbox.bottom):
            entity.render(surface)
        self.room.render_placement(surface, self.players.values())
        for player in self.players.values():
            hint = self.room.interaction_hint(player)
            if hint and not self.show_orders_panel:
                key = "Enter" if player.uses_keyboard else "A"
                lines = [f"{key}: {hint}"]
                action, target = self.room.next_action(player)
                if action == "unload":
                    quantity = player.carrying.contents[target.product_type]
                    lines.append(f"1 unidad por pulsación · En la caja: {quantity}")
                box = player.carrying if player.carrying is not None and player.carrying.is_order else None
                if action in ("pack", "take_table_box", "box_full"):
                    box = target.box
                if box is not None and box.quantity:
                    lines += [f"{settings.PRODUCT_NAMES[product_type]} × {quantity}"
                              for product_type, quantity in sorted(box.contents.items())]
                images = [self.game.fonts["small"].render(
                    line, True, settings.ACCENT_COLOR if action == "unload" and index == 0 else settings.TEXT_COLOR,
                ) for index, line in enumerate(lines)]
                line_height = self.game.fonts["small"].get_linesize()
                rect = pygame.Rect(0, 0, max(image.get_width() for image in images), len(images) * line_height)
                rect.midbottom = round(player.position.x), round(player.position.y) - 38
                rect.clamp_ip(pygame.Rect(4, settings.CLOCK_BAR_HEIGHT + 4,
                                         settings.VIRTUAL_WIDTH - 8, settings.VIRTUAL_HEIGHT - settings.CLOCK_BAR_HEIGHT - 8))
                pygame.draw.rect(surface, settings.PANEL_COLOR, rect.inflate(8, 4), border_radius=4)
                for index, image in enumerate(images):
                    surface.blit(image, (rect.x, rect.y + index * line_height))
                    
        if hasattr(self, "penalties"):
            for pen in self.penalties:
                img = self.game.fonts["small"].render(pen.text, True, settings.PLACEMENT_INVALID_COLOR)
                img.set_alpha(int(pen.alpha))
                surface.blit(img, (round(pen.x) - img.get_width()//2, round(pen.y)))
                
        pygame.draw.rect(surface, settings.CLOCK_BAR_COLOR,
                         (0, 0, settings.VIRTUAL_WIDTH, settings.CLOCK_BAR_HEIGHT))
        draw_text(surface, self.clock_text, self.game.fonts["medium"],
                  settings.CLOCK_BAR_HEIGHT // 2, settings.BACKGROUND_COLOR)
                  
        stars_str = f"{self.game.stars:.2f}".rstrip('0').rstrip('.')
        label = self.game.fonts["small"].render(
            f"Día {self.game.day} · {stars_str}/{settings.MAX_STARS} estrellas",
            True, settings.BACKGROUND_COLOR,
        )
        surface.blit(label, (20, 7))
        
        salary1 = self.players[1].salary if 1 in self.players else 0
        salary2 = self.players[2].salary if 2 in self.players else 0
        label_salary = self.game.fonts["small"].render(f"Salarios: J1: {salary1}¢ | J2: {salary2}¢", True, settings.BACKGROUND_COLOR)
        surface.blit(label_salary, (settings.VIRTUAL_WIDTH - label_salary.get_width() - 8, 7))

        if getattr(self, "active_dialog", None):
            self.active_dialog.render(surface)
        if self.show_orders_panel:
            self.orders_panel.render(surface, self.room, 1)
