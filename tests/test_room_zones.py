import unittest
import pygame
from src.world.Room import Room
from src.world.Box import Box

class RoomZonesTest(unittest.TestCase):
    def test_room_loads_zones_from_tiled(self):
        # Desactivar video de pygame para tests
        import os
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        pygame.init()
        pygame.display.set_mode((640, 480))
        
        room = Room()
        
        # Verificar que no está usando las coordenadas por defecto
        self.assertNotEqual(room.dispatch_area.topleft, (0, 0))
        self.assertNotEqual(room.unloading_area.topleft, (0, 0))
        
        # Verificar que encontró la caja en tiled (deberían ser 2 cajas ahora)
        self.assertEqual(len(room.objects), 2)
        
        # Verificar que las cajas iniciales NO están en la zona de carga (dispatch)
        self.assertEqual(room.count_deliveries(), 0)
        
        # Forzar una caja en la zona de carga (dispatch)
        box = room.objects[0]
        box.position.update(room.dispatch_area.centerx, room.dispatch_area.centery)
        self.assertEqual(room.count_deliveries(), 1)
        
        # Forzar las dos cajas en la zona
        box2 = room.objects[1]
        box2.position.update(room.dispatch_area.centerx, room.dispatch_area.centery)
        self.assertEqual(room.count_deliveries(), 2)

if __name__ == '__main__':
    unittest.main()
