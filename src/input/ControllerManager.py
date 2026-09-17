"""Apertura y seguimiento de mandos Xbox y otros mandos mapeados por SDL."""

import pygame
from gale.input_handler import InputHandler
from pygame._sdl2 import controller


class ControllerManager:
    def __init__(self) -> None:
        pygame.joystick.init()
        controller.init()
        controller.set_eventstate(True)
        # Las referencias abiertas mantienen la recepción de eventos.
        self.controllers: dict[int, controller.Controller] = {}
        try:
            InputHandler.init_gamepads()
        except pygame.error:
            # Un mando puede desaparecer durante la inicialización de Gale.
            pass
        self.refresh()

    def refresh(self) -> None:
        """Detecta conexiones y desconexiones usando IDs de instancia."""
        connected = set()
        joystick_ids = set()
        for index in range(pygame.joystick.get_count()):
            try:
                joystick = pygame.joystick.Joystick(index)
                instance_id = joystick.get_instance_id()
                joystick_ids.add(instance_id)
                InputHandler.gamepads.setdefault(instance_id, joystick)
                if not controller.is_controller(index):
                    continue
                if instance_id not in self.controllers:
                    self.controllers[instance_id] = controller.Controller(index)
                connected.add(instance_id)
            except pygame.error:
                # El dispositivo puede desaparecer mientras se enumera.
                continue
        for instance_id in self.controllers.keys() - connected:
            self._close_device(self.controllers.pop(instance_id))
        for instance_id in InputHandler.gamepads.keys() - joystick_ids:
            self._close_device(InputHandler.gamepads.pop(instance_id))

    @staticmethod
    def _close_device(device) -> None:
        try:
            device.quit()
        except pygame.error:
            # SDL puede haber cerrado el dispositivo al desconectarlo.
            pass

    def is_connected(self, instance_id: int) -> bool:
        return instance_id in self.controllers

    def close(self) -> None:
        for device in self.controllers.values():
            self._close_device(device)
        self.controllers.clear()
        for device in InputHandler.gamepads.values():
            self._close_device(device)
        InputHandler.gamepads.clear()
