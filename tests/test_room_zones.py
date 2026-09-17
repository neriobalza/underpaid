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
        
        # Hay dos cajas de recepción y dos cajas de pedidos.
        self.assertEqual(len(room.objects), 4)
        orders = [box for box in room.objects if box.is_order]
        self.assertEqual(len(orders), 2)
        
        # Verificar que las cajas iniciales NO están en la zona de carga (dispatch)
        self.assertEqual(room.count_deliveries(), 0)
        
        # Forzar una caja en la zona de carga (dispatch)
        box = orders[0]
        box.position.update(room.dispatch_area.centerx, room.dispatch_area.centery)
        self.assertEqual(room.count_deliveries(), 1)
        
        # Forzar las dos cajas en la zona
        box2 = orders[1]
        box2.position.update(room.dispatch_area.centerx, room.dispatch_area.centery)
        self.assertEqual(room.count_deliveries(), 2)

if __name__ == '__main__':
    unittest.main()
