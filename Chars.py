from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, 
                             QLabel, QLineEdit, QComboBox, QFormLayout, QSizePolicy, QPushButton, QTextEdit, QGroupBox, QScrollArea, QLayout, QStyle, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QPoint, QRect, QSize
from PyQt6.QtGui import QFont, QIntValidator, QPixmap, QPainter, QColor, QIcon
from config import FONT_FAMILY_REGULAR, FONT_FAMILY_BOLD, CHAR_LIST_DIR
from widgets import WrappingButton
import os

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
        
        if self.itemList:
            itemWidth = self.itemList[0].sizeHint().width()
            if rect.width() < itemWidth * 2 + spaceX:
                for item in self.itemList:
                    wid = item.widget()
                    size = item.sizeHint()
                    centerX = rect.x() + (rect.width() - size.width()) // 2
                    if not testOnly:
                        item.setGeometry(QRect(QPoint(centerX, y), size))
                    y = y + size.height() + spaceY
                return y - rect.y()

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

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class ResourceWidget(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.placeholder = QLabel()
        self.placeholder.setFixedSize(60, 60)
        self.placeholder.setStyleSheet("background-color: #333333; border: 1px solid #555;")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_path = os.path.join(CHAR_LIST_DIR, f"{self.label_text}.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.placeholder.setPixmap(pixmap.scaled(
                self.placeholder.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        
        left_col = QVBoxLayout()
        left_col.setSpacing(2)
        left_col.addWidget(self.placeholder, alignment=Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(self.label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont(FONT_FAMILY_BOLD, 10))
        lbl.setStyleSheet("color: #cccccc; border: none;")
        left_col.addWidget(lbl)
        layout.addLayout(left_col)
        
        right_col = QVBoxLayout()
        right_col.setSpacing(5)
        
        max_row = QHBoxLayout()
        max_row.setContentsMargins(0,0,0,0)
        max_row.setSpacing(5)
        
        lbl_max = QLabel("Макс:")
        lbl_max.setStyleSheet("color: #888; border: none;")
        self.input_max = QLineEdit("10")
        self.input_max.setValidator(QIntValidator(0, 999))
        self.input_max.setFixedWidth(40)
        self.input_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_max.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #555;")
        
        max_row.addStretch()
        max_row.addWidget(lbl_max)
        max_row.addWidget(self.input_max)
        max_row.addStretch()
        
        right_col.addLayout(max_row)
        
        current_row = QHBoxLayout()
        current_row.setContentsMargins(0,0,0,0)
        current_row.setSpacing(0)
        
        self.btn_minus = QPushButton("-")
        self.btn_minus.setFixedSize(20, 20)
        self.btn_minus.clicked.connect(self.dec_val)
        
        self.input_current = QLineEdit("10")
        self.input_current.setValidator(QIntValidator(0, 999))
        self.input_current.setFixedWidth(40)
        self.input_current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_current.setStyleSheet("background-color: #2b2b2b; color: white; border-top: 1px solid #555; border-bottom: 1px solid #555; border-left: none; border-right: none;")
        
        self.btn_plus = QPushButton("+")
        self.btn_plus.setFixedSize(20, 20)
        self.btn_plus.clicked.connect(self.inc_val)
        
        current_row.addStretch()
        current_row.addWidget(self.btn_minus)
        current_row.addWidget(self.input_current)
        current_row.addWidget(self.btn_plus)
        current_row.addStretch()
        
        right_col.addLayout(current_row)
        
        layout.addLayout(right_col)
        
    def dec_val(self):
        try:
            val = int(self.input_current.text())
            self.input_current.setText(str(val - 1))
        except ValueError:
            pass

    def inc_val(self):
        try:
            val = int(self.input_current.text())
            self.input_current.setText(str(val + 1))
        except ValueError:
            pass

class StatWidget(QWidget):
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        self.label_text = label_text
        self.bg_pixmap = None
        
        image_path = os.path.join(CHAR_LIST_DIR, f"{label_text}.png")
        if os.path.exists(image_path):
            self.bg_pixmap = QPixmap(image_path)
            
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        self.input = QLineEdit()
        self.input.setFixedSize(50, 50)
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input.setFont(QFont(FONT_FAMILY_BOLD, 16))
        self.input.setStyleSheet("background-color: transparent; color: white; border: 1px solid #555;")
        
        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont(FONT_FAMILY_REGULAR, 9))
        lbl.setStyleSheet("color: #cccccc; border: none;")
        
        layout.addWidget(self.input, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.bg_pixmap:
            x = (self.width() - 50) // 2
            y = 0
            target_rect = QRect(x, y, 50, 50)
            painter.setOpacity(0.3)
            painter.drawPixmap(target_rect, self.bg_pixmap)
            painter.setOpacity(1.0)
        else:
            x = (self.width() - 50) // 2
            y = 0
            painter.fillRect(x, y, 50, 50, QColor("#2b2b2b"))
            
        super().paintEvent(event)

class CharacterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.Box)
        self.setLineWidth(2)
        self.setStyleSheet("CharacterWidget { border: 2px solid #555; border-radius: 5px; background-color: #222; }")
        
        self.base_width = 420
        self.base_height_expanded = 650
        self.base_height_collapsed = 450
        self.base_height_brief = 300
        self.scale_factor = 1.0
        self.abilities_visible = True
        self.view_mode = "Full"
        
        self.stats = {} # Store stat widgets
        
        self.setMinimumHeight(self.base_height_expanded) 
        self.update_size()
        self.init_ui()

    def update_size(self):
        self.setFixedWidth(int(self.base_width * self.scale_factor))
        if self.view_mode == "Brief":
            base_h = self.base_height_brief
        else:
            base_h = self.base_height_expanded if self.abilities_visible else self.base_height_collapsed
        self.setMinimumHeight(base_h)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(15)
        
        left_col = QVBoxLayout()
        self.image_placeholder = QLabel()
        self.image_placeholder.setFixedSize(100, 100)
        self.image_placeholder.setStyleSheet("background-color: #333333; border: 1px solid #555;")
        self.image_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.combo_patronage = NoScrollComboBox()
        self.combo_patronage.addItems(["Кровь", "Луна", "Твердь", "Пепел", "Небо", "Солнце", "Пустота"])
        self.combo_patronage.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #555;")
        self.combo_patronage.currentTextChanged.connect(self.update_image)
        
        left_col.addWidget(self.image_placeholder)
        left_col.addWidget(self.combo_patronage)
        left_col.addStretch()
        top_layout.addLayout(left_col)
        
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.form_layout.setSpacing(8)
        
        def create_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_FAMILY_BOLD, 10))
            lbl.setStyleSheet("color: #cccccc; border: none;")
            return lbl
            
        def create_input():
            inp = QLineEdit()
            inp.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #555; padding: 4px;")
            inp.setMinimumHeight(25)
            return inp

        self.inp_char_name = create_input()
        self.inp_player_name = create_input()
        self.inp_city = create_input()
        self.inp_prof = create_input()

        self.form_layout.addRow(create_label("Имя персонажа:"), self.inp_char_name)
        self.form_layout.addRow(create_label("Имя игрока:"), self.inp_player_name)
        
        self.gender_age_widget = QWidget()
        gender_age_layout = QHBoxLayout(self.gender_age_widget)
        gender_age_layout.setContentsMargins(0,0,0,0)
        self.inp_gender = create_input()
        self.inp_age = create_input()
        self.inp_age.setValidator(QIntValidator(0, 999))
        self.lbl_gender = create_label("Пол:")
        self.lbl_age = create_label("Возраст:")
        gender_age_layout.addWidget(self.lbl_gender)
        gender_age_layout.addWidget(self.inp_gender)
        gender_age_layout.addSpacing(10)
        gender_age_layout.addWidget(self.lbl_age)
        gender_age_layout.addWidget(self.inp_age)
        gender_age_layout.addStretch()
        self.form_layout.addRow(self.gender_age_widget)

        self.lbl_city = create_label("Город:")
        self.form_layout.addRow(self.lbl_city, self.inp_city)
        self.lbl_prof = create_label("Профессия:")
        self.form_layout.addRow(self.lbl_prof, self.inp_prof)
        
        top_layout.addLayout(self.form_layout)
        main_layout.addLayout(top_layout)
        
        res_group = QGroupBox("Базовые ресурсы")
        res_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        res_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")
        res_layout = QHBoxLayout()
        self.res_hp = ResourceWidget("Здоровье")
        self.res_en = ResourceWidget("Энергия")
        res_layout.addWidget(self.res_hp)
        res_layout.addSpacing(20)
        res_layout.addWidget(self.res_en)
        res_layout.addStretch()
        res_group.setLayout(res_layout)
        main_layout.addWidget(res_group)
        
        stats_group = QGroupBox("Характеристики")
        stats_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        stats_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")
        stats_layout = QHBoxLayout()
        stat_names = ["Самочувствие", "Внимание", "Движение", "Сражение", "Мышление", "Общение"]
        for name in stat_names:
            sw = StatWidget(name)
            stats_layout.addWidget(sw)
            self.stats[name] = sw
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        self.abilities_group = QGroupBox("Способности")
        self.abilities_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        self.abilities_group.setStyleSheet("QGroupBox { border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; padding: 0 3px; }")
        
        self.btn_toggle_abilities = QPushButton("▼")
        self.btn_toggle_abilities.setFixedSize(20, 20)
        self.btn_toggle_abilities.setCheckable(True)
        self.btn_toggle_abilities.setChecked(True)
        self.btn_toggle_abilities.clicked.connect(self.toggle_abilities)
        self.btn_toggle_abilities.setStyleSheet("QPushButton { border: none; color: #cccccc; font-weight: bold; }")
        
        ab_layout = QVBoxLayout()
        
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(self.btn_toggle_abilities)
        ab_layout.addLayout(header_layout)
        
        self.abilities_content = QWidget()
        abilities_content_layout = QVBoxLayout(self.abilities_content)
        abilities_content_layout.setContentsMargins(0,0,0,0)
        
        lbl_passive = QLabel("Пассивные способности:")
        lbl_passive.setStyleSheet("border: none;")
        abilities_content_layout.addWidget(lbl_passive)
        self.txt_passive = QTextEdit()
        self.txt_passive.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #555;")
        self.txt_passive.setMinimumHeight(60)
        abilities_content_layout.addWidget(self.txt_passive)
        
        lbl_active = QLabel("Активные способности:")
        lbl_active.setStyleSheet("border: none;")
        abilities_content_layout.addWidget(lbl_active)
        self.txt_active = QTextEdit()
        self.txt_active.setStyleSheet("background-color: #2b2b2b; color: white; border: 1px solid #555;")
        self.txt_active.setMinimumHeight(60)
        abilities_content_layout.addWidget(self.txt_active)
        
        ab_layout.addWidget(self.abilities_content)
        
        self.abilities_group.setLayout(ab_layout)
        main_layout.addWidget(self.abilities_group)
        
        main_layout.addStretch()
        
        self.update_image(self.combo_patronage.currentText())

    def toggle_abilities(self, checked):
        self.abilities_visible = checked
        self.abilities_content.setVisible(checked)
        self.btn_toggle_abilities.setText("▼" if checked else "▲")
        self.update_size()
        
        if self.parent():
            self.parent().layout().invalidate()

    def update_image(self, text):
        image_path = os.path.join(CHAR_LIST_DIR, f"{text}.png")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            self.image_placeholder.setPixmap(pixmap.scaled(
                self.image_placeholder.size(), 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.image_placeholder.clear()

    def set_view_mode(self, mode):
        self.view_mode = mode
        is_full = (mode == "Full")
        
        self.gender_age_widget.setVisible(is_full)
        self.lbl_city.setVisible(is_full)
        self.inp_city.setVisible(is_full)
        self.lbl_prof.setVisible(is_full)
        self.inp_prof.setVisible(is_full)
        
        if not is_full:
            self.btn_toggle_abilities.setChecked(False)
            self.toggle_abilities(False)
        else:
            self.btn_toggle_abilities.setChecked(True)
            self.toggle_abilities(True)
            
        self.update_size()

    def get_data(self):
        data = {
            'patronage': self.combo_patronage.currentText(),
            'char_name': self.inp_char_name.text(),
            'player_name': self.inp_player_name.text(),
            'gender': self.inp_gender.text(),
            'age': self.inp_age.text(),
            'city': self.inp_city.text(),
            'profession': self.inp_prof.text(),
            'hp_current': self.res_hp.input_current.text(),
            'hp_max': self.res_hp.input_max.text(),
            'en_current': self.res_en.input_current.text(),
            'en_max': self.res_en.input_max.text(),
            'stats': {name: w.input.text() for name, w in self.stats.items()},
            'passive_abilities': self.txt_passive.toPlainText(),
            'active_abilities': self.txt_active.toPlainText()
        }
        return data

    def set_data(self, data):
        if not data: return
        self.combo_patronage.setCurrentText(data.get('patronage', 'Кровь'))
        self.inp_char_name.setText(data.get('char_name', ''))
        self.inp_player_name.setText(data.get('player_name', ''))
        self.inp_gender.setText(data.get('gender', ''))
        self.inp_age.setText(data.get('age', ''))
        self.inp_city.setText(data.get('city', ''))
        self.inp_prof.setText(data.get('profession', ''))
        
        self.res_hp.input_current.setText(data.get('hp_current', '10'))
        self.res_hp.input_max.setText(data.get('hp_max', '10'))
        self.res_en.input_current.setText(data.get('en_current', '10'))
        self.res_en.input_max.setText(data.get('en_max', '10'))
        
        stats_data = data.get('stats', {})
        for name, val in stats_data.items():
            if name in self.stats:
                self.stats[name].input.setText(val)
                
        self.txt_passive.setPlainText(data.get('passive_abilities', ''))
        self.txt_active.setPlainText(data.get('active_abilities', ''))

class PlayersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_factor = 1.0
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        self.flow_layout = FlowLayout(content_widget, 10, 10)
        
        self.char_widgets = [CharacterWidget() for _ in range(4)]
        for widget in self.char_widgets:
            self.flow_layout.addWidget(widget)
            
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        bottom_layout.addWidget(QLabel("Вид листа:"))
        self.view_group = QButtonGroup(self)
        self.rb_full = QRadioButton("Полный")
        self.rb_brief = QRadioButton("Краткий")
        self.rb_full.setChecked(True)
        
        self.view_group.addButton(self.rb_full)
        self.view_group.addButton(self.rb_brief)
        
        self.rb_full.toggled.connect(lambda: self.change_view_mode("Full"))
        self.rb_brief.toggled.connect(lambda: self.change_view_mode("Brief"))
        
        bottom_layout.addWidget(self.rb_full)
        bottom_layout.addWidget(self.rb_brief)
        
        bottom_layout.addStretch()
        
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        self.lbl_zoom = QLineEdit("100%")
        self.lbl_zoom.setFixedSize(60, 30)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.editingFinished.connect(self.apply_zoom_from_input)
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(30, 30)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        
        bottom_layout.addWidget(self.btn_zoom_out)
        bottom_layout.addWidget(self.lbl_zoom)
        bottom_layout.addWidget(self.btn_zoom_in)
        
        main_layout.addLayout(bottom_layout)

    def zoom_in(self):
        self.scale_factor += 0.05
        self.update_zoom()

    def zoom_out(self):
        if self.scale_factor > 0.2:
            self.scale_factor -= 0.05
            self.update_zoom()

    def apply_zoom_from_input(self):
        text = self.lbl_zoom.text().strip().replace('%', '')
        try:
            value = int(text)
            self.scale_factor = max(0.2, value / 100.0)
            self.update_zoom()
        except ValueError:
            self.update_zoom()

    def update_zoom(self):
        self.lbl_zoom.setText(f"{self.scale_factor:.0%}")
        for widget in self.char_widgets:
            widget.scale_factor = self.scale_factor
            widget.update_size()
        self.flow_layout.invalidate()

    def change_view_mode(self, mode):
        for widget in self.char_widgets:
            widget.set_view_mode(mode)
        self.flow_layout.invalidate()

    def get_data(self):
        return [w.get_data() for w in self.char_widgets]

    def set_data(self, data_list):
        if not data_list or not isinstance(data_list, list):
            return
        for i, data in enumerate(data_list):
            if i < len(self.char_widgets):
                self.char_widgets[i].set_data(data)
