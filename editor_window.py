from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QColorDialog, QSpinBox, QCheckBox, 
                             QDialogButtonBox, QFrame, QComboBox, QWidget, QGroupBox, QGridLayout)
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QTextDocument, QTextOption, QIcon, QPixmap
from PyQt6.QtCore import Qt, QRectF, QSize
from config import CELL_RADIUS, CELL_SIZE, FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, ROWS, COLS
from utils import get_font_name, get_fitted_font_size

# Пресеты для типов комнат
ROOM_TYPES = {
    "Обычная зала": {
        'color': '#666666', 'text_color': '#CCCCCC', 'text_color_name': '#CCCCCC',
        'font_weight_num': 'bold', 'font_weight_name': 'normal'
    },
    "Зала внутреннего контура": {
        'color': '#666666', 'text_color': '#CCCCCC', 'text_color_name': '#CCCCCC',
        'font_weight_num': 'bold', 'font_weight_name': 'normal'
    },
    "Белая зала": {
        'color': '#FFFFFF', 'text_color': '#000000', 'text_color_name': '#000000',
        'font_weight_num': 'bold', 'font_weight_name': 'normal' # Changed to normal
    },
    "Транспортная зала": {
        'color': '#ffc000', 'text_color': '#000000', 'text_color_name': '#000000',
        'font_weight_num': 'bold', 'font_weight_name': 'normal' # Changed to normal
    },
    "Сгенерированная зала": {
        'color': '#666666', 'text_color': '#CCCCCC', 'text_color_name': '#CCCCCC',
        'font_weight_num': 'bold', 'font_weight_name': 'normal'
    }
}

PRESET_COLORS = ["#70ad47", "#3e68b3", "#ff0000", "#000000", "#ffffff", "#ffc000", "#a5a5a5"]

class CellPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(CELL_SIZE + 40, CELL_SIZE + 40)
        self.data = {}

    def update_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(40, 40, 40))

        if not self.data:
            return

        margin_x = (self.width() - CELL_SIZE) / 2
        margin_y = (self.height() - CELL_SIZE) / 2
        rect = QRectF(margin_x, margin_y, CELL_SIZE, CELL_SIZE)

        bg_color = QColor(self.data.get('color', '#CCCCCC'))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, CELL_RADIUS, CELL_RADIUS)

        num_text = str(self.data.get('number', ''))
        if self.data.get('room_type') == 'Сгенерированная зала':
            num_text = f"-{num_text}-"

        text_color = QColor(self.data.get('text_color', '#000000'))
        painter.setPen(text_color)
        
        font_size_num = self.data.get('font_size_num', 24)
        is_bold_num = self.data.get('font_weight_num') == 'bold'
        font_num = QFont(get_font_name(is_bold_num), font_size_num)
        painter.setFont(font_num)

        name_text = self.data.get('name', '').strip()
        room_type = self.data.get('room_type', '')
        is_inner_contour = room_type == 'Зала внутреннего контура'
        
        if is_inner_contour:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, num_text)
            
        elif name_text:
            # Номер смещаем вверх (0.05)
            num_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.05, rect.width(), rect.height() * 0.3)
            painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, num_text)
            
            painter.save()
            
            text_color_name = QColor(self.data.get('text_color_name', '#000000'))
            
            # Auto-fit font size for name
            initial_font_size_name = self.data.get('font_size_name', 12)
            is_bold_name = self.data.get('font_weight_name') == 'bold'
            fitted_font_size = get_fitted_font_size(name_text, is_bold_name, initial_font_size_name, rect.width() * 0.95)
            
            font_name = QFont(get_font_name(is_bold_name), fitted_font_size)
            
            name_area_width = rect.width() - 10
            name_area_x = rect.x() + 5
            
            formatted_name = name_text.replace(' ', '\n')
            
            doc = QTextDocument()
            doc.setDefaultFont(font_name)
            doc.setPlainText(formatted_name)
            doc.setTextWidth(name_area_width)
            
            option = QTextOption()
            option.setAlignment(Qt.AlignmentFlag.AlignCenter)
            doc.setDefaultTextOption(option)
            
            color_name = text_color_name.name()
            import html
            safe_text = html.escape(name_text).replace(' ', '<br>')
            weight = "bold" if is_bold_name else "normal"
            html_content = f"<div style='color:{color_name}; font-family:{font_name.family()}; font-size:{fitted_font_size}pt; font-weight:{weight};' align='center'>{safe_text}</div>"
            doc.setHtml(html_content)
            
            text_height = doc.size().height()
            center_y = rect.y() + rect.height() * 0.55
            name_area_y = center_y - text_height / 2 + rect.height() * 0.1
            
            painter.translate(name_area_x, name_area_y)
            doc.drawContents(painter)
            
            painter.restore()
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, num_text)


