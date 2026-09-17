import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import pygame

# Initialize pygame display so we can load images if needed
pygame.init()
pygame.display.set_mode((640, 480))

from src.world.Room import Room
room = Room()

print(f"dispatch_area: {room.dispatch_area}")
print(f"unloading_area: {room.unloading_area}")
print(f"boxes count: {len(room.objects)}")
for i, box in enumerate(room.objects):
    print(f"  Box {i}: x={box.position.x}, y={box.position.y}")

