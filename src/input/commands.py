"""Comandos de movimiento del teclado compartidos entre personajes."""

import pygame
from gale.command import Command


class SetMovementKey(Command):
    def __init__(self, key: int, pressed: bool) -> None:
        self.key = key
        self.pressed = pressed

    def execute(self, player, dt: float = 0.0) -> None:
        if self.pressed:
            player.keyboard_keys.add(self.key)
        else:
            player.keyboard_keys.discard(self.key)
        player.direction.update(
            int(pygame.K_d in player.keyboard_keys) - int(pygame.K_a in player.keyboard_keys),
            int(pygame.K_s in player.keyboard_keys) - int(pygame.K_w in player.keyboard_keys),
        )


MOVEMENT_COMMANDS = {
    action: (SetMovementKey(key, True), SetMovementKey(key, False))
    for action, key in (
        ("keyboard_up", pygame.K_w), ("keyboard_down", pygame.K_s),
        ("keyboard_left", pygame.K_a), ("keyboard_right", pygame.K_d),
    )
}
