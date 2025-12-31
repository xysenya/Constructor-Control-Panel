from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QFrame, QCheckBox, QLineEdit, 
                             QMenu, QMessageBox, QFileDialog, QGridLayout, QPlainTextEdit, QSizePolicy, QLayout, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF, QPointF, QRect, QPoint, QEvent
from PyQt6.QtGui import QFont, QColor, QPalette, QPainter, QBrush, QPen, QTextDocument, QTextOption, QPolygonF, QFontMetrics, QAction
from config import FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, BASE_ROOM_SOUNDS_DIR, AUDIO_PANEL_SOUNDS_DIR, CELL_RADIUS, ROWS, COLS
from utils import get_font_name, get_fitted_font_size
from editor_window import EditCellDialog
from text_formatting import FormattingToolbar
import os
import math

# --- Dynamic Label ---
class DynamicLabel(QLabel):
    def __init__(self, text, font, parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setFont(font)
        self._original_font = font

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        font = self._original_font
        font_size = font.pointSize()
        fm = QFontMetrics(font)
        rect = self.contentsRect()
        text_rect = fm.boundingRect(rect, Qt.TextFlag.TextWordWrap, self.text())
        
        while (text_rect.width() > rect.width() or text_rect.height() > rect.height()) and font_size > 8:
            font_size -= 1
            font.setPointSize(font_size)
            fm = QFontMetrics(font)
            text_rect = fm.boundingRect(rect, Qt.TextFlag.TextWordWrap, self.text())
            
        self.setFont(font)

# --- FlowLayout Implementation ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
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
        
        # Group items into lines
        lines = []
        current_line = []
        current_line_width = 0
        
        for item in self.itemList:
            wid = item.widget()
            spaceX = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            
            item_width = item.sizeHint().width()
            
            if x + item_width + spaceX > rect.right() and current_line:
                # New line
                lines.append((current_line, current_line_width, lineHeight))
                x = rect.x()
                y = y + lineHeight + spacing # Vertical spacing
                current_line = []
                current_line_width = 0
                lineHeight = 0

            current_line.append(item)
            current_line_width += item_width + spaceX
            x += item_width + spaceX
            lineHeight = max(lineHeight, item.sizeHint().height())
            
        if current_line:
            lines.append((current_line, current_line_width, lineHeight))

        # Calculate total height
        total_height = 0
        for _, _, h in lines:
            total_height += h + spacing
        if lines:
            total_height -= spacing # Remove last spacing
            
        if testOnly:
            return total_height + rect.y() # Add top margin/offset

        # Place items
        y = rect.y()
        for line_items, line_width, line_h in lines:
            # Center the line
            # line_width includes trailing spacing, remove it for centering calc
            actual_width = line_width - spacing 
            x_start = rect.x() + (rect.width() - actual_width) / 2
            
            x = x_start
            for item in line_items:
                wid = item.widget()
                spaceX = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
                
                item.setGeometry(QRect(QPoint(int(x), int(y)), item.sizeHint()))
                x += item.sizeHint().width() + spaceX
            
            y += line_h + spacing

        return y - rect.y() # Height used

# --- Square Widget Mixin ---
class SquareWidgetMixin:
    def heightForWidth(self, width):
        return width
        
    def sizeHint(self):
        return QSize(100, 100)

class CellWidget(QWidget):
    clicked = pyqtSignal() # Signal for click
    
    def __init__(self, data, size=100, parent=None):
        super().__init__(parent)
        self.data = data
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def update_data(self, data):
        self.data = data
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.data: return

        color_str = self.data.get('color', '#CCCCCC')
        if not isinstance(color_str, str) or not color_str.startswith('#'):
            color_str = '#CCCCCC'
        bg_color = QColor(color_str)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
            
        rect = QRectF(self.rect())
        painter.drawRoundedRect(rect, CELL_RADIUS, CELL_RADIUS)
        
        num_text = str(self.data.get('number', ''))
        if self.data.get('room_type') == 'Сгенерированная зала':
            num_text = f"-{num_text}-"
            
        text_color = QColor(self.data.get('text_color', '#000000'))
        painter.setPen(text_color)
        
        font_size_num = int(self.data.get('font_size_num', 24) * (self.width() / 100.0))
        is_bold_num = self.data.get('font_weight_num') == 'bold'
        font_num = QFont(get_font_name(is_bold_num), font_size_num)
        painter.setFont(font_num)
        
        # Always draw number in the center, no name
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, num_text)