class EditCellDialog(QDialog):
    def __init__(self, data, coords=None, parent=None):
        super().__init__(parent)
        
        title = "Настройка залы"
        if coords:
            r, c = coords
            
            col_char = ""
            if c < COLS:
                col_char = chr(ord('A') + c)
            elif c == COLS:
                col_char = "X"
            elif c == COLS + 1:
                col_char = "Z"
                
            row_num = ""
            if c < COLS:
                row_num = str(ROWS - r)
            else:
                row_num = str(6 - r)
            
            title = f"Настройка залы [{col_char}{row_num}]"
            
        self.setWindowTitle(title)
        self.resize(700, 550)
        self.data = data.copy()
        
        self.current_colors = {
            'color': self.data.get('color', '#CCCCCC'),
            'text_color': self.data.get('text_color', '#000000'),
            'text_color_name': self.data.get('text_color_name', '#000000')
        }
        
        self.color_buttons = []
        
        self.init_ui()
        self.update_preview()
        self.on_type_changed(self.combo_type.currentText(), initial=True)

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Верхняя часть: Тип комнаты
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип залы:"))
        self.combo_type = QComboBox()
        self.combo_type.addItems(ROOM_TYPES.keys())
        
        current_type = self.data.get('room_type', 'Обычная зала')
        if current_type in ROOM_TYPES:
            self.combo_type.setCurrentText(current_type)
        
        self.combo_type.currentTextChanged.connect(self.on_type_changed)
        type_layout.addWidget(self.combo_type)
        main_layout.addLayout(type_layout)

        # Центральная часть
        center_layout = QHBoxLayout()
        
        # --- Левая колонка: Настройки ---
        settings_layout = QVBoxLayout()
        
        # Группа: Основное
        group_main = QGroupBox("Основные данные")
        form_layout = QVBoxLayout()
        
        h_num = QHBoxLayout()
        h_num.addWidget(QLabel("Номер:"))
        self.input_number = QLineEdit(str(self.data.get('number', '')))
        self.input_number.textChanged.connect(self.update_preview)
        h_num.addWidget(self.input_number)
        form_layout.addLayout(h_num)
        
        h_name = QHBoxLayout()
        h_name.addWidget(QLabel("Имя:"))
        self.input_name = QLineEdit(self.data.get('name', ''))
        self.input_name.textChanged.connect(self.update_preview)
        h_name.addWidget(self.input_name)
        form_layout.addLayout(h_name)
        
        group_main.setLayout(form_layout)
        settings_layout.addWidget(group_main)
        
        # Группа: Цвета
        group_colors = QGroupBox("Цвета")
        colors_layout = QVBoxLayout()
        
        self.btn_color = QPushButton("Цвет фона")
        self.update_btn_style(self.btn_color, self.current_colors['color'])
        self.btn_color.clicked.connect(lambda: self.choose_color('color', self.btn_color))
        colors_layout.addWidget(self.btn_color)
        
        # Палитра цветов
        palette_layout = QGridLayout()
        palette_layout.setSpacing(5)
        for i, color_hex in enumerate(PRESET_COLORS):
            btn = QPushButton()
            btn.setFixedSize(25, 25)
            btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #555;")
            btn.clicked.connect(lambda checked, c=color_hex: self.set_preset_color(c))
            self.color_buttons.append((btn, color_hex))
            palette_layout.addWidget(btn, 0, i)
        
        colors_layout.addLayout(palette_layout)
        self.update_palette_checks()

        self.btn_text_color = QPushButton("Цвет номера")
        self.update_btn_style(self.btn_text_color, self.current_colors['text_color'])
        self.btn_text_color.clicked.connect(lambda: self.choose_color('text_color', self.btn_text_color))
        colors_layout.addWidget(self.btn_text_color)

        self.btn_name_color = QPushButton("Цвет имени")
        self.update_btn_style(self.btn_name_color, self.current_colors['text_color_name'])
        self.btn_name_color.clicked.connect(lambda: self.choose_color('text_color_name', self.btn_name_color))
        colors_layout.addWidget(self.btn_name_color)
        
        group_colors.setLayout(colors_layout)
        settings_layout.addWidget(group_colors)
        
        # Группа: Шрифты
        group_fonts = QGroupBox("Шрифты")
        fonts_layout = QVBoxLayout()
        
        # Номер
        h_font_num = QHBoxLayout()
        h_font_num.addWidget(QLabel("Номер:"))
        self.spin_size_num = QSpinBox()
        self.spin_size_num.setRange(8, 72)
        self.spin_size_num.setValue(int(self.data.get('font_size_num', 24)))
        self.spin_size_num.valueChanged.connect(self.update_preview)
        h_font_num.addWidget(self.spin_size_num)
        
        self.chk_bold_num = QCheckBox("Жирный")
        self.chk_bold_num.setChecked(self.data.get('font_weight_num') == 'bold')
        self.chk_bold_num.stateChanged.connect(self.update_preview)
        h_font_num.addWidget(self.chk_bold_num)
        fonts_layout.addLayout(h_font_num)
        
        # Имя
        h_font_name = QHBoxLayout()
        h_font_name.addWidget(QLabel("Имя:"))
        self.spin_size_name = QSpinBox()
        self.spin_size_name.setRange(8, 72)
        self.spin_size_name.setValue(int(self.data.get('font_size_name', 12)))
        self.spin_size_name.valueChanged.connect(self.update_preview)
        h_font_name.addWidget(self.spin_size_name)
        
        self.chk_bold_name = QCheckBox("Жирный")
        self.chk_bold_name.setChecked(self.data.get('font_weight_name') == 'bold')
        self.chk_bold_name.stateChanged.connect(self.update_preview)
        h_font_name.addWidget(self.chk_bold_name)
        fonts_layout.addLayout(h_font_name)
        
        group_fonts.setLayout(fonts_layout)
        settings_layout.addWidget(group_fonts)
        
        settings_layout.addStretch()
        center_layout.addLayout(settings_layout, stretch=1)
        
        # --- Правая колонка: Предпросмотр ---
        preview_layout = QVBoxLayout()
        preview_label = QLabel("Предпросмотр (1:1):")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        self.preview_widget = CellPreviewWidget()
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        preview_layout.addStretch()
        
        center_layout.addLayout(preview_layout, stretch=1)
        
        main_layout.addLayout(center_layout)

        # Кнопки OK/Cancel
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

        self.setLayout(main_layout)

    def update_btn_style(self, btn, color_str):
        bg_color = QColor(color_str)
        text_color = "black" if bg_color.lightness() > 128 else "white"
        btn.setStyleSheet(f"background-color: {color_str}; color: {text_color}; font-weight: bold; border-radius: 4px; padding: 5px;")

    def auto_adjust_text_color(self, bg_hex):
        bg = bg_hex.lower()
        black_text_bgs = ["#ffffff", "#a5a5a5", "#ffc000", "#cccccc"]
        white_text_bgs = ["#70ad47", "#3e68b3", "#ff0000", "#000000", "#666666"]
        
        new_color = None
        if bg in black_text_bgs:
            new_color = "#000000"
        elif bg in white_text_bgs:
            new_color = "#ffffff"
        else:
            c = QColor(bg)
            new_color = "#000000" if c.lightness() > 128 else "#ffffff"
            
        if new_color:
            self.current_colors['text_color'] = new_color
            self.current_colors['text_color_name'] = new_color
            self.update_btn_style(self.btn_text_color, new_color)
            self.update_btn_style(self.btn_name_color, new_color)

    def set_preset_color(self, color_hex):
        self.current_colors['color'] = color_hex
        self.update_btn_style(self.btn_color, color_hex)
        self.auto_adjust_text_color(color_hex)
        self.update_palette_checks()
        self.update_preview()

    def update_palette_checks(self):
        current_bg = self.current_colors['color'].lower()
        for btn, color_hex in self.color_buttons:
            if color_hex.lower() == current_bg:
                btn.setText("✔")
                check_color = "black" if QColor(color_hex).lightness() > 128 else "white"
                btn.setStyleSheet(f"background-color: {color_hex}; color: {check_color}; font-weight: bold; border: 2px solid #fff;")
            else:
                btn.setText("")
                btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid #555;")

    def choose_color(self, key, btn):
        current = self.current_colors[key]
        color = QColorDialog.getColor(QColor(current), self, "Выберите цвет")
        if color.isValid():
            hex_color = color.name()
            self.current_colors[key] = hex_color
            self.update_btn_style(btn, hex_color)
            if key == 'color':
                self.auto_adjust_text_color(hex_color)
                self.update_palette_checks()
            self.update_preview()

    def on_type_changed(self, type_name, initial=False):
        if type_name in ROOM_TYPES:
            preset = ROOM_TYPES[type_name]
            
            if not initial:
                self.current_colors['color'] = preset['color']
                self.current_colors['text_color'] = preset['text_color']
                self.current_colors['text_color_name'] = preset['text_color_name']
                
                self.update_btn_style(self.btn_color, self.current_colors['color'])
                self.update_btn_style(self.btn_text_color, self.current_colors['text_color'])
                self.update_btn_style(self.btn_name_color, self.current_colors['text_color_name'])
                
                self.chk_bold_num.setChecked(preset['font_weight_num'] == 'bold')
                self.chk_bold_name.setChecked(preset['font_weight_name'] == 'bold')
                
                self.update_palette_checks()
            
            # Reset defaults
            self.input_name.setEnabled(True)
            self.input_number.setEnabled(True)
            self.btn_color.setEnabled(True)
            for btn, _ in self.color_buttons:
                btn.setEnabled(True)
            
            if type_name == "Зала внутреннего контура":
                self.input_name.setText("Зала внутреннего контура")
                self.input_name.setEnabled(False)
                # Set default description and signal if empty
                if not self.data.get('description_text'):
                    self.data['description_text'] = "В зале находится таймер на 20 мин и экран, транслирующий вид на какой-то город. Нет никакого испытания, можно кратко описать, чем занимаются персонажи."
                if not self.data.get('signal_text'):
                    self.data['signal_text'] = "Досточтимые рыцари! Вы находитесь в зале внутреннего контура. Двери залы откроются через 20 минут."
            
            elif type_name == "Белая зала":
                self.input_number.setText("1001")
                self.input_number.setEnabled(False)
                if not initial or self.input_name.text() == "Введите имя залы":
                    self.input_name.setText("Точка нужной координаты")
                
                self.btn_color.setEnabled(False)
                for btn, _ in self.color_buttons:
                    btn.setEnabled(False)
                    
                if not self.data.get('description_text'):
                    self.data['description_text'] = "Играет торжественная музыка. В центре залы находится консоль, в которую можно ввести требуемое для исполнения желание. В комнате стоят конструкторы, они смотрят на героев, что-то делают."
                if not self.data.get('signal_text'):
                    self.data['signal_text'] = "Досточтимые рыцари! Ваш поход завершен. Вы находитесь в белой зале конструктора под номером 1001. Для окончания похода просканируйте вашу эмблему, введите желание, требуемое для исполнения, а затем нажмите кнопку ввода."

            elif type_name == "Транспортная зала":
                self.input_number.setText("2761")
                if not initial or self.input_name.text() == "Введите имя залы":
                    self.input_name.setText("Переход вертикального уровня")
                
                self.btn_color.setEnabled(False)
                for btn, _ in self.color_buttons:
                    btn.setEnabled(False)
                    
                if not self.data.get('description_text'):
                    self.data['description_text'] = "Двери залы открыты. В центре залы стоит кабина лифта, напоминающего лифт из дорого отеля начала 21-го века.\nС помощью лифта можно переместиться на Оранжевый или Фиолетовый уровень конструктора"
                if not self.data.get('signal_text'):
                    self.data['signal_text'] = "Досточтимые рыцари! Вы находитесь в транспортной зале Конструктора. Двери залы открыты. Вы можете использовать залу для перемещения между уровнями Конструктора."

            else:
                # Restore default name if it was locked
                if self.input_name.text() == "Зала внутреннего контура":
                    self.input_name.setText("")
            
            self.update_preview()

    def update_preview(self):
        preview_data = {
            'number': self.input_number.text(),
            'name': self.input_name.text(),
            'room_type': self.combo_type.currentText(),
            'color': self.current_colors['color'],
            'text_color': self.current_colors['text_color'],
            'text_color_name': self.current_colors['text_color_name'],
            'font_size_num': self.spin_size_num.value(),
            'font_size_name': self.spin_size_name.value(),
            'font_weight_num': 'bold' if self.chk_bold_num.isChecked() else 'normal',
            'font_weight_name': 'bold' if self.chk_bold_name.isChecked() else 'normal'
        }
        self.preview_widget.update_data(preview_data)

    def get_data(self):
        data = {
            'number': self.input_number.text(),
            'name': self.input_name.text(),
            'room_type': self.combo_type.currentText(),
            'color': self.current_colors['color'],
            'text_color': self.current_colors['text_color'],
            'text_color_name': self.current_colors['text_color_name'],
            'font_size_num': self.spin_size_num.value(),
            'font_size_name': self.spin_size_name.value(),
            'font_weight_num': 'bold' if self.chk_bold_num.isChecked() else 'normal',
            'font_weight_name': 'bold' if self.chk_bold_name.isChecked() else 'normal',
            # Preserve description and signal text if they were set in on_type_changed
            'description_text': self.data.get('description_text', ''),
            'signal_text': self.data.get('signal_text', '')
        }
        return data
