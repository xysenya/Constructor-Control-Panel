from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QGroupBox, QScrollArea, QFrame, QLayout, QGridLayout, QSizePolicy, QPushButton, QStackedLayout, QTextEdit, QRadioButton, QButtonGroup, QBoxLayout)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QPen, QRadialGradient, QBrush
from config import FONT_FAMILY_BOLD, CHAR_LIST_DIR, ORANGE_LVL_DIR
import os

POINTS_OF_INTEREST = {
    "white_room": {"pos": (280, 71), "file": "Белая Зала.png", "group": "white_room", "name": "Белая Зала", "legend_icon": "Белая ЗалаЛ.png"}, 
    "hotel": {"pos": (267, 419), "file": "Отель.png", "group": "hotel", "name": "Отель", "legend_icon": "ОтельЛ.png"},
    "metro": {"pos": (451, 586), "file": "Метро.png", "group": "metro", "name": "Метро", "legend_icon": "МетроЛ.png"},
    
    "sun": {"pos": (132, 56), "file": "Солнце.png", "group": "places", "name": "Солнце", "legend_icon": "СолнцеЛ.png"},
    "firmament": {"pos": (67, 215), "file": "Твердь.png", "group": "places", "name": "Твердь", "legend_icon": "ТвердьЛ.png"},
    "blood": {"pos": (475, 110), "file": "Кровь.png", "group": "places", "name": "Кровь", "legend_icon": "КровьЛ.png"},
    "moon": {"pos": (424, 474), "file": "Луна.png", "group": "places", "name": "Луна", "legend_icon": "ЛунаЛ.png"},
    "sky": {"pos": (486, 295), "file": "Небо.png", "group": "places", "name": "Небо", "legend_icon": "НебоЛ.png"},
    "ash": {"pos": (164, 461), "file": "Пепел.png", "group": "places", "name": "Пепел", "legend_icon": "ПепелЛ.png"},
    "void": {"pos": (252, 303), "file": "Пустота.png", "group": "places", "name": "Пустота", "legend_icon": "ПустотаЛ.png"},
    
    "cont1": {"pos": (56, 113), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 1", "legend_icon": "КонтейнерЛ.png"},
    "cont2": {"pos": (290, 191), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 2", "legend_icon": "КонтейнерЛ.png"},
    "cont3": {"pos": (546, 219), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 3", "legend_icon": "КонтейнерЛ.png"},
    "cont4": {"pos": (113, 305), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 4", "legend_icon": "КонтейнерЛ.png"},
    "cont5": {"pos": (344, 383), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 5", "legend_icon": "КонтейнерЛ.png"},
    "cont6": {"pos": (59, 536), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 6", "legend_icon": "КонтейнерЛ.png"},
    "cont7": {"pos": (234, 515), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 7", "legend_icon": "КонтейнерЛ.png"},
    "cont8": {"pos": (539, 430), "file": "КонтейнерЛ.png", "group": "containers", "name": "Контейнер 8", "legend_icon": "КонтейнерЛ.png"},
    
    "shelt1": {"pos": (325, 120), "file": "Убежище.png", "group": "shelters", "name": "Убежище 1", "legend_icon": "УбежищеЛ.png"},
    "shelt2": {"pos": (45, 381), "file": "Убежище.png", "group": "shelters", "name": "Убежище 2", "legend_icon": "УбежищеЛ.png"},
    "shelt3": {"pos": (376, 323), "file": "Убежище.png", "group": "shelters", "name": "Убежище 3", "legend_icon": "УбежищеЛ.png"},
    "shelt4": {"pos": (289, 582), "file": "Убежище.png", "group": "shelters", "name": "Убежище 4", "legend_icon": "УбежищеЛ.png"},
    
    "stor1": {"pos": (533, 133), "file": "Хранилище.png", "group": "storages", "name": "Хранилище 1", "legend_icon": "ХранилищеЛ.png"},
    "stor2": {"pos": (458, 361), "file": "Хранилище.png", "group": "storages", "name": "Хранилище 2", "legend_icon": "ХранилищеЛ.png"},
    "stor3": {"pos": (151, 553), "file": "Хранилище.png", "group": "storages", "name": "Хранилище 3", "legend_icon": "ХранилищеЛ.png"},
    "stor4": {"pos": (536, 540), "file": "Хранилище.png", "group": "storages", "name": "Хранилище 4", "legend_icon": "ХранилищеЛ.png"},
}

PLAYER_LEGEND_MAPPING = {
    "white_room": ("Белая Зала.png", "Белая Зала"),
    "hotel": ("ОтельЛ.png", "Отель"),
    "metro": ("МетроЛ.png", "Метро"),
    "places": ("МестаСилы.png", "Места Силы"),
    "shelters": ("УбежищеЛ.png", "Убежище"),
    "storages": ("ХранилищеЛ.png", "Хранилище"),
    "containers": ("КонтейнерЛ.png", "Контейнер"),
}

LEGEND_ITEMS = [
    ("ОтельЛ.png", "Отель", 0),
    ("МетроЛ.png", "Метро", 0),
    ("МестаСилы.png", "Места Силы", 0),
    ("КровьЛ.png", "Исцеление материи, создание чувств", 1),
    ("ПепелЛ.png", "Уничтожение материи и чувств", 1),
    ("НебоЛ.png", "Управление сознанием других и его законами", 1),
    ("СолнцеЛ.png", "Обретение знаний и исцеление сознания", 1),
    ("ЛунаЛ.png", "Травмирование сознания и сокрытие знаний и воспоминаний других людей", 1),
    ("ТвердьЛ.png", "Изменение материи и управление ей", 1),
    ("ПустотаЛ.png", "Управление временем и пространством", 1),
    ("ХранилищеЛ.png", "Хранилище", 0),
    ("УбежищеЛ.png", "Убежище", 0),
    ("КонтейнерЛ.png", "Контейнер", 0), 
]

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margin, _, _, _ = self.getContentsMargins()
        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spaceX = self.spacing()
        spaceY = self.spacing()

        for item in self.itemList:
            wid = item.widget()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        return y + lineHeight - rect.y()

class LegendItemWidget(QWidget):
    clicked = pyqtSignal(str, str)

    def __init__(self, image_file, text, indent_level=0, parent=None):
        super().__init__(parent)
        self.text = text
        self.image_file = image_file
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)
        
        if indent_level > 0:
            layout.addSpacing(indent_level * 20)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(30, 30)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        path = os.path.join(ORANGE_LVL_DIR, image_file)
        if os.path.exists(path):
            pixmap = QPixmap(path)
            self.icon_label.setPixmap(pixmap.scaled(
                self.icon_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        
        layout.addWidget(self.icon_label)
        
        lbl_text = QLabel(text)
        lbl_text.setWordWrap(True)
        lbl_text.setStyleSheet("color: #cccccc;")
        layout.addWidget(lbl_text)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.text != "Места Силы":
                self.clicked.emit(self.text, self.image_file)
        super().mousePressEvent(event)

class InteractiveMapLabel(QWidget):
    element_clicked = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        
        self.base_map_pixmap = None
        self.element_pixmaps = {}
        self.visible_groups = set()
        self.message = ""
        
        self.set_map_image("Map0.png")
        self.load_element_images()

    def set_map_image(self, filename):
        self.image_path = os.path.join(ORANGE_LVL_DIR, filename) 
        if os.path.exists(self.image_path):
            self.base_map_pixmap = QPixmap(self.image_path)
            self.message = ""
        else:
            self.base_map_pixmap = None
            self.message = f"Карта не найдена:\n{filename}"
        self.update()

    def load_element_images(self):
        loaded_files = {}
        for key, data in POINTS_OF_INTEREST.items():
            filename = data["file"]
            if filename not in loaded_files:
                path = os.path.join(ORANGE_LVL_DIR, filename)
                if os.path.exists(path):
                    loaded_files[filename] = QPixmap(path)
                else:
                    print(f"Image not found: {path}")
                    loaded_files[filename] = None
            
            if loaded_files[filename]:
                self.element_pixmaps[key] = loaded_files[filename]

    def set_group_visible(self, group, visible):
        if visible:
            self.visible_groups.add(group)
        else:
            self.visible_groups.discard(group)
        self.update()

    def draw_content(self, painter, rect, visible_groups, map_pixmap):
        if map_pixmap:
            scaled_map = map_pixmap.scaled(
                rect.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            offset_x = rect.x() + (rect.width() - scaled_map.width()) // 2
            offset_y = rect.y() + (rect.height() - scaled_map.height()) // 2
            painter.drawPixmap(offset_x, offset_y, scaled_map)
            
            base_width = 600.0
            base_height = 600.0
            
            scale_x = scaled_map.width() / base_width
            scale_y = scaled_map.height() / base_height
            
            for key, data in POINTS_OF_INTEREST.items():
                if data["group"] in visible_groups:
                    if key in self.element_pixmaps:
                        pixmap = self.element_pixmaps[key]
                        
                        base_scale_factor = 3.0
                        if key == "hotel":
                            base_scale_factor /= 1.5
                            
                        icon_w = int(pixmap.width() / base_scale_factor * scale_x)
                        icon_h = int(pixmap.height() / base_scale_factor * scale_y)
                        
                        scaled_icon = pixmap.scaled(icon_w, icon_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        
                        orig_x, orig_y = data["pos"]
                        pos_x = offset_x + orig_x * scale_x
                        pos_y = offset_y + orig_y * scale_y
                        
                        glow_color = None
                        if data["group"] == "shelters":
                            glow_color = QColor(0, 255, 0, 150)
                        elif data["group"] == "storages":
                            glow_color = QColor(255, 255, 0, 150)
                        elif data["group"] == "containers":
                            glow_color = QColor(255, 0, 0, 150)
                            
                        if glow_color:
                            glow_radius = max(icon_w, icon_h) / 1.5
                            gradient = QRadialGradient(QPointF(pos_x, pos_y), glow_radius)
                            gradient.setColorAt(0, glow_color)
                            gradient.setColorAt(1, Qt.GlobalColor.transparent)
                            
                            painter.setBrush(QBrush(gradient))
                            painter.setPen(Qt.PenStyle.NoPen)
                            painter.drawEllipse(QPointF(pos_x, pos_y), glow_radius, glow_radius)
                        
                        painter.drawPixmap(int(pos_x - icon_w // 2), int(pos_y - icon_h // 2), scaled_icon)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        if self.base_map_pixmap:
            self.draw_content(painter, self.rect(), self.visible_groups, self.base_map_pixmap)
        else:
            painter.setPen(QColor("white"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            
            if not self.base_map_pixmap:
                return
                
            rect = self.rect()
            scaled_map = self.base_map_pixmap.scaled(
                rect.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            offset_x = rect.x() + (rect.width() - scaled_map.width()) // 2
            offset_y = rect.y() + (rect.height() - scaled_map.height()) // 2
            
            base_width = 600.0
            base_height = 600.0
            
            scale_x = scaled_map.width() / base_width
            scale_y = scaled_map.height() / base_height
            
            clicked_element = None
            
            for key, data in POINTS_OF_INTEREST.items():
                if data["group"] in self.visible_groups:
                    orig_x, orig_y = data["pos"]
                    elem_x = offset_x + orig_x * scale_x
                    elem_y = offset_y + orig_y * scale_y
                    
                    dist = ((pos.x() - elem_x)**2 + (pos.y() - elem_y)**2)**0.5
                    if dist < 20 * scale_x:
                        clicked_element = data
                        break
            
            if clicked_element:
                self.element_clicked.emit(clicked_element)
                
        super().mousePressEvent(event)

    def get_current_map_pixmap(self, visible_groups=None, map_image_name=None, with_legend=False):
        groups_to_draw = visible_groups if visible_groups is not None else self.visible_groups
        
        target_map_pixmap = self.base_map_pixmap
        if map_image_name:
             path = os.path.join(ORANGE_LVL_DIR, map_image_name)
             if os.path.exists(path):
                 target_map_pixmap = QPixmap(path)
        
        if not target_map_pixmap:
            return None
            
        map_width = 600
        map_height = 600
        legend_width = 350 if with_legend else 0
        total_width = map_width + legend_width
        
        result_pixmap = QPixmap(total_width, map_height)
        result_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        map_rect = QRect(0, 0, map_width, map_height)
        
        if target_map_pixmap:
            scaled_map = target_map_pixmap.scaled(
                map_rect.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            offset_x = map_rect.x() + (map_rect.width() - scaled_map.width()) // 2
            offset_y = map_rect.y() + (map_rect.height() - scaled_map.height()) // 2
            painter.drawPixmap(offset_x, offset_y, scaled_map)
            
            base_width = 600.0
            base_height = 600.0
            
            scale_x = scaled_map.width() / base_width
            scale_y = scaled_map.height() / base_height
            
            for key, data in POINTS_OF_INTEREST.items():
                if data["group"] in groups_to_draw:
                    if key in self.element_pixmaps:
                        pixmap = self.element_pixmaps[key]
                        
                        base_scale_factor = 3.0
                        if key == "hotel":
                            base_scale_factor /= 1.5
                            
                        icon_w = int(pixmap.width() / base_scale_factor * scale_x)
                        icon_h = int(pixmap.height() / base_scale_factor * scale_y)
                        
                        scaled_icon = pixmap.scaled(icon_w, icon_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                        
                        orig_x, orig_y = data["pos"]
                        pos_x = offset_x + orig_x * scale_x
                        pos_y = offset_y + orig_y * scale_y
                        
                        glow_color = None
                        if data["group"] == "shelters":
                            glow_color = QColor(0, 255, 0, 150)
                        elif data["group"] == "storages":
                            glow_color = QColor(255, 255, 0, 150)
                        elif data["group"] == "containers":
                            glow_color = QColor(255, 0, 0, 150)
                            
                        if glow_color:
                            glow_radius = max(icon_w, icon_h) / 1.5
                            gradient = QRadialGradient(QPointF(pos_x, pos_y), glow_radius)
                            gradient.setColorAt(0, glow_color)
                            gradient.setColorAt(1, Qt.GlobalColor.transparent)
                            
                            painter.setBrush(QBrush(gradient))
                            painter.setPen(Qt.PenStyle.NoPen)
                            painter.drawEllipse(QPointF(pos_x, pos_y), glow_radius, glow_radius)
                        
                        painter.drawPixmap(int(pos_x - icon_w // 2), int(pos_y - icon_h // 2), scaled_icon)
        
        if with_legend:
            legend_rect = QRect(map_width, 0, legend_width, map_height)
            self.draw_legend(painter, legend_rect, groups_to_draw)
        
        painter.end()
        return result_pixmap

    def draw_legend(self, painter, rect, visible_groups):
        painter.save()
        
        header_font = QFont(FONT_FAMILY_BOLD, 28)
        painter.setFont(header_font)
        painter.setPen(QColor("white"))
        
        header_rect = QRect(rect.x(), rect.y() + 20, rect.width(), 50)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignCenter, "ЛЕГЕНДА КАРТЫ")
        
        item_font = QFont(FONT_FAMILY_BOLD, 18)
        painter.setFont(item_font)
        
        start_y = 90
        item_height = 70
        icon_size = 50
        
        order = ["white_room", "hotel", "places", "metro", "shelters", "storages", "containers"]
        
        current_y = start_y
        
        for key in order:
            if key in visible_groups and key in PLAYER_LEGEND_MAPPING:
                icon_file, text = PLAYER_LEGEND_MAPPING[key]
                
                path = os.path.join(ORANGE_LVL_DIR, icon_file)
                if os.path.exists(path):
                    icon_pixmap = QPixmap(path)
                    scaled_icon = icon_pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    
                    icon_x = rect.x() + 30
                    icon_y = current_y + (item_height - icon_size) // 2
                    painter.drawPixmap(icon_x, icon_y, scaled_icon)
                
                text_x = rect.x() + 30 + icon_size + 20
                text_rect = QRect(text_x, current_y, rect.width() - (text_x - rect.x()) - 10, item_height)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextWordWrap, text)
                
                current_y += item_height
        
        painter.restore()

class ClickableLabel(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.text = text
        self.pixmap = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(50, 50)

    def setPixmap(self, pixmap):
        self.pixmap = pixmap
        self.update()

    def clear(self):
        self.pixmap = None
        self.update()

    def setText(self, text):
        self.text = text
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        if self.pixmap:
            scaled = self.pixmap.scaled(
                self.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(QColor("#888"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class OrangeDetailedView(QWidget):
    back_signal = pyqtSignal()
    show_image_requested = pyqtSignal(str)
    play_signal_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("OrangeDetailedView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#OrangeDetailedView { background-color: #401d06; }")
        self.is_horizontal = True
        self.init_ui()
        self.current_pixmaps = [None, None, None]
        self.current_image_paths = [None, None, None]
        self.current_name = "" # Store current name to use as key for saving

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        header_layout = QHBoxLayout()
        
        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(80, 80)
        self.icon_frame.setStyleSheet("background-color: #ed7d31; border-radius: 10px;")
        icon_layout = QVBoxLayout(self.icon_frame)
        icon_layout.setContentsMargins(5, 5, 5, 5)
        self.header_icon = QLabel()
        self.header_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.header_icon)
        
        header_layout.addWidget(self.icon_frame)
        
        self.lbl_title = QLabel("TITLE")
        self.lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 24))
        self.lbl_title.setStyleSheet("color: white;")
        self.lbl_title.setWordWrap(True)
        self.lbl_title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        header_layout.addWidget(self.lbl_title, stretch=1)
        
        self.btn_back = QPushButton("Назад")
        self.btn_back.setFixedSize(100, 40)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #4472c4;
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5582d4;
            }
        """)
        self.btn_back.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(self.btn_back)
        
        layout.addLayout(header_layout)
        
        self.content_container = QWidget()
        self.content_layout = QGridLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.large_placeholder = ClickableLabel("400x400")
        self.large_placeholder.setMinimumSize(100, 100)
        
        self.small_container = QWidget()
        self.small_layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, self.small_container)
        self.small_layout.setContentsMargins(0, 0, 0, 0)
        self.small_layout.setSpacing(10)
        
        self.small_placeholder1 = ClickableLabel("200x200")
        self.small_placeholder1.setMinimumSize(50, 50)
        self.small_placeholder1.clicked.connect(lambda: self.swap_images(1))
        self.small_layout.addWidget(self.small_placeholder1)
        
        self.small_placeholder2 = ClickableLabel("200x200")
        self.small_placeholder2.setMinimumSize(50, 50)
        self.small_placeholder2.clicked.connect(lambda: self.swap_images(2))
        self.small_layout.addWidget(self.small_placeholder2)
        
        self.content_layout.addWidget(self.large_placeholder, 0, 0)
        self.content_layout.addWidget(self.small_container, 0, 1)
        self.content_layout.setColumnStretch(0, 2)
        self.content_layout.setColumnStretch(1, 1)
        
        layout.addWidget(self.content_container)
        
        controls_layout = QHBoxLayout()
        
        self.chk_show_to_players = QCheckBox("Показать изображение игрокам")
        self.chk_show_to_players.setStyleSheet("""
            QCheckBox { color: white; font-weight: bold; background-color: rgba(0,0,0,0.3); padding: 5px; border-radius: 5px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """)
        self.chk_show_to_players.toggled.connect(self.on_show_to_players_toggled)
        controls_layout.addWidget(self.chk_show_to_players)
        
        self.btn_play_signal = QPushButton("Воспроизвести сигнал")
        self.btn_play_signal.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold; padding: 5px;")
        self.btn_play_signal.clicked.connect(self.play_signal_requested.emit)
        self.btn_play_signal.hide()
        controls_layout.addWidget(self.btn_play_signal)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #a9b7c6;
                border: 1px solid #3c3f41;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 14px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.text_edit)

    def resizeEvent(self, event):
        width = event.size().width()
        breakpoint = 600

        should_be_horizontal = width >= breakpoint

        if self.is_horizontal != should_be_horizontal:
            self.is_horizontal = should_be_horizontal
            
            while self.content_layout.count():
                self.content_layout.takeAt(0)
            
            if self.is_horizontal:
                self.small_layout.setDirection(QBoxLayout.Direction.TopToBottom)
                
                self.content_layout.addWidget(self.large_placeholder, 0, 0, 1, 1)
                self.content_layout.addWidget(self.small_container, 0, 1, 1, 1)
                
                self.content_layout.setColumnStretch(0, 2)
                self.content_layout.setColumnStretch(1, 1)
                self.content_layout.setRowStretch(0, 1)
                self.content_layout.setRowStretch(1, 0)
            else:
                self.small_layout.setDirection(QBoxLayout.Direction.LeftToRight)
                
                self.content_layout.addWidget(self.large_placeholder, 0, 0, 1, 1)
                self.content_layout.addWidget(self.small_container, 1, 0, 1, 1)
                
                self.content_layout.setColumnStretch(0, 1)
                self.content_layout.setColumnStretch(1, 0)
                self.content_layout.setRowStretch(0, 1)
                self.content_layout.setRowStretch(1, 0)
        
        super().resizeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.force_update_icon)

    def force_update_icon(self):
        self.header_icon.update()
        self.icon_frame.update()

    def set_data(self, name, icon_filename):
        self.current_name = name # Store for saving
        
        display_name = name
        folder_name = ""
        
        if "Контейнер" in name:
            display_name = "КОНТЕЙНЕР"
            folder_name = "Контейнер"
        elif "Убежище" in name:
            display_name = "УБЕЖИЩЕ"
            folder_name = "Убежище"
        elif "Хранилище" in name:
            display_name = "ХРАНИЛИЩЕ"
            folder_name = "Хранилище"
        elif "Исцеление материи" in name or "Кровь" in name:
            display_name = "МЕСТО СИЛЫ – КРОВЬ"
            icon_filename = "КровьЛ.png"
            folder_name = "Кровь"
        elif "Уничтожение материи" in name or "Пепел" in name:
            display_name = "МЕСТО СИЛЫ – ПЕПЕЛ"
            icon_filename = "ПепелЛ.png"
            folder_name = "Пепел"
        elif "Управление сознанием" in name or "Небо" in name:
            display_name = "МЕСТО СИЛЫ – НЕБО"
            icon_filename = "НебоЛ.png"
            folder_name = "Небо"
        elif "Обретение знаний" in name or "Солнце" in name:
            display_name = "МЕСТО СИЛЫ – СОЛНЦЕ"
            icon_filename = "СолнцеЛ.png"
            folder_name = "Солнце"
        elif "Травмирование сознания" in name or "Луна" in name:
            display_name = "МЕСТО СИЛЫ – ЛУНА"
            icon_filename = "ЛунаЛ.png"
            folder_name = "Луна"
        elif "Изменение материи" in name or "Твердь" in name:
            display_name = "МЕСТО СИЛЫ – ТВЕРДЬ"
            icon_filename = "ТвердьЛ.png"
            folder_name = "Твердь"
        elif "Управление временем" in name or "Пустота" in name:
            display_name = "МЕСТО СИЛЫ – ПУСТОТА"
            icon_filename = "ПустотаЛ.png"
            folder_name = "Пустота"
        elif "Отель" in name:
            display_name = "ОТЕЛЬ"
            folder_name = "Отель"
        elif "Метро" in name:
            display_name = "МЕТРО"
            folder_name = "Метро"
        elif "Белая Зала" in name:
            display_name = "БЕЛАЯ ЗАЛА"
            folder_name = "Белая Зала"
        else:
            display_name = name.upper()
            folder_name = name
            
        self.lbl_title.setText(display_name)
            
        self.header_icon.clear()
        self.header_icon.setText("")
        
        if display_name == "БЕЛАЯ ЗАЛА":
            self.header_icon.setFont(QFont(FONT_FAMILY_BOLD, 24))
            self.header_icon.setStyleSheet("color: white;")
            self.header_icon.setText("1001")
            self.btn_play_signal.show()
        else:
            self.btn_play_signal.hide()
            path = os.path.join(ORANGE_LVL_DIR, icon_filename)
            if os.path.exists(path):
                pixmap = QPixmap(path)
                self.header_icon.setPixmap(pixmap.scaled(
                    QSize(70, 70), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
        
        self.icon_frame.update()
        self.header_icon.update()
        
        QTimer.singleShot(10, self.force_update_icon)
            
        self.load_content(folder_name)

    def load_content(self, folder_name):
        folder_path = os.path.join(ORANGE_LVL_DIR, folder_name)
        
        self.current_pixmaps = [None, None, None]
        self.current_image_paths = [None, None, None]
        
        for i in range(3):
            img_path = os.path.join(folder_path, f"{i+1}.png")
            if os.path.exists(img_path):
                self.current_pixmaps[i] = QPixmap(img_path)
                self.current_image_paths[i] = img_path
        
        self.update_placeholders()
        
        text_path = os.path.join(folder_path, "Text.txt")
        if os.path.exists(text_path):
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read())
            except Exception as e:
                self.text_edit.setText(f"Ошибка чтения файла: {e}")
        else:
            self.text_edit.clear()

    def update_placeholders(self):
        if self.current_pixmaps[0]:
            self.large_placeholder.setPixmap(self.current_pixmaps[0])
        else:
            self.large_placeholder.clear()
            self.large_placeholder.setText("Нет изображения")
            
        if self.current_pixmaps[1]:
            self.small_placeholder1.setPixmap(self.current_pixmaps[1])
            self.small_placeholder1.show()
        else:
            self.small_placeholder1.hide()
            
        if self.current_pixmaps[2]:
            self.small_placeholder2.setPixmap(self.current_pixmaps[2])
            self.small_placeholder2.show()
        else:
            self.small_placeholder2.hide()
            
        self.large_placeholder.update()
        self.small_placeholder1.update()
        self.small_placeholder2.update()
        
        if self.chk_show_to_players.isChecked():
            self.update_player_view()

    def swap_images(self, small_index):
        if self.current_pixmaps[small_index]:
            self.current_pixmaps[0], self.current_pixmaps[small_index] = self.current_pixmaps[small_index], self.current_pixmaps[0]
            self.current_image_paths[0], self.current_image_paths[small_index] = self.current_image_paths[small_index], self.current_image_paths[0]
            self.update_placeholders()

    def on_show_to_players_toggled(self, checked):
        if checked:
            self.update_player_view()
        else:
            self.show_image_requested.emit("None")

    def update_player_view(self):
        if self.current_image_paths[0]:
            self.show_image_requested.emit(self.current_image_paths[0])
        else:
            self.show_image_requested.emit("None")

    def on_back_clicked(self):
        self.chk_show_to_players.setChecked(False)
        self.back_signal.emit()

    def get_text_data(self):
        return self.text_edit.toPlainText()

    def set_text_data(self, text):
        self.text_edit.setPlainText(text)

class OrangeTab(QWidget):
    show_image_requested = pyqtSignal(object)
    play_signal_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_horizontal = True
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.saved_detailed_texts = {} # Store text for each detailed view
        self.init_ui()

    def init_ui(self):
        self.stacked_layout = QStackedLayout(self)
        
        self.map_page = QWidget()
        map_page_layout = QVBoxLayout(self.map_page)
        map_page_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #401d06; border: none; }")
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background-color: #401d06;")
        self.content_layout = QGridLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.left_container = QWidget()
        left_layout = QVBoxLayout(self.left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_title = QLabel("КАРТА ОРАНЖЕВОГО УРОВНЯ")
        lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 24))
        lbl_title.setStyleSheet("color: white; margin-bottom: 10px;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(lbl_title)
        
        self.map_placeholder = InteractiveMapLabel()
        self.map_placeholder.element_clicked.connect(self.on_map_element_clicked)
        left_layout.addWidget(self.map_placeholder)
        
        checkboxes_layout = QGridLayout()
        
        self.chk_white_room = QCheckBox("Показать Белую Залу")
        self.chk_hotel = QCheckBox("Показать Отель")
        self.chk_places = QCheckBox("Показать Места Силы")
        self.chk_metro = QCheckBox("Показать Метро")
        self.chk_shelters = QCheckBox("Показать Убежища")
        self.chk_storages = QCheckBox("Показать Хранилища")
        self.chk_containers = QCheckBox("Показать Контейнеры")
        self.chk_labels = QCheckBox("Показать подписи")
        
        chk_style = """
            QCheckBox { color: white; font-weight: bold; background-color: rgba(0,0,0,0.3); padding: 5px; border-radius: 5px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
        """
        
        self.checkbox_map = {
            self.chk_white_room: "white_room",
            self.chk_hotel: "hotel",
            self.chk_places: "places",
            self.chk_metro: "metro",
            self.chk_shelters: "shelters",
            self.chk_storages: "storages",
            self.chk_containers: "containers",
        }
        
        checkboxes = [
            self.chk_white_room, self.chk_hotel, self.chk_places, self.chk_metro,
            self.chk_shelters, self.chk_storages, self.chk_containers, self.chk_labels
        ]
        
        for i, chk in enumerate(checkboxes):
            chk.setStyleSheet(chk_style)
            chk.setChecked(True)
            chk.toggled.connect(self.update_map_visibility)
            row = i // 4
            col = i % 4
            checkboxes_layout.addWidget(chk, row, col)
            
        left_layout.addLayout(checkboxes_layout)
            
        self.content_layout.addWidget(self.left_container, 0, 0)
        
        self.right_container = QWidget()
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0,0,0,0)
        
        toggle_layout = QHBoxLayout()
        self.btn_legend = QPushButton("Легенда карты")
        self.btn_desc = QPushButton("Описание уровня")
        self.btn_show_map_to_players = QPushButton("Вывод карты игрокам")
        
        self.btn_legend.setCheckable(True)
        self.btn_desc.setCheckable(True)
        self.btn_show_map_to_players.setCheckable(True)
        self.btn_legend.setChecked(True)
        
        self.toggle_group = QButtonGroup(self)
        self.toggle_group.addButton(self.btn_legend)
        self.toggle_group.addButton(self.btn_desc)
        self.toggle_group.addButton(self.btn_show_map_to_players)
        self.toggle_group.setExclusive(True)
        
        btn_style = """
            QPushButton { 
                color: white; 
                font-weight: bold; 
                font-size: 14px; 
                background-color: rgba(0,0,0,0.3); 
                padding: 8px; 
                border-radius: 5px; 
                border: 1px solid #555;
            }
            QPushButton:checked {
                background-color: #4472c4;
                border: 1px solid #669df6;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.1);
            }
        """
        self.btn_legend.setStyleSheet(btn_style)
        self.btn_desc.setStyleSheet(btn_style)
        self.btn_show_map_to_players.setStyleSheet(btn_style)
        
        self.btn_legend.clicked.connect(lambda: self.right_stack.setCurrentIndex(0))
        self.btn_desc.clicked.connect(lambda: self.right_stack.setCurrentIndex(1))
        self.btn_show_map_to_players.clicked.connect(lambda: self.right_stack.setCurrentIndex(2))
        
        toggle_layout.addWidget(self.btn_legend)
        toggle_layout.addWidget(self.btn_desc)
        toggle_layout.addWidget(self.btn_show_map_to_players)
        toggle_layout.addStretch()
        self.right_layout.addLayout(toggle_layout)
        
        self.right_stack = QStackedLayout()
        
        self.legend_group = QGroupBox()
        self.legend_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; }")
        
        self.legend_layout = QGridLayout()
        self.legend_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.legend_group.setLayout(self.legend_layout)
        
        self.legend_items = []
        for img_file, text, indent in LEGEND_ITEMS:
            item = LegendItemWidget(img_file, text, indent)
            item.clicked.connect(lambda t=text, i=img_file: self.show_detailed_view(t, i))
            self.legend_items.append(item)
            self.legend_layout.addWidget(item)
            
        self.right_stack.addWidget(self.legend_group)
        
        self.desc_group = QGroupBox()
        self.desc_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; }")
        desc_layout = QVBoxLayout()
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #a9b7c6;
                border: none;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 14px;
                padding: 8px;
            }
        """)
        desc_layout.addWidget(self.desc_text)
        self.desc_group.setLayout(desc_layout)
        self.right_stack.addWidget(self.desc_group)
        
        self.map_output_group = QGroupBox()
        self.map_output_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; }")
        map_output_layout = QVBoxLayout()
        map_output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        main_toggle_layout = QHBoxLayout()
        
        self.chk_show_map_to_players = QCheckBox("Показать карту игрокам")
        self.chk_show_map_to_players.setStyleSheet(chk_style)
        self.chk_show_map_to_players.toggled.connect(self.on_show_map_to_players_toggled)
        main_toggle_layout.addWidget(self.chk_show_map_to_players)
        
        self.chk_show_legend_to_players = QCheckBox("Показать легенду игрокам")
        self.chk_show_legend_to_players.setStyleSheet(chk_style)
        self.chk_show_legend_to_players.setEnabled(False)
        self.chk_show_legend_to_players.toggled.connect(self.update_player_map_view)
        main_toggle_layout.addWidget(self.chk_show_legend_to_players)
        
        main_toggle_layout.addStretch()
        map_output_layout.addLayout(main_toggle_layout)
        
        map_output_layout.addSpacing(10)
        
        self.output_checkboxes = {}
        
        checkbox_container = QWidget()
        checkbox_flow_layout = FlowLayout(checkbox_container, margin=0, spacing=10)
        
        output_chk_defs = [
            ("Показать Белую Залу", "white_room"),
            ("Показать Отель", "hotel"),
            ("Показать Места Силы", "places"),
            ("Показать Метро", "metro"),
            ("Показать Убежища", "shelters"),
            ("Показать Хранилища", "storages"),
            ("Показать Контейнеры", "containers"),
            ("Показать подписи", "labels")
        ]
        
        for i, (text, key) in enumerate(output_chk_defs):
            chk = QCheckBox(text)
            chk.setStyleSheet(chk_style)
            chk.setEnabled(False)
            chk.toggled.connect(self.update_player_map_view)
            self.output_checkboxes[key] = chk
            
            checkbox_flow_layout.addWidget(chk)
            
        map_output_layout.addWidget(checkbox_container)
        map_output_layout.addStretch()
        
        self.map_output_group.setLayout(map_output_layout)
        self.right_stack.addWidget(self.map_output_group)
        
        self.right_layout.addLayout(self.right_stack)
        
        desc_path = os.path.join(ORANGE_LVL_DIR, "Description.txt")
        if os.path.exists(desc_path):
            try:
                with open(desc_path, 'r', encoding='utf-8') as f:
                    self.desc_text.setText(f.read())
            except:
                self.desc_text.setText("Ошибка чтения Description.txt")
        else:
            self.desc_text.setText("Файл Description.txt не найден.")

        self.content_layout.addWidget(self.right_container, 0, 1)
        
        scroll_area.setWidget(self.content_widget)
        map_page_layout.addWidget(scroll_area)
        
        self.stacked_layout.addWidget(self.map_page)
        
        self.detailed_view = OrangeDetailedView()
        self.detailed_view.back_signal.connect(self.show_map)
        self.detailed_view.show_image_requested.connect(self.on_detailed_view_image_requested)
        self.detailed_view.play_signal_requested.connect(self.play_signal_requested.emit)
        
        self.stacked_layout.addWidget(self.detailed_view)
        
        self.update_map_visibility()

    def toggle_right_panel(self):
        if self.btn_legend.isChecked():
            self.right_stack.setCurrentIndex(0)
        elif self.btn_desc.isChecked():
            self.right_stack.setCurrentIndex(1)
        else:
            self.right_stack.setCurrentIndex(2)

    def update_map_visibility(self):
        for chk, group in self.checkbox_map.items():
            self.map_placeholder.set_group_visible(group, chk.isChecked())
            
        if self.chk_labels.isChecked():
            self.map_placeholder.set_map_image("Map1.png")
        else:
            self.map_placeholder.set_map_image("Map0.png")

    def resizeEvent(self, event):
        width = event.size().width()
        map_width = 650 
        
        if width > map_width + 300:
            if not self.is_horizontal:
                self.content_layout.addWidget(self.left_container, 0, 0)
                self.content_layout.addWidget(self.right_container, 0, 1)
                self.is_horizontal = True
            
            self.content_layout.setColumnStretch(0, 0)
            self.content_layout.setColumnStretch(1, 1)
            available_width = width - map_width
                
        else:
            if self.is_horizontal:
                self.content_layout.addWidget(self.left_container, 0, 0)
                self.content_layout.addWidget(self.right_container, 1, 0)
                self.is_horizontal = False
            
            self.content_layout.setColumnStretch(0, 1)
            self.content_layout.setColumnStretch(1, 0)
            available_width = width
            
        cols = max(1, int(available_width / 350))
        self.update_legend_columns(cols)
            
        if self.is_horizontal:
            self.right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        else:
            self.right_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
        super().resizeEvent(event)

    def update_legend_columns(self, cols):
        for i in reversed(range(self.legend_layout.count())): 
            self.legend_layout.takeAt(i)
            
        for i, item in enumerate(self.legend_items):
            row = i // cols
            col = i % cols
            self.legend_layout.addWidget(item, row, col)

    def on_map_element_clicked(self, data):
        name = data["name"]
        icon = data.get("legend_icon", data["file"])
        
        self.show_detailed_view(name, icon)

    def show_detailed_view(self, name, icon_filename):
        self.detailed_view.set_data(name, icon_filename)
        
        # Restore saved text if exists
        if name in self.saved_detailed_texts:
            self.detailed_view.set_text_data(self.saved_detailed_texts[name])
            
        self.stacked_layout.setCurrentIndex(1)

    def show_map(self):
        # Save text before leaving
        current_name = self.detailed_view.current_name
        if current_name:
            self.saved_detailed_texts[current_name] = self.detailed_view.get_text_data()
            
        self.stacked_layout.setCurrentIndex(0)
        self.update_player_map_view()

    def on_show_map_to_players_toggled(self, checked):
        self.chk_show_legend_to_players.setEnabled(checked)
        if not checked:
            self.chk_show_legend_to_players.setChecked(False)
            
        for chk in self.output_checkboxes.values():
            chk.setEnabled(checked)
            if not checked:
                chk.setChecked(False)
        
        self.update_player_map_view()

    def update_player_map_view(self):
        if self.stacked_layout.currentIndex() == 1 and self.detailed_view.chk_show_to_players.isChecked():
            return

        if not self.chk_show_map_to_players.isChecked():
            self.show_image_requested.emit("None")
            return

        visible_groups = set()
        for key, chk in self.output_checkboxes.items():
            if key == "labels":
                continue
            if chk.isChecked():
                visible_groups.add(key)
        
        map_image = "Map0.png"
        if self.output_checkboxes["labels"].isChecked():
            map_image = "Map1.png"
            
        show_legend = self.chk_show_legend_to_players.isChecked()
            
        pixmap = self.map_placeholder.get_current_map_pixmap(
            visible_groups=visible_groups, 
            map_image_name=map_image,
            with_legend=show_legend
        )
        
        if pixmap:
            self.show_image_requested.emit(pixmap)
        else:
            self.show_image_requested.emit("None")

    def on_detailed_view_image_requested(self, image_data):
        if image_data == "None":
            self.update_player_map_view()
        else:
            self.show_image_requested.emit(image_data)

    def get_data(self):
        # Save current detailed view text if open
        if self.stacked_layout.currentIndex() == 1:
            current_name = self.detailed_view.current_name
            if current_name:
                self.saved_detailed_texts[current_name] = self.detailed_view.get_text_data()
                
        return {
            'detailed_texts': self.saved_detailed_texts
        }

    def set_data(self, data):
        if not data: return
        self.saved_detailed_texts = data.get('detailed_texts', {})
        
        # If detailed view is open, update it
        if self.stacked_layout.currentIndex() == 1:
            current_name = self.detailed_view.current_name
            if current_name and current_name in self.saved_detailed_texts:
                self.detailed_view.set_text_data(self.saved_detailed_texts[current_name])
