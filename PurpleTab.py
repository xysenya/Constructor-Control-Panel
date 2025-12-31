import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy, QStackedLayout, QPushButton, QCheckBox, QTextEdit, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPixmap, QColor
from config import FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, PURPLE_LVL_DIR
from layouts import FlowLayout

PURPLE_COLOR = "#785dc8"
BG_COLOR = "#2f243c"

TITLE_MAPPING = {
    "Пещеры": "ПЕЩЕРЫ ФИОЛЕТОВОГО УРОВНЯ",
    "Надписи": "НАДПИСИ НА СТЕНАХ",
    "Расщелина": "РАСЩЕЛИНА С КОСТРОМ",
    "Комната стража": "КОМНАТА СТРАЖА",
    "Страж": "СТРАЖ ФИОЛЕТОВОГО УРОВНЯ",
    "Белая зала": "БЕЛАЯ ЗАЛА"
}

class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

class FlowContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = FlowLayout(self, margin=0, spacing=10)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

    def addWidget(self, widget):
        self.layout.addWidget(widget)

class PurpleDetailedView(QWidget):
    back_requested = pyqtSignal()
    show_image_requested = pyqtSignal(str)
    play_signal_requested = pyqtSignal()
    switch_view_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_key = ""
        self.current_pixmaps = [None, None, None]
        self.current_paths = [None, None, None]
        
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(BG_COLOR))
        self.setPalette(p)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        
        self.icon_frame = QFrame()
        self.icon_frame.setFixedSize(80, 80)
        self.icon_frame.setStyleSheet(f"background-color: {PURPLE_COLOR}; border-radius: 10px;")
        icon_layout = QVBoxLayout(self.icon_frame)
        icon_layout.setContentsMargins(0,0,0,0)
        
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(self.icon_label)
        
        header_layout.addWidget(self.icon_frame)
        
        self.lbl_title = QLabel("TITLE")
        self.lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 24))
        self.lbl_title.setStyleSheet("color: white;")
        self.lbl_title.setWordWrap(True)
        header_layout.addWidget(self.lbl_title, stretch=1)
        
        btn_back = QPushButton("Назад")
        btn_back.setFixedSize(100, 40)
        btn_back.setStyleSheet("""
            QPushButton { background-color: #4472c4; color: white; border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #5582d4; }
        """)
        btn_back.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(btn_back)
        
        layout.addLayout(header_layout)

        self.images_container = QWidget()
        images_layout = QVBoxLayout(self.images_container)
        images_layout.setContentsMargins(0,0,0,0)
        images_layout.setSpacing(10)
        
        self.main_image = ClickableLabel()
        self.main_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_image.setMinimumSize(200, 200) 
        self.main_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        images_layout.addWidget(self.main_image)
        
        self.small_images_container = QWidget()
        self.small_images_layout = QHBoxLayout(self.small_images_container)
        self.small_images_layout.setContentsMargins(0,0,0,0)
        self.small_images_layout.setSpacing(10)
        
        self.small_image1 = ClickableLabel()
        self.small_image1.setFixedSize(100, 100)
        self.small_image1.setStyleSheet("border: none;") 
        self.small_image1.clicked.connect(lambda: self.swap_images(1))
        
        self.small_image2 = ClickableLabel()
        self.small_image2.setFixedSize(100, 100)
        self.small_image2.setStyleSheet("border: none;")
        self.small_image2.clicked.connect(lambda: self.swap_images(2))
        
        self.nav_image = ClickableLabel()
        self.nav_image.setFixedSize(100, 100)
        self.nav_image.setStyleSheet("border: none;")
        self.nav_image.clicked.connect(lambda: self.switch_view_requested.emit("Белая зала"))
        
        self.small_images_layout.addStretch()
        self.small_images_layout.addWidget(self.small_image1)
        self.small_images_layout.addWidget(self.small_image2)
        self.small_images_layout.addWidget(self.nav_image)
        self.small_images_layout.addStretch()
        
        images_layout.addWidget(self.small_images_container)
        
        layout.addWidget(self.images_container)

        controls_layout = QHBoxLayout()
        
        self.chk_show = QCheckBox("Показать изображение игрокам")
        self.chk_show.setStyleSheet("color: white; font-weight: bold;")
        self.chk_show.toggled.connect(self.on_show_toggled)
        controls_layout.addWidget(self.chk_show)
        
        self.btn_signal = QPushButton("Воспроизвести сигнал")
        self.btn_signal.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold; padding: 5px;")
        self.btn_signal.clicked.connect(self.play_signal_requested.emit)
        self.btn_signal.hide()
        controls_layout.addWidget(self.btn_signal)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False) # Changed to False to allow editing
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

    def set_data(self, key):
        self.current_key = key
        
        title_text = TITLE_MAPPING.get(key, key.upper())
        self.lbl_title.setText(title_text)
        
        self.icon_label.clear()
        self.icon_label.setText("")
        
        if key == "Белая зала":
            self.icon_label.setText("1001")
            self.icon_label.setFont(QFont(FONT_FAMILY_BOLD, 24))
            self.icon_label.setStyleSheet("color: white; border: none;")
            self.btn_signal.show()
        else:
            self.btn_signal.hide()
            icon_path = os.path.join(PURPLE_LVL_DIR, f"{key}D.png")
            if os.path.exists(icon_path):
                pixmap = QPixmap(icon_path)
                self.icon_label.setPixmap(pixmap.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.icon_label.setText("IMG")
                self.icon_label.setStyleSheet("color: white;")

        self.current_pixmaps = [None, None, None]
        self.current_paths = [None, None, None]
        self.small_images_container.hide()
        self.small_image1.hide()
        self.small_image2.hide()
        self.nav_image.hide()
        
        main_img_name = f"{key}.png"
        
        if key == "Комната стража":
            self.small_images_container.show()
            self.small_image1.show()
            self.nav_image.show()
            self.load_image(1, "Мониторы.png")
            
            nav_path = os.path.join(PURPLE_LVL_DIR, "Белая зала.png")
            if os.path.exists(nav_path):
                pixmap = QPixmap(nav_path)
                self.nav_image.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
        elif key == "Белая зала":
            self.small_images_container.show()
            self.small_image1.show()
            self.small_image2.show()
            main_img_name = "Белая зала 1.png"
            self.load_image(1, "Белая зала 2.png")
            self.load_image(2, "Белая зала 3.png")
            
        self.load_image(0, main_img_name)
        self.update_images_display()

        text_path = os.path.join(PURPLE_LVL_DIR, f"{key}.txt")
        if os.path.exists(text_path):
            try:
                with open(text_path, 'r', encoding='utf-8') as f:
                    self.text_edit.setText(f.read())
            except Exception as e:
                self.text_edit.setText(f"Ошибка чтения: {e}")
        else:
            self.text_edit.clear()
            
        self.chk_show.setChecked(False)

    def load_image(self, index, filename):
        path = os.path.join(PURPLE_LVL_DIR, filename)
        if os.path.exists(path):
            self.current_pixmaps[index] = QPixmap(path)
            self.current_paths[index] = path

    def update_images_display(self):
        if self.current_pixmaps[0]:
            self.update_main_image_scaling()
        else:
            self.main_image.clear()
            self.main_image.setText("Нет изображения")
            
        if self.current_pixmaps[1]:
            self.small_image1.setPixmap(self.current_pixmaps[1].scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
        if self.current_pixmaps[2]:
            self.small_image2.setPixmap(self.current_pixmaps[2].scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def update_main_image_scaling(self):
        if self.current_pixmaps[0]:
            available_width = self.contentsRect().width()
            target_size = min(400, available_width)
            target_size = max(200, target_size)
            
            scaled = self.current_pixmaps[0].scaled(target_size, target_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.main_image.setPixmap(scaled)

    def resizeEvent(self, event):
        self.update_main_image_scaling()
        super().resizeEvent(event)

    def swap_images(self, small_index):
        if self.current_pixmaps[small_index]:
            self.current_pixmaps[0], self.current_pixmaps[small_index] = self.current_pixmaps[small_index], self.current_pixmaps[0]
            self.current_paths[0], self.current_paths[small_index] = self.current_paths[small_index], self.current_paths[0]
            self.update_images_display()
            
            if self.chk_show.isChecked():
                self.show_image_requested.emit(self.current_paths[0])

    def on_show_toggled(self, checked):
        if checked and self.current_paths[0]:
            self.show_image_requested.emit(self.current_paths[0])
        else:
            self.show_image_requested.emit("None")

    def on_back_clicked(self):
        self.chk_show.setChecked(False)
        self.back_requested.emit()

    def get_text_data(self):
        return self.text_edit.toPlainText()

    def set_text_data(self, text):
        self.text_edit.setPlainText(text)

class PlaceholderWidget(QWidget):
    clicked = pyqtSignal(str)
    
    def __init__(self, w, h, text, parent=None):
        super().__init__(parent)
        self.text = text
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(w, h)
        self.image_label.setStyleSheet("background-color: rgba(255, 255, 255, 0.1); border: 2px dashed rgba(255, 255, 255, 0.3); border-radius: 10px;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_path = os.path.join(PURPLE_LVL_DIR, f"{text}.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_label.setPixmap(pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.image_label.setStyleSheet("background-color: transparent; border: none;")
        else:
            self.image_label.setText(f"{w}x{h}")
            self.image_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); border: 2px dashed rgba(255, 255, 255, 0.3); border-radius: 10px;")
            
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        lbl_text = QLabel(text)
        lbl_text.setFont(QFont(FONT_FAMILY_BOLD, 14))
        lbl_text.setStyleSheet("color: white;")
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_text.setWordWrap(True)
        lbl_text.setFixedWidth(w)
        
        layout.addWidget(lbl_text, alignment=Qt.AlignmentFlag.AlignCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.text)
        super().mousePressEvent(event)

class PurpleTab(QWidget):
    show_image_requested = pyqtSignal(str)
    play_signal_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.saved_detailed_texts = {}
        self.init_ui()

    def init_ui(self):
        self.stacked_layout = QStackedLayout(self)
        
        self.page_main = QWidget()
        main_layout = QVBoxLayout(self.page_main)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet(f"QScrollArea {{ background-color: {BG_COLOR}; border: none; }}")
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {BG_COLOR};")
        
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(30)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        lbl_title = QLabel("ФИОЛЕТОВЫЙ УРОВЕНЬ КОНСТРУКТОРА")
        lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 28))
        lbl_title.setStyleSheet("color: white;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        self.content_layout.addWidget(lbl_title)

        self.group1_container = FlowContainer()
        self.group1_container.addWidget(self.create_placeholder(200, 200, "Пещеры"))
        self.group1_container.addWidget(self.create_placeholder(200, 200, "Надписи"))
        self.group1_container.addWidget(self.create_placeholder(200, 200, "Расщелина"))
        self.content_layout.addWidget(self.group1_container)

        self.group2_container = FlowContainer()
        self.group2_container.addWidget(self.create_placeholder(200, 200, "Страж"))
        self.group2_container.addWidget(self.create_placeholder(200, 200, "Комната стража"))
        self.group2_container.addWidget(self.create_placeholder(100, 100, "Белая зала"))
        self.content_layout.addWidget(self.group2_container)

        desc_text = (
            "Огромный лабиринт из сотен поворотов, таящий в себе опасность. "
            "Фиолетовый уровень – единая точка для всех сигнатур всех итераций симуляции. "
            "Если оставить здесь сообщение, то скорее всего оно дойдет до каких-либо Рыцарей, "
            "которые в будущем сюда попадут."
        )
        lbl_desc = QLabel(desc_text)
        lbl_desc.setFont(QFont(FONT_FAMILY_REGULAR, 16))
        lbl_desc.setStyleSheet("color: #d0d0d0;")
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_wrapper = QWidget()
        desc_layout = QVBoxLayout(desc_wrapper)
        desc_layout.addWidget(lbl_desc)
        self.content_layout.addWidget(desc_wrapper)
        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.stacked_layout.addWidget(self.page_main)
        
        self.detailed_view = PurpleDetailedView()
        self.detailed_view.back_requested.connect(self.show_main_page)
        self.detailed_view.show_image_requested.connect(self.show_image_requested.emit)
        self.detailed_view.play_signal_requested.connect(self.play_signal_requested.emit)
        self.detailed_view.switch_view_requested.connect(self.open_detailed_view)
        
        self.stacked_layout.addWidget(self.detailed_view)

    def create_placeholder(self, w, h, text):
        p = PlaceholderWidget(w, h, text)
        p.clicked.connect(self.open_detailed_view)
        return p
    
    def open_detailed_view(self, key):
        self.detailed_view.set_data(key)
        
        if key in self.saved_detailed_texts:
            self.detailed_view.set_text_data(self.saved_detailed_texts[key])
            
        self.stacked_layout.setCurrentIndex(1)
        
    def show_main_page(self):
        current_key = self.detailed_view.current_key
        if current_key:
            self.saved_detailed_texts[current_key] = self.detailed_view.get_text_data()
            
        self.stacked_layout.setCurrentIndex(0)

    def get_data(self):
        if self.stacked_layout.currentIndex() == 1:
            current_key = self.detailed_view.current_key
            if current_key:
                self.saved_detailed_texts[current_key] = self.detailed_view.get_text_data()
                
        return {
            'detailed_texts': self.saved_detailed_texts
        }

    def set_data(self, data):
        if not data: return
        self.saved_detailed_texts = data.get('detailed_texts', {})
        
        if self.stacked_layout.currentIndex() == 1:
            current_key = self.detailed_view.current_key
            if current_key and current_key in self.saved_detailed_texts:
                self.detailed_view.set_text_data(self.saved_detailed_texts[current_key])