class NavButton(QPushButton, SquareWidgetMixin):
    def __init__(self, r, c, data, parent=None):
        super().__init__(parent)
        self.r = r
        self.c = c
        self.data = data
        
        # Allow shrinking but prefer square
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setMinimumSize(10, 10)
        self.setMaximumSize(100, 100)
        
        self.is_hovered = False
        
    def enterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        x_offset = (self.width() - side) / 2
        y_offset = (self.height() - side) / 2
        rect = QRectF(x_offset, y_offset, side, side)
        
        color_str = self.data.get('color', '#CCCCCC')
        if not isinstance(color_str, str) or not color_str.startswith('#'):
            color_str = '#CCCCCC'
        bg_color = QColor(color_str)
        painter.setBrush(QBrush(bg_color))
        
        if self.is_hovered:
            pen = QPen(QColor(255, 215, 0))
            pen.setWidth(3)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            
        if self.is_hovered:
            inset = 1.5
            rect = rect.adjusted(inset, inset, -inset, -inset)
            
        painter.drawRoundedRect(rect, CELL_RADIUS, CELL_RADIUS)
        
        num_text = str(self.data.get('number', ''))
        if self.data.get('room_type') == 'Сгенерированная зала':
            num_text = f"-{num_text}-"
            
        text_color = QColor(self.data.get('text_color', '#000000'))
        painter.setPen(text_color)
        
        scale_factor = side / 100.0
        font_size_num = int(self.data.get('font_size_num', 24) * 0.9 * scale_factor)
        is_bold_num = self.data.get('font_weight_num') == 'bold'
        font_num = QFont(get_font_name(is_bold_num), max(8, font_size_num))
        painter.setFont(font_num)
        
        name_text = str(self.data.get('name', '')).strip()
        room_type = self.data.get('room_type', '')
        is_inner_contour = room_type == 'Зала внутреннего контура'
        
        if is_inner_contour:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, num_text)
        elif name_text:
            num_rect = QRectF(rect.x(), rect.y() + rect.height() * 0.05, rect.width(), rect.height() * 0.3)
            painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, num_text)
            
            painter.save()
            text_color_name = QColor(self.data.get('text_color_name', '#000000'))
            
            initial_font_size_name = int(self.data.get('font_size_name', 12) * 0.9 * scale_factor)
            is_bold_name = self.data.get('font_weight_name') == 'bold'
            fitted_font_size = get_fitted_font_size(name_text, is_bold_name, initial_font_size_name, rect.width() * 0.95)
            
            font_name = QFont(get_font_name(is_bold_name), max(6, fitted_font_size))
            
            name_area_width = rect.width() - 10
            name_area_x = rect.x() + 5
            
            color_name = text_color_name.name()
            import html
            safe_text = html.escape(name_text).replace(' ', '<br>')
            weight = "bold" if is_bold_name else "normal"
            html_content = f"<div style='color:{color_name}; font-family:{font_name.family()}; font-size:{fitted_font_size}pt; font-weight:{weight};' align='center'>{safe_text}</div>"
            
            doc = QTextDocument()
            doc.setDefaultFont(font_name)
            doc.setHtml(html_content)
            doc.setTextWidth(name_area_width)
            
            text_height = doc.size().height()
            center_y = rect.y() + rect.height() * 0.55
            name_area_y = center_y - text_height / 2 + rect.height() * 0.1
            
            painter.translate(name_area_x, name_area_y)
            doc.drawContents(painter)
            painter.restore()
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, num_text)

