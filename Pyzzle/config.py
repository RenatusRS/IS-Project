import os

# parameters
HEIGHT = 676
WIDTH = 880
SIDE_WIDTH = 240
TILE_SIZE = 64
HALF_PADDING = 2
FRAME_RATE = 60
LINE_PADDING = 20
LETTER_FONT = None
VARS_FONT = None
VARS_LARGER_FONT = None
INFO_FONT = None
PADDING = 4
TIMER_MARGINS = LINE_PADDING, 15, 100, 30, 3
DOMAIN_LEN = 7
DOMAIN_WIDTH = int(SIDE_WIDTH * 0.8)
SURFACE_HEIGHT = (HEIGHT - (DOMAIN_LEN + 1) * PADDING) // DOMAIN_LEN
SUBSURFACE_HEIGHT = HEIGHT // 11
SCROLL_KEY = 'scroll'
ALGORITHMS = 'algorithms'

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (64, 64, 64)
RED = (192, 0, 0)
GREEN = (0, 208, 0)
DARK_GREEN = (0, 192, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)

GR_LEN = 101
R_to_G = [((255 * (100 - i)) / 100, (255 * i) / 100, 0) for i in range(GR_LEN)]

GAME_FOLDER = os.path.dirname(__file__)
IMG_FOLDER = os.path.join(GAME_FOLDER, 'img')
SCHEMA_FOLDER = os.path.join(GAME_FOLDER, 'schemas')
WORDS_FOLDER = os.path.join(GAME_FOLDER, 'words')
FONT_FOLDER = os.path.join(GAME_FOLDER, 'fonts')
