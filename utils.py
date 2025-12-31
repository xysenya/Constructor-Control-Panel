from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QFileDialog
from config import FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR

def hex_to_rgba(hex_color):
    """Преобразует цвет из #RRGGBB в кортеж (r, g, b, 255)."""
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

def get_font_name(is_bold):
    """Возвращает имя шрифта в зависимости от жирности."""
    return FONT_FAMILY_BOLD if is_bold else FONT_FAMILY_REGULAR

def get_fitted_font_size(text, is_bold, initial_font_size, max_width):
    """
    Подбирает размер шрифта так, чтобы текст помещался в заданную ширину.
    """
    if not text:
        return initial_font_size

    font_size = initial_font_size
    font_name = get_font_name(is_bold)
    
    # Создаем шрифт
    font = QFont(font_name, font_size)
    if is_bold:
        font.setBold(True)
    
    # Разбиваем на строки, ищем самую длинную
    lines = text.replace(' ', '\n').split('\n')
    longest_line = max(lines, key=len) if lines else ""
    
    fm = QFontMetrics(font)
    width = fm.horizontalAdvance(longest_line)
    
    while width > max_width and font_size > 5:
        font_size -= 1
        font.setPointSize(font_size)
        fm = QFontMetrics(font)
        width = fm.horizontalAdvance(longest_line)
        
    return font_size

def mark_as_changed():
    """Заглушка для отметки изменений."""
    pass

def open_file_dialog_windows(parent=None, title="Открыть файл", filter_desc="Audio Files", filter_ext="*.wav *.mp3"):
    """
    Открывает диалог выбора файла Qt.
    """
    file_path, _ = QFileDialog.getOpenFileName(parent, title, "", f"{filter_desc} ({filter_ext})")
    return file_path if file_path else None
