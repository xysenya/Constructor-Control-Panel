from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
                             QColorDialog, QFileDialog, QComboBox, QToolButton, QFontComboBox, 
                             QDialog, QLabel, QSpinBox, QCheckBox, QDialogButtonBox, QSlider, QSizePolicy, QLayout)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRect, QPoint
from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QTextImageFormat, QIcon, QAction, QImage, QTextListFormat
import os
from config import PLAYER_BUTTONS_DIR

# --- Внутренний класс FlowLayout ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=2):
        super(FlowLayout, self).__init__(parent)
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
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
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
        super(FlowLayout, self).setGeometry(rect)
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
        spacing = self.spacing()
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            spaceY = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)
            
            item_size = item.sizeHint()
            item_width = item_size.width()
            item_height = item_size.height()
            
            nextX = x + item_width + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item_width + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x = nextX
            lineHeight = max(lineHeight, item_height)

        return y + lineHeight - rect.y()

class ImageResizeDialog(QDialog):
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Размер изображения")
        self.original_width = width
        self.original_height = height
        self.original_ratio = width / height if height > 0 else 1.0
        
        layout = QVBoxLayout(self)
        
        # Scale Slider
        h_scale = QHBoxLayout()
        h_scale.addWidget(QLabel("Масштаб (%):"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 200) # 1% to 200%
        self.slider.setValue(100)
        h_scale.addWidget(self.slider)
        self.lbl_percent = QLabel("100%")
        h_scale.addWidget(self.lbl_percent)
        layout.addLayout(h_scale)
        
        # Width
        h_w = QHBoxLayout()
        h_w.addWidget(QLabel("Ширина (px):"))
        self.spin_w = QSpinBox()
        self.spin_w.setRange(1, 5000)
        self.spin_w.setValue(int(width))
        h_w.addWidget(self.spin_w)
        layout.addLayout(h_w)
        
        # Height
        h_h = QHBoxLayout()
        h_h.addWidget(QLabel("Высота (px):"))
        self.spin_h = QSpinBox()
        self.spin_h.setRange(1, 5000)
        self.spin_h.setValue(int(height))
        h_h.addWidget(self.spin_h)
        layout.addLayout(h_h)
        
        # Aspect Ratio
        self.chk_ratio = QCheckBox("Сохранять пропорции")
        self.chk_ratio.setChecked(True)
        layout.addWidget(self.chk_ratio)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect signals
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.spin_w.valueChanged.connect(self.on_width_changed)
        self.spin_h.valueChanged.connect(self.on_height_changed)
        
        self.is_updating = False

    def on_slider_changed(self, val):
        if self.is_updating: return
        self.is_updating = True
        
        self.lbl_percent.setText(f"{val}%")
        factor = val / 100.0
        
        new_w = int(self.original_width * factor)
        new_h = int(self.original_height * factor)
        
        self.spin_w.setValue(new_w)
        self.spin_h.setValue(new_h)
        
        self.is_updating = False

    def on_width_changed(self, val):
        if self.is_updating: return
        self.is_updating = True
        
        if self.chk_ratio.isChecked():
            new_h = int(val / self.original_ratio)
            self.spin_h.setValue(new_h)
            
        percent = int((val / self.original_width) * 100)
        self.slider.blockSignals(True)
        self.slider.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")
        self.slider.blockSignals(False)
            
        self.is_updating = False
            
    def on_height_changed(self, val):
        if self.is_updating: return
        self.is_updating = True
        
        if self.chk_ratio.isChecked():
            new_w = int(val * self.original_ratio)
            self.spin_w.setValue(new_w)
            
        percent = int((val / self.original_height) * 100)
        self.slider.blockSignals(True)
        self.slider.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")
        self.slider.blockSignals(False)
            
        self.is_updating = False

    def get_size(self):
        return self.spin_w.value(), self.spin_h.value()

class FormattingToolbar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        size_policy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        size_policy.setHeightForWidth(True)
        self.setSizePolicy(size_policy)
        
        self.setMinimumWidth(1)
        
        self.current_editor = None
        self.init_ui()

    def set_editor(self, editor):
        self.current_editor = editor

    def init_ui(self):
        layout = FlowLayout(self, margin=5, spacing=5)
        
        self.combo_font = QFontComboBox()
        self.combo_font.currentFontChanged.connect(self.text_family)
        self.combo_font.setMinimumWidth(120)
        layout.addWidget(self.combo_font)

        self.combo_size = QComboBox()
        self.combo_size.setEditable(True)
        sizes = [6, 8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
        self.combo_size.addItems([str(s) for s in sizes])
        self.combo_size.setCurrentText("14")
        self.combo_size.textActivated.connect(self.text_size)
        self.combo_size.setFixedWidth(50)
        layout.addWidget(self.combo_size)

        def create_btn(text, callback, checkable=False, icon_path=None, icon_theme=None, tooltip=None):
            btn = QToolButton()
            btn.setText(text)
            
            if icon_path:
                full_path = os.path.join(PLAYER_BUTTONS_DIR, icon_path)
                if os.path.exists(full_path):
                    btn.setIcon(QIcon(full_path))
                    btn.setText("")
            elif icon_theme:
                icon = QIcon.fromTheme(icon_theme)
                if not icon.isNull():
                    btn.setIcon(icon)
                    btn.setText("")
            
            btn.setFixedSize(30, 30)
            btn.setIconSize(QSize(24, 24))
            
            if checkable:
                btn.setCheckable(True)
            btn.clicked.connect(callback)
            if tooltip:
                btn.setToolTip(tooltip)
            return btn

        self.btn_bold = create_btn("B", self.text_bold, True, icon_theme="format-text-bold", tooltip="Жирный")
        layout.addWidget(self.btn_bold)

        self.btn_italic = create_btn("I", self.text_italic, True, icon_theme="format-text-italic", tooltip="Курсив")
        layout.addWidget(self.btn_italic)
        
        self.btn_underline = create_btn("U", self.text_underline, True, icon_theme="format-text-underline", tooltip="Подчеркнутый")
        layout.addWidget(self.btn_underline)

        btn_color = create_btn("", self.text_color, icon_path="color.png", tooltip="Цвет текста")
        layout.addWidget(btn_color)

        layout.addWidget(create_btn("L", lambda: self.text_align(Qt.AlignmentFlag.AlignLeft), icon_theme="format-justify-left", tooltip="По левому краю"))
        layout.addWidget(create_btn("C", lambda: self.text_align(Qt.AlignmentFlag.AlignCenter), icon_theme="format-justify-center", tooltip="По центру"))
        layout.addWidget(create_btn("R", lambda: self.text_align(Qt.AlignmentFlag.AlignRight), icon_theme="format-justify-right", tooltip="По правому краю"))
        layout.addWidget(create_btn("J", lambda: self.text_align(Qt.AlignmentFlag.AlignJustify), icon_path="wideallign.png", tooltip="По ширине"))

        layout.addWidget(create_btn("", lambda: self.create_list(QTextListFormat.Style.ListDisc), icon_path="list-bullet.png", tooltip="Маркированный список"))
        layout.addWidget(create_btn("", lambda: self.create_list(QTextListFormat.Style.ListDecimal), icon_path="list-number.png", tooltip="Нумерованный список"))

        layout.addWidget(create_btn("", self.insert_image, icon_path="image.png", tooltip="Вставить изображение"))
        layout.addWidget(create_btn("", self.resize_image, icon_path="resize.png", tooltip="Изменить размер изображения"))

    def minimumSizeHint(self):
        return QSize(100, 40)

    def _check_editor(self):
        return self.current_editor is not None

    def text_bold(self):
        if not self._check_editor(): return
        fmt = QTextCharFormat()
        weight = QFont.Weight.Bold if self.btn_bold.isChecked() else QFont.Weight.Normal
        fmt.setFontWeight(weight)
        self.merge_format_on_word_or_selection(fmt)

    def text_italic(self):
        if not self._check_editor(): return
        fmt = QTextCharFormat()
        fmt.setFontItalic(self.btn_italic.isChecked())
        self.merge_format_on_word_or_selection(fmt)

    def text_underline(self):
        if not self._check_editor(): return
        fmt = QTextCharFormat()
        fmt.setFontUnderline(self.btn_underline.isChecked())
        self.merge_format_on_word_or_selection(fmt)

    def text_family(self, font):
        if not self._check_editor(): return
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self.merge_format_on_word_or_selection(fmt)

    def text_size(self, text):
        if not self._check_editor(): return
        if not text.isdigit(): return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(float(text))
        self.merge_format_on_word_or_selection(fmt)

    def text_color(self):
        if not self._check_editor(): return
        col = QColorDialog.getColor(self.current_editor.textColor(), self)
        if not col.isValid():
            return
        fmt = QTextCharFormat()
        fmt.setForeground(col)
        self.merge_format_on_word_or_selection(fmt)

    def text_align(self, align):
        if not self._check_editor(): return
        self.current_editor.setAlignment(align)

    def create_list(self, style):
        if not self._check_editor(): return
        cursor = self.current_editor.textCursor()
        cursor.createList(style)

    def insert_image(self):
        if not self._check_editor(): return
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            image = QImage(file_path)
            if image.isNull(): return
            
            editor_width = self.current_editor.viewport().width()
            target_width = int(editor_width * 0.75)
            
            if target_width > 0:
                scaled_image = image.scaledToWidth(target_width, Qt.TransformationMode.SmoothTransformation)
                width = scaled_image.width()
                height = scaled_image.height()
            else:
                width = image.width()
                height = image.height()

            image_format = QTextImageFormat()
            image_format.setName(file_path)
            image_format.setWidth(width)
            image_format.setHeight(height)
            
            cursor = self.current_editor.textCursor()
            cursor.insertImage(image_format)

    def resize_image(self):
        if not self._check_editor(): return
        
        cursor = self.current_editor.textCursor()
        fmt = cursor.charFormat().toImageFormat()
        
        if not fmt.isValid():
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.KeepAnchor)
            fmt = cursor.charFormat().toImageFormat()
        
        if not fmt.isValid():
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.MoveAnchor)
            cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor)
            fmt = cursor.charFormat().toImageFormat()

        if fmt.isValid():
            dialog = ImageResizeDialog(fmt.width(), fmt.height(), self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_w, new_h = dialog.get_size()
                fmt.setWidth(new_w)
                fmt.setHeight(new_h)
                cursor.mergeCharFormat(fmt)

    def merge_format_on_word_or_selection(self, format):
        cursor = self.current_editor.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(format)
        self.current_editor.mergeCurrentCharFormat(format)

class RichTextEditor(QWidget):
    textChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
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
        self.text_edit.currentCharFormatChanged.connect(self.current_char_format_changed)
        self.text_edit.textChanged.connect(self.textChanged.emit)
        
        self.toolbar = FormattingToolbar()
        self.toolbar.set_editor(self.text_edit)
        self.toolbar.hide()
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.text_edit)

    def set_edit_mode(self, enabled):
        self.text_edit.setReadOnly(not enabled)
        if enabled:
            self.toolbar.show()
        else:
            self.toolbar.hide()

    def current_char_format_changed(self, format):
        font = format.font()
        self.toolbar.combo_font.setCurrentIndex(self.toolbar.combo_font.findText(QFont(font).family()))
        self.toolbar.combo_size.setCurrentIndex(self.toolbar.combo_size.findText(str(int(font.pointSize()))))
        self.toolbar.btn_bold.setChecked(font.bold())
        self.toolbar.btn_italic.setChecked(font.italic())
        self.toolbar.btn_underline.setChecked(font.underline())
        
    def toHtml(self):
        return self.text_edit.toHtml()
        
    def setHtml(self, html):
        self.text_edit.setHtml(html)
        
    def toPlainText(self):
        return self.text_edit.toPlainText()
        
    def setPlainText(self, text):
        self.text_edit.setPlainText(text)