class NavSpacer(QWidget, SquareWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setMinimumSize(10, 10)
        self.setMaximumSize(100, 100)
        self.setStyleSheet("background: transparent;")

class CompassWidget(QWidget, SquareWidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setMinimumSize(10, 10)
        self.setMaximumSize(100, 100)
        
    def heightForWidth(self, width):
        return width
        
    def sizeHint(self):
        return QSize(100, 100)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        side = min(self.width(), self.height())
        center = QPointF(self.width() / 2, self.height() / 2)
        
        radius = side * 0.25
        inner_radius = radius * 0.3
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#666666")))
        
        points = []
        for i in range(8):
            angle = i * math.pi / 4
            r = radius if i % 2 == 0 else inner_radius
            points.append(QPointF(center.x() + r * math.sin(angle), center.y() - r * math.cos(angle)))
            
        painter.drawPolygon(QPolygonF(points))
        
        font_size = int(side * 0.12)
        font = QFont(FONT_FAMILY_BOLD, max(8, font_size))
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        
        offset = radius + font_size
        
        painter.drawText(QRectF(center.x() - 20, center.y() - offset - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, "С")
        painter.drawText(QRectF(center.x() - 20, center.y() + offset - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, "Ю")
        painter.drawText(QRectF(center.x() + offset - 20, center.y() - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, "В")
        painter.drawText(QRectF(center.x() - offset - 20, center.y() - 20, 40, 40), Qt.AlignmentFlag.AlignCenter, "З")

class NavPanel(QWidget):
    nav_signal = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QGridLayout(self)
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        
    def update_nav(self, r, c, cell_data):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        compass = CompassWidget()
        self.layout.addWidget(compass, 1, 1)
        
        neighbors_map = {
            (r + 1, c): (0, 1), # Top
            (r - 1, c): (2, 1), # Bottom
            (r, c - 1): (1, 0), # Left
            (r, c + 1): (1, 2)  # Right
        }
        
        # Fill all 9 slots (except center 1,1) to maintain grid structure
        for grid_r in range(3):
            for grid_c in range(3):
                if grid_r == 1 and grid_c == 1:
                    continue # Center is compass
                
                # Find if there is a neighbor for this slot
                target_coord = None
                for coord, grid_pos in neighbors_map.items():
                    if grid_pos == (grid_r, grid_c):
                        target_coord = coord
                        break
                
                widget_to_add = None
                
                if target_coord:
                    nr, nc = target_coord
                    
                    # Check exclusion logic
                    is_excluded = False
                    if c == COLS - 1 and nc >= COLS: # G column excluding X/Z
                        is_excluded = True
                    
                    if not is_excluded and (nr, nc) in cell_data:
                        btn = NavButton(nr, nc, cell_data[(nr, nc)])
                        btn.clicked.connect(lambda checked, nr=nr, nc=nc: self.nav_signal.emit(nr, nc))
                        widget_to_add = btn
                
                if widget_to_add is None:
                    # Add a spacer widget to hold the cell size
                    widget_to_add = NavSpacer()
                
                self.layout.addWidget(widget_to_add, grid_r, grid_c)
                
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        self.layout.setColumnStretch(2, 1)
        self.layout.setRowStretch(0, 1)
        self.layout.setRowStretch(1, 1)
        self.layout.setRowStretch(2, 1)

class DetailedView(QWidget):
    back_signal = pyqtSignal()
    cell_changed_signal = pyqtSignal(int, int)
    data_changed_signal = pyqtSignal(int, int, str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self.r = 0
        self.c = 0
        self.cell_data_ref = {} 
        
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.cell_preview = CellWidget({}, size=100)
        self.cell_preview.clicked.connect(self.open_edit_dialog)
        header_layout.addWidget(self.cell_preview)
        
        info_layout = QVBoxLayout()
        self.lbl_name = QLabel("NAME")
        self.lbl_name.setFont(QFont(FONT_FAMILY_BOLD, 28))
        self.lbl_name.setStyleSheet("color: #ffffff;")
        self.lbl_name.setWordWrap(True)
        info_layout.addWidget(self.lbl_name)
        
        self.lbl_coord = QLabel("Координата: A1")
        self.lbl_coord.setFont(QFont(FONT_FAMILY_REGULAR, 18))
        self.lbl_coord.setStyleSheet("color: #b0b0b0;")
        info_layout.addWidget(self.lbl_coord)
        
        header_layout.addLayout(info_layout)
        header_layout.addStretch()
        
        btn_back = QPushButton("Назад")
        btn_back.setFixedSize(100, 40)
        btn_back.setStyleSheet("""
            QPushButton { background-color: #505050; color: white; border-radius: 5px; font-weight: bold; font-family: 'Epilepsy Sans B'; font-size: 16px; }
            QPushButton:hover { background-color: #606060; }
        """)
        btn_back.clicked.connect(self.on_back_clicked)
        header_layout.addWidget(btn_back)
        
        self.layout.addLayout(header_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #404040;")
        self.layout.addWidget(line)
        
        # Content
        content_layout = QHBoxLayout()
        
        # Left: Description
        desc_layout = QVBoxLayout()
        lbl_desc = DynamicLabel("Описание залы", QFont(FONT_FAMILY_BOLD, 22))
        desc_layout.addWidget(lbl_desc)
        
        # Frame for Description
        self.frame_desc = QFrame()
        self.frame_desc.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border: 1px solid #505050;
                border-radius: 8px;
            }
        """)
        frame_desc_layout = QVBoxLayout(self.frame_desc)
        frame_desc_layout.setContentsMargins(0, 0, 0, 0)
        
        # Revert to QTextEdit
        self.txt_desc = QTextEdit()
        self.txt_desc.setReadOnly(False) # Default Editable
        self.txt_desc.setFont(QFont(FONT_FAMILY_REGULAR, 14))
        self.txt_desc.setStyleSheet("""
            QTextEdit { 
                background-color: transparent; 
                color: white; 
                border: none;
                padding: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #707070;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.txt_desc.textChanged.connect(self.on_desc_changed)
        # Install event filter to track focus
        self.txt_desc.installEventFilter(self)
        frame_desc_layout.addWidget(self.txt_desc)
        
        desc_layout.addWidget(self.frame_desc)
        content_layout.addLayout(desc_layout, stretch=1)
        
        # Right: Audio & Nav
        right_layout = QVBoxLayout()
        
        # Nav Panel
        self.nav_panel = NavPanel()
        self.nav_panel.nav_signal.connect(self.on_navigate)
        
        # Center NavPanel
        nav_container = QHBoxLayout()
        nav_container.addStretch()
        nav_container.addWidget(self.nav_panel)
        nav_container.addStretch()
        right_layout.addLayout(nav_container)
        
        right_layout.addStretch()
        
        # Audio Controls
        lbl_audio = DynamicLabel("Звуковой сигнал авторизации:", QFont(FONT_FAMILY_BOLD, 22))
        right_layout.addWidget(lbl_audio)
        
        # Flow Layout for Audio Buttons
        audio_btns_widget = QWidget()
        audio_btns_widget.setStyleSheet("background-color: transparent;")
        audio_flow = FlowLayout(audio_btns_widget)
        
        self.btn_play = QPushButton("Воспроизвести\nсигнал")
        self.btn_play.setMinimumSize(120, 50)
        self.btn_play.setStyleSheet("background-color: #4472c4; color: white; border-radius: 10px; font-weight: bold; font-family: 'Epilepsy Sans B';")
        self.btn_play.clicked.connect(self.on_play_click)
        self.btn_play.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_play.customContextMenuRequested.connect(self.on_play_context_menu)
        audio_flow.addWidget(self.btn_play)
        
        btn_error = QPushButton("ОШИБКА")
        btn_error.setMinimumSize(120, 50)
        btn_error.setStyleSheet("background-color: #c83232; color: white; border-radius: 10px; font-weight: bold; font-family: 'Epilepsy Sans B';")
        btn_error.clicked.connect(lambda: self.play_sound_file("Error.wav"))
        audio_flow.addWidget(btn_error)
        
        btn_complete = QPushButton("Испытание\nзавершено")
        btn_complete.setMinimumSize(120, 50)
        btn_complete.setStyleSheet("background-color: #70ad47; color: white; border-radius: 10px; font-weight: bold; font-family: 'Epilepsy Sans B';")
        btn_complete.clicked.connect(lambda: self.play_sound_file("ChallengeComplete.wav"))
        audio_flow.addWidget(btn_complete)
        
        right_layout.addWidget(audio_btns_widget)
        
        self.chk_key_action = QCheckBox("Учитывать ключевое действие")
        self.chk_key_action.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        self.chk_key_action.setStyleSheet("QCheckBox { color: white; }")
        self.chk_key_action.stateChanged.connect(self.on_key_action_changed)
        right_layout.addWidget(self.chk_key_action)
        
        # Frame for Signal Input
        self.frame_signal = QFrame()
        self.frame_signal.setStyleSheet("""
            QFrame {
                background-color: #353535;
                border: 1px solid #505050;
                border-radius: 8px;
            }
        """)
        frame_signal_layout = QVBoxLayout(self.frame_signal)
        frame_signal_layout.setContentsMargins(0, 0, 0, 0)
        
        # Changed to QTextEdit for formatting support
        self.input_signal = QTextEdit()
        self.input_signal.setReadOnly(False) # Default Editable
        self.input_signal.setFont(QFont(FONT_FAMILY_REGULAR, 14))
        self.input_signal.setStyleSheet("""
            QTextEdit { 
                background-color: transparent; 
                color: white; 
                border: none; 
                padding: 5px;
            }
            QScrollBar:vertical {
                border: none;
                background: #2b2b2b;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #505050;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #707070;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        self.input_signal.textChanged.connect(self.on_signal_changed)
        # Install event filter to track focus
        self.input_signal.installEventFilter(self)
        frame_signal_layout.addWidget(self.input_signal)
        
        right_layout.addWidget(self.frame_signal, stretch=1)
        
        content_layout.addLayout(right_layout, stretch=1)
        
        self.layout.addLayout(content_layout)
        
        # --- Formatting Toolbar ---
        self.formatting_toolbar = FormattingToolbar()
        self.formatting_toolbar.set_editor(self.txt_desc) # Default to desc
        self.formatting_toolbar.hide() # Default hidden
        self.layout.addWidget(self.formatting_toolbar)
        
        self.setLayout(self.layout)

    def set_edit_mode(self, enabled):
        # Only toggle toolbar visibility, text fields remain editable
        if enabled:
            self.formatting_toolbar.show()
        else:
            self.formatting_toolbar.hide()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.FocusIn:
            if obj == self.txt_desc:
                self.formatting_toolbar.set_editor(self.txt_desc)
            elif obj == self.input_signal:
                self.formatting_toolbar.set_editor(self.input_signal)
        return super().eventFilter(obj, event)

    def show_cell(self, r, c, data, all_cell_data=None):
        self.r = r
        self.c = c
        self.data = data
        if all_cell_data:
            self.cell_data_ref = all_cell_data
        
        self.cell_preview.update_data(data)
        
        name_text = str(data.get('name', '')).strip()
        if data.get('room_type') == 'Зала внутреннего контура':
            name_text = "ЗАЛА ВНУТРЕННЕГО КОНТУРА"
        self.lbl_name.setText(name_text.upper())
        
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
            row_num = str(6 - r) # Для X и Z

        self.lbl_coord.setText(f"Координата: {col_char}{row_num}")
        
        # Only update text if widget doesn't have focus to prevent cursor jump
        if not self.txt_desc.hasFocus():
            self.txt_desc.blockSignals(True)
            content = data.get('description_text', '')
            if '<' in content and '>' in content:
                self.txt_desc.setHtml(content)
            else:
                self.txt_desc.setPlainText(content)
            self.txt_desc.blockSignals(False)
        
        if not self.input_signal.hasFocus():
            self.input_signal.blockSignals(True)
            # Signal text is usually plain, but now we support HTML
            content = data.get('signal_text', '')
            if '<' in content and '>' in content:
                self.input_signal.setHtml(content)
            else:
                self.input_signal.setPlainText(content)
            self.input_signal.blockSignals(False)
        
        self.chk_key_action.blockSignals(True)
        self.chk_key_action.setChecked(data.get('key_action_enabled', False))
        self.chk_key_action.blockSignals(False)
        
        # Hide nav panel for X and Z columns
        if c >= COLS:
            self.nav_panel.hide()
        else:
            self.nav_panel.show()
            if self.cell_data_ref:
                self.nav_panel.update_nav(r, c, self.cell_data_ref)

    def refresh_navigation(self):
        if self.cell_data_ref:
            self.nav_panel.update_nav(self.r, self.c, self.cell_data_ref)

    def on_back_clicked(self):
        self.back_signal.emit()

    def on_navigate(self, r, c):
        if (r, c) in self.cell_data_ref:
            self.show_cell(r, c, self.cell_data_ref[(r, c)])
            self.cell_changed_signal.emit(r, c)

    def on_desc_changed(self):
        val = self.txt_desc.toHtml()
        self.data['description_text'] = val
        self.data_changed_signal.emit(self.r, self.c, 'description_text', val)

    def on_signal_changed(self):
        val = self.input_signal.toHtml() # Save as HTML now
        self.data['signal_text'] = val
        self.data_changed_signal.emit(self.r, self.c, 'signal_text', val)

    def on_key_action_changed(self, state):
        val = bool(state)
        self.data['key_action_enabled'] = val
        self.data_changed_signal.emit(self.r, self.c, 'key_action_enabled', val)

    def on_play_click(self):
        if self.data.get('key_action_enabled', False):
            reply = QMessageBox.question(self, "Подтверждение", 
                                         "Игроки выполнили ключевое событие?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self._resolve_and_play()
        else:
            self._resolve_and_play()

    def _resolve_and_play(self):
        # Check if a custom sound file is set
        custom_sound = self.data.get('custom_sound_path')
        if custom_sound and os.path.exists(custom_sound):
            self.play_sound_path(custom_sound)
            return

        signal_text = self.input_signal.toPlainText().strip() # Use plain text for filename
        room_type = self.data.get('room_type', '')
        
        sound_path = None
        
        path = os.path.join(BASE_ROOM_SOUNDS_DIR, f"{signal_text}.wav")
        if os.path.exists(path): sound_path = path
        
        if not sound_path:
            path = os.path.join(AUDIO_PANEL_SOUNDS_DIR, f"{signal_text}.wav")
            if os.path.exists(path): sound_path = path
            
        if not sound_path:
            filename = "NoAudio.wav"
            if room_type == 'Белая зала': filename = "WhiteRoomSound.wav"
            elif room_type == 'Транспортная зала': filename = "TransportRoomSound.wav"
            elif room_type == 'Зала внутреннего контура': filename = "OuterRoomSound.wav"
            
            path = os.path.join(BASE_ROOM_SOUNDS_DIR, filename)
            if os.path.exists(path): sound_path = path
            else:
                path = os.path.join(AUDIO_PANEL_SOUNDS_DIR, filename)
                if os.path.exists(path): sound_path = path
                
        if sound_path:
            self.play_sound_path(sound_path)
        else:
            print(f"Sound not found for: {signal_text}")

    def play_sound_file(self, filename):
        path = os.path.join(AUDIO_PANEL_SOUNDS_DIR, filename)
        if os.path.exists(path):
            self.play_sound_path(path)

    def play_sound_path(self, path):
        from PyQt6.QtWidgets import QApplication
        main_window = QApplication.instance().activeWindow()
        if hasattr(main_window, 'play_sound'):
            main_window.play_sound(path)

    def on_play_context_menu(self, pos):
        menu = QMenu(self)
        action_select = menu.addAction("Выбрать звуковой сигнал...")
        action_clear = menu.addAction("Очистить звуковой сигнал")
        
        # Check if custom sound is set
        if not self.data.get('custom_sound_path'):
            action_clear.setEnabled(False)
        
        action = menu.exec(self.btn_play.mapToGlobal(pos))
        
        if action == action_select:
            file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Audio (*.wav *.mp3)")
            if file_path:
                # Save the full path to the data dictionary
                self.data['custom_sound_path'] = file_path
                self.data_changed_signal.emit(self.r, self.c, 'custom_sound_path', file_path)
                QMessageBox.information(self, "Успех", f"Звуковой файл привязан: {os.path.basename(file_path)}")
        elif action == action_clear:
            if 'custom_sound_path' in self.data:
                del self.data['custom_sound_path']
                self.data_changed_signal.emit(self.r, self.c, 'custom_sound_path', None)
                QMessageBox.information(self, "Успех", "Привязка звукового файла удалена")

    def open_edit_dialog(self):
        dialog = EditCellDialog(self.data, coords=(self.r, self.c), parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.data_changed_signal.emit(self.r, self.c, '__all__', new_data)
            
            # Update local view
            self.show_cell(self.r, self.c, new_data)
