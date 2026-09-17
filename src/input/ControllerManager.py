"""Apertura y seguimiento de mandos Xbox y otros mandos mapeados por SDL."""

import pygame
from pygame._sdl2 import controller


class ControllerManager:
    def __init__(self) -> None:
        pygame.joystick.init()
        controller.init()
        controller.set_eventstate(True)
        # Las referencias abiertas mantienen la recepción de eventos.
        self.controllers: dict[int, controller.Controller] = {}
        self.refresh()

    def refresh(self) -> None:
        """Detecta conexiones y desconexiones usando IDs de instancia."""
        connected = set()
        for index in range(pygame.joystick.get_count()):
            try:
                if not controller.is_controller(index):
                    continue
                joystick = pygame.joystick.Joystick(index)
                instance_id = joystick.get_instance_id()
                if instance_id not in self.controllers:
                    self.controllers[instance_id] = controller.Controller(index)
                connected.add(instance_id)
            except pygame.error:
                # El dispositivo puede desaparecer mientras se enumera.
                continue
        for instance_id in self.controllers.keys() - connected:
            self.controllers.pop(instance_id).quit()

    def is_connected(self, instance_id: int) -> bool:
        return instance_id in self.controllers

    def close(self) -> None:
        for device in self.controllers.values():
            device.quit()
        self.controllers.clear()
