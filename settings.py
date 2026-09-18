"""Configuración de pantalla, controles y colores de Underpaid."""

import pygame
from functools import lru_cache
from pathlib import Path

from gale.input_handler import InputHandler
from gale.frames import generate_frames
from gale.tilemap import Tileset


TITLE = "Underpaid"
FPS = 60

# La lógica y los menús siempre se dibujan en estas coordenadas.
VIRTUAL_WIDTH = 640
VIRTUAL_HEIGHT = 480

# Todas las resoluciones de ventana tienen proporción 4:3.
WINDOW_RESOLUTIONS = (
    (640, 480),
    (960, 720),
    (1280, 960),
    (1920, 1440),
)

# Cambia este índice (0–3) para elegir la resolución al iniciar.
DEFAULT_RESOLUTION_INDEX = 0
WINDOW_WIDTH, WINDOW_HEIGHT = WINDOW_RESOLUTIONS[DEFAULT_RESOLUTION_INDEX]

# True para iniciar en pantalla completa; False para iniciar en ventana.
FULLSCREEN = False

BACKGROUND_COLOR = (23, 27, 38)
PANEL_COLOR = (35, 41, 56)
TEXT_COLOR = (235, 238, 245)
MUTED_COLOR = (164, 174, 194)
ACCENT_COLOR = (246, 190, 76)

PLAYER_COLORS = {1: (82, 169, 255), 2: (255, 116, 128)}
PLAYER_SPEED = 180
PLAYER_FRAME_WIDTH = 32
PLAYER_FRAME_HEIGHT = 64
# Sólo la mitad inferior del personaje ocupa espacio en el suelo.
PLAYER_COLLISION_WIDTH = PLAYER_FRAME_WIDTH
PLAYER_COLLISION_HEIGHT = PLAYER_FRAME_HEIGHT // 2
PLAYER_FRAME_INTERVAL = 0.12
STICK_DEADZONE = 0.2
SELECTION_THRESHOLD = 0.6
KEYBOARD_INPUT = "keyboard"

BASE_DIR = Path(__file__).resolve().parent

# La sala reutiliza los tiles e IDs de 06-princess, a escala 2:1.
TILE_SIZE = 16
TILE_SCALE = 2
TILE_RENDER_SIZE = TILE_SIZE * TILE_SCALE
CLOCK_START_HOUR = 8
CLOCK_END_HOUR = 16
SECONDS_PER_GAME_HOUR = 60
MATCH_DURATION = (CLOCK_END_HOUR - CLOCK_START_HOUR) * SECONDS_PER_GAME_HOUR
MAX_STARS = 5
CLOCK_BAR_HEIGHT = TILE_RENDER_SIZE
CLOCK_BAR_COLOR = (255, 255, 255)
PLACEMENT_VALID_COLOR = (40, 220, 80)
PLACEMENT_INVALID_COLOR = (240, 50, 50)
PLACEMENT_UNLOAD_COLOR = (255, 220, 60)
MAP_WIDTH = VIRTUAL_WIDTH // TILE_RENDER_SIZE
MAP_HEIGHT = (VIRTUAL_HEIGHT - CLOCK_BAR_HEIGHT) // TILE_RENDER_SIZE
MAP_RENDER_OFFSET_X = (VIRTUAL_WIDTH - MAP_WIDTH * TILE_RENDER_SIZE) // 2
MAP_RENDER_OFFSET_Y = CLOCK_BAR_HEIGHT

