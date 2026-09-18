"""Comandos de movimiento del teclado compartidos entre personajes."""

from gale.command import Command

class SetMovementDirection(Command):
    def __init__(self, direction: str, pressed: bool) -> None:
        self.direction = direction
        self.pressed = pressed

    def execute(self, player, dt: float = 0.0) -> None:
        if self.pressed:
            player.active_directions.add(self.direction)
        else:
            player.active_directions.discard(self.direction)
            
        player.direction.update(
            int("right" in player.active_directions) - int("left" in player.active_directions),
            int("down" in player.active_directions) - int("up" in player.active_directions),
        )
