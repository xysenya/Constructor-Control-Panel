import os
import sys

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ШРИФТОВ ---
FONT_FAMILY_REGULAR = 'Epilepsy Sans'
FONT_FAMILY_BOLD = 'Epilepsy Sans B'
FONT_FAMILY_FALLBACK = 'Arial'  # Запасной шрифт

# --- КОНФИГУРАЦИЯ СЕТКИ ---
ROWS = 7
COLS = 7
EXTRA_COLS = 2
EXTRA_ROWS_TOP = 5
EXTRA_ROWS_BOTTOM = 1
DEFAULT_COLOR = "#666666"
DEFAULT_TITLE = "Конструктор: Панель Управления"
BASE_FONT_SIZE_NUMBER = 24
BASE_FONT_SIZE_NAME = 16
BASE_FONT_SIZE_TITLE = 36
BASE_FONT_SIZE_COORDS = 24

# Координаты ячеек внешнего контура по часовой стрелке, начиная с A1 (6,0)
OUTER_CONTOUR_COORDS = [
    (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 6),
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),
    (0, 5), (0, 4), (0, 3), (0, 2), (0, 1), (0, 0),
    (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)
]

# --- ПАРАМЕТРЫ ОКНА ---
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
CELL_SIZE = 100
CELL_SPACING = 4
CELL_RADIUS = 15
GRID_COLOR = (50, 50, 50, 255)
HIGHLIGHT_COLOR = (255, 215, 0, 255)
REMOTE_HIGHLIGHT_COLOR = (237, 125, 49, 255)
PATH_COLOR = (255, 165, 0, 255)
PATH_POINT_COLOR = (0, 0, 255, 255)

# --- ПАРАМЕТРЫ ВКЛАДОК ---
tab_names = [
    "Карта Серого уровня", "Оранжевый уровень", "Фиолетовый уровень",
    "Предметы", "Персонажи игроков", "NPC", "Сюжет", "Заметки"
]

def get_base_dir():
    """
    Возвращает путь к папке, где находится исполняемый файл (exe) или скрипт (py).
    В этой папке должны лежать все ресурсы.
    """
    if getattr(sys, 'frozen', False):
        # Если запущено как exe
        return os.path.dirname(sys.executable)
    else:
        # Если запущено как скрипт
        return os.path.dirname(os.path.abspath(__file__))

# Базовая директория программы
BASE_DIR = get_base_dir()
SCRIPT_DIR = BASE_DIR # Для совместимости со старым кодом

# --- ПУТИ К РЕСУРСАМ ---
# Все папки ищем относительно BASE_DIR
BASE_ROOM_SOUNDS_DIR = os.path.join(BASE_DIR, "BaseRoomSounds")
AUDIO_PANEL_SOUNDS_DIR = os.path.join(BASE_DIR, "AudioPanelSounds")
SYNTH_SPEECH_DIR = os.path.join(BASE_DIR, "SynthSpeech")
TIMER_SOUNDS_DIR = os.path.join(BASE_DIR, "TimerSounds")
PLAYER_BUTTONS_DIR = os.path.join(BASE_DIR, "PlayerButtons")
CHAR_LIST_DIR = os.path.join(BASE_DIR, "CharList")
BASE_MUSIC_DIR = os.path.join(BASE_DIR, "BaseMusic")
ORANGE_LVL_DIR = os.path.join(BASE_DIR, "OrangeLVL")
PURPLE_LVL_DIR = os.path.join(BASE_DIR, "PurpleLVL")
LORE_DIR = os.path.join(BASE_DIR, "Lore")
ITEMS_DIR = os.path.join(BASE_DIR, "Items")
VISUAL_TAB_DIR = os.path.join(BASE_DIR, "VisualTab")
WHITE_ROOM_MOVE_DIR = os.path.join(BASE_DIR, "WhiteRoomMove")

# Создаем папки для записи, если их нет
for d in [AUDIO_PANEL_SOUNDS_DIR, SYNTH_SPEECH_DIR]:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            pass