TILE_TOP_LEFT_CORNER = 4
TILE_TOP_RIGHT_CORNER = 5
TILE_BOTTOM_LEFT_CORNER = 23
TILE_BOTTOM_RIGHT_CORNER = 24
TILE_FLOORS = (
    7, 8, 9, 10, 11, 12, 13,
    26, 27, 28, 29, 30, 31, 32,
    45, 46, 47, 48, 49, 50, 51,
    64, 65, 66, 67, 68, 69, 70,
    88, 89, 107, 108,
)
TILE_TOP_WALLS = (58, 59, 60)
TILE_BOTTOM_WALLS = (79, 80, 81)
TILE_LEFT_WALLS = (77, 96, 115)
TILE_RIGHT_WALLS = (78, 97, 116)
BOX_SIZES = {
    "large": (2 * TILE_RENDER_SIZE, 2 * TILE_RENDER_SIZE),
    "medium": (TILE_RENDER_SIZE, TILE_RENDER_SIZE),
    "small": (TILE_RENDER_SIZE // 2, TILE_RENDER_SIZE // 2),
}
BOX_SPRITES = {
    "large": "big_box.png",
    "medium": "medium_box.png",
    "small": "small_box.png",
}
BOX_SPEED_MULTIPLIERS = {
    "large": 1 / 2,
    "medium": 2 / 3,
    "small": 1,
}
POT_LIFT_DURATION = 0.3
PRODUCT_NAMES = ("Camisa", "Audífonos", "Pantalones", "Teléfono", "Zapatos")
BOX_CAPACITIES = {"large": None, "medium": 5, "small": 3}
ORDERS_PER_PLAYER = 2
ORDER_MIN_PRODUCTS = 2
ORDER_MAX_PRODUCTS = 5
POINTS_PER_ORDER = 100
INCORRECT_ORDER_PENALTY = 50


@lru_cache(maxsize=1)
def load_product_frames() -> tuple[pygame.Surface, ...]:
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / "products.png").convert_alpha()
    frames = generate_frames(sheet, 32, 32)
    if len(frames) != len(PRODUCT_NAMES):
        raise ValueError("El spritesheet de productos requiere cinco sprites de 32 × 32")
    return tuple(sheet.subsurface(rect).copy() for rect in frames)


@lru_cache(maxsize=3)
def load_box_sprite(box_type: str = "large") -> pygame.Surface:
    if box_type not in BOX_SPRITES:
        raise ValueError("Tipo de caja inválido: usa large, medium o small")
    return pygame.image.load(BASE_DIR / "assets" / "graphics" / BOX_SPRITES[box_type]).convert_alpha()


@lru_cache(maxsize=3)
def load_box_image(box_type: str) -> pygame.Surface:
    if box_type not in BOX_SIZES:
        raise ValueError("Tipo de caja inválido: usa large, medium o small")
    # Escalado sin suavizado para conservar el estilo pixel art del sprite.
    return pygame.transform.scale(load_box_sprite(box_type), BOX_SIZES[box_type])


@lru_cache(maxsize=1)
def load_table_sprite() -> pygame.Surface:
    return pygame.image.load(BASE_DIR / "assets" / "graphics" / "table.png").convert_alpha()


@lru_cache(maxsize=1)
def load_shelf_frames() -> tuple[pygame.Surface, ...]:
    """Primer sprite: repisa vacía; segundo: repisa con productos."""
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / "shelf.png").convert_alpha()
    frames = generate_frames(sheet, 32, 64)
    if len(frames) < 2:
        raise ValueError("El spritesheet de repisas requiere al menos dos sprites de 32 × 64")
    return tuple(sheet.subsurface(rect).copy() for rect in frames[:2])


@lru_cache(maxsize=1)
def load_room_tileset() -> Tileset:
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / "tilesheet.png").convert_alpha()
    sheet = pygame.transform.scale(sheet, (sheet.get_width() * TILE_SCALE, sheet.get_height() * TILE_SCALE))
    return Tileset(sheet, TILE_RENDER_SIZE, TILE_RENDER_SIZE)


@lru_cache(maxsize=2)
def load_player_frames(filename: str = "player_walk.png") -> dict[str, tuple[pygame.Surface, ...]]:
    """Carga una vez el spritesheet; cada jugador conserva su propio reloj."""
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / filename).convert_alpha()
    return {
        direction: tuple(
            sheet.subsurface(pygame.Rect(
                column * PLAYER_FRAME_WIDTH, row * PLAYER_FRAME_HEIGHT,
                PLAYER_FRAME_WIDTH, PLAYER_FRAME_HEIGHT,
            )).copy()
            for column in range(4)
        )
        for row, direction in enumerate(("down", "right", "up", "left"))
    }


@lru_cache(maxsize=1)
def load_boss_frames() -> list[pygame.Surface]:
    """Carga los frames del jefe para diálogos."""
    sheet = pygame.image.load(BASE_DIR / "assets" / "graphics" / "boss_face.png").convert_alpha()
    return [
        sheet.subsurface(pygame.Rect(column * 32, 0, 32, 32)).copy()
        for column in range(2)
    ]


def create_8bit_blip(frequency: int = 450, duration_ms: int = 35, sample_rate: int = 44100) -> pygame.mixer.Sound:
    """Sintetiza una onda cuadrada retro usando NumPy (estilo Undertale)."""
    import numpy as np
    duration_sec = duration_ms / 1000.0
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    
    # Onda cuadrada
    wave = np.sign(np.sin(frequency * t * 2 * np.pi))
    
    # Fade-out lineal rápido para evitar chasquidos de audio (popping) al final
    envelope = np.linspace(1.0, 0.0, len(wave))
    wave = wave * envelope
    
    # Escalar a entero de 16 bits y bajar el volumen al 20%
    audio = np.int16(wave * 32767 * 0.2)
    
    # Duplicar para canales estéreo
    stereo_audio = np.column_stack((audio, audio))
    return pygame.sndarray.make_sound(stereo_audio)


@lru_cache(maxsize=3)
def load_dialog_sound(character: str = "default") -> pygame.mixer.Sound:
    """Genera y almacena en caché el pitido de diálogo según el personaje."""
    if character == "boss":
        # Un sonido más grave para el jefe
        return create_8bit_blip(200, 45)
    else:
        # Sonido estándar para texto sin personaje (o "normal text")
        return create_8bit_blip(450, 35)


def create_fonts() -> dict[str, pygame.font.Font]:
    """Se llama después de que Gale inicializa Pygame."""
    return {
        "small": pygame.font.Font(None, 22),
        "medium": pygame.font.Font(None, 30),
        "large": pygame.font.Font(None, 64),
    }


for key, action in (
    # Jugador 1
    (pygame.K_w, "keyboard1_up"),
    (pygame.K_s, "keyboard1_down"),
    (pygame.K_a, "keyboard1_left"),
    (pygame.K_d, "keyboard1_right"),
    (pygame.K_SPACE, "keyboard1_confirm"),
    (pygame.K_ESCAPE, "keyboard1_cancel"),
    (pygame.K_q, "keyboard1_orders"),
    
    # Jugador 2
    (pygame.K_UP, "keyboard2_up"),
    (pygame.K_DOWN, "keyboard2_down"),
    (pygame.K_LEFT, "keyboard2_left"),
    (pygame.K_RIGHT, "keyboard2_right"),
    (pygame.K_RETURN, "keyboard2_confirm"),
    (pygame.K_DELETE, "keyboard2_cancel"),
    (pygame.K_BACKSPACE, "keyboard2_orders"),
):
    InputHandler.set_keyboard_action(key, action)

InputHandler.set_mouse_click_action(pygame.BUTTON_LEFT, "click")
InputHandler.set_mouse_motion_action(None, "mouse_move")

# Botones y ejes estandarizados por el mapeo de SDL para mandos Xbox.
for button, action in (
    (pygame.CONTROLLER_BUTTON_A, "pad_a"),
    (pygame.CONTROLLER_BUTTON_B, "pad_b"),
    (pygame.CONTROLLER_BUTTON_START, "pad_pause"),
    (pygame.CONTROLLER_BUTTON_X, "pad_orders"),
    (pygame.CONTROLLER_BUTTON_DPAD_UP, "pad_up"),
    (pygame.CONTROLLER_BUTTON_DPAD_DOWN, "pad_down"),
    (pygame.CONTROLLER_BUTTON_DPAD_LEFT, "pad_left"),
    (pygame.CONTROLLER_BUTTON_DPAD_RIGHT, "pad_right"),
):
    InputHandler.set_gamepad_button_action(button, action)

InputHandler.set_gamepad_axis_action(pygame.CONTROLLER_AXIS_LEFTX, "pad_x")
InputHandler.set_gamepad_axis_action(pygame.CONTROLLER_AXIS_LEFTY, "pad_y")
