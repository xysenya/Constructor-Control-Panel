import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, 
                             QLayout, QSizePolicy, QGroupBox, QPushButton, QDialog, QApplication, 
                             QLineEdit, QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QTextEdit, QSplitter, QMessageBox)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon, QImage, QIntValidator
from config import FONT_FAMILY_BOLD, SCRIPT_DIR, PLAYER_BUTTONS_DIR

ITEMS_BASE_DIR = os.path.join(SCRIPT_DIR, "Items")
BLOCK_NAMES = [
    "ПРЕДМЕТЫ", 
    "ВЕЛИКИЕ ПРЕДМЕТЫ", 
    "ПРЕДМЕТЫ УРОВНЯ", 
    "СТИМУЛЯТОРЫ", 
    "КЛЮЧИ", 
    "КОМПАСЫ", 
    "СПОСОБНОСТИ РЫЦАРЕЙ"
]
ITEM_WIDTH = 200
ITEM_HEIGHT = 275

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=10, spacing=10):
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

class ImageViewerDialog(QDialog):
    def __init__(self, pixmap, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        
        layout = QVBoxLayout(self)
        
        self.image_label = QLabel()
        self.image_label.setPixmap(pixmap)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.image_label)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(scroll_area)
        
        self.resize(pixmap.width() + 40, pixmap.height() + 40)

class ItemListDialog(QDialog):
    def __init__(self, given_items, saved_state, forced_checked, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список предметов")
        self.resize(900, 600)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        self.given_items = given_items
        self.saved_state = saved_state
        self.forced_checked = forced_checked
        
        main_layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Предметы")
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #333;
                border: 1px solid #555;
                color: white;
            }
            QTreeWidget::item:hover {
                background-color: #444;
            }
        """)
        self.tree.itemChanged.connect(self.on_item_changed)
        splitter.addWidget(self.tree)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                border: 1px solid #555;
                color: white;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 14px;
                padding: 10px;
            }
        """)
        splitter.addWidget(self.text_edit)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(splitter)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setFixedSize(120, 40)
        self.btn_save.setStyleSheet("background-color: #4472c4; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_save.clicked.connect(self.accept)
        
        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.setFixedSize(120, 40)
        self.btn_cancel.setStyleSheet("background-color: #555; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        
        main_layout.addLayout(btn_layout)
        
        self.populate_tree()
        self.update_text()

    def populate_tree(self):
        self.tree.blockSignals(True)
        for block_name in BLOCK_NAMES:
            if block_name == "СПОСОБНОСТИ РЫЦАРЕЙ":
                continue
                
            parent_item = QTreeWidgetItem(self.tree)
            parent_item.setText(0, block_name)
            
            if block_name in self.saved_state:
                parent_item.setCheckState(0, self.saved_state[block_name])
            else:
                if block_name == "ПРЕДМЕТЫ":
                    parent_item.setCheckState(0, Qt.CheckState.Checked)
                else:
                    parent_item.setCheckState(0, Qt.CheckState.Unchecked)
                
            parent_item.setExpanded(True)
            
            folder_path = os.path.join(ITEMS_BASE_DIR, block_name)
            if os.path.isdir(folder_path):
                for filename in sorted(os.listdir(folder_path)):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        name_no_ext = os.path.splitext(filename)[0]
                        child_item = QTreeWidgetItem(parent_item)
                        
                        if name_no_ext in self.given_items:
                            child_item.setText(0, f"{name_no_ext} (УЖЕ ВЫДАНО)")
                            font = child_item.font(0)
                            font.setBold(True)
                            child_item.setFont(0, font)
                            
                            if name_no_ext in self.forced_checked:
                                child_item.setCheckState(0, Qt.CheckState.Checked)
                            else:
                                child_item.setCheckState(0, Qt.CheckState.Unchecked)
                        else:
                            child_item.setText(0, name_no_ext)
                            
                            if name_no_ext in self.saved_state:
                                child_item.setCheckState(0, self.saved_state[name_no_ext])
                            else:
                                if block_name == "ПРЕДМЕТЫ":
                                    child_item.setCheckState(0, Qt.CheckState.Checked)
                                else:
                                    child_item.setCheckState(0, Qt.CheckState.Unchecked)
                            
        self.tree.blockSignals(False)

    def on_item_changed(self, item, column):
        self.tree.blockSignals(True)
        if item.childCount() > 0:
            state = item.checkState(column)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(column, state)
        
        self.tree.blockSignals(False)
        self.update_text()

    def update_text(self):
        lines = []
        counter = 1
        
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.CheckState.Checked:
                    text = child.text(0).replace(" (УЖЕ ВЫДАНО)", "")
                    lines.append(f"{counter}. {text}")
                    counter += 1
                    
        self.text_edit.setPlainText("\n".join(lines))

    def get_state(self):
        state = {}
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            state[parent.text(0)] = parent.checkState(0)
            
            for j in range(parent.childCount()):
                child = parent.child(j)
                clean_name = child.text(0).replace(" (УЖЕ ВЫДАНО)", "")
                state[clean_name] = child.checkState(0)
        return state

class ItemWidget(QFrame):
    state_changed = pyqtSignal(str, str, bool)

    def __init__(self, image_path, block_name, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.block_name = block_name
        self.pixmap = QPixmap(image_path)
        
        self.base_width = ITEM_WIDTH
        self.base_height = ITEM_HEIGHT
        self.scale_factor = 1.0
        
        self.default_style = """
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 5px;
            }
        """
        self.given_style = """
            QFrame {
                background-color: #1e4d2b;
                border: 2px solid #2e7d32;
                border-radius: 5px;
            }
        """
        
        self.setStyleSheet(self.default_style)
        
        self.init_ui()
        self.update_size()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        self.image_label = QLabel()
        self.image_label.setStyleSheet("border: none; background: transparent;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.mousePressEvent = self.show_full_image
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        filename = os.path.splitext(os.path.basename(self.image_path))[0]
        name_label = QLabel(filename)
        name_label.setStyleSheet("color: #ccc; border: none; background: transparent;")
        name_label.setWordWrap(True)
        
        copy_button = QPushButton()
        copy_icon_path = os.path.join(PLAYER_BUTTONS_DIR, "copy.png")
        if os.path.exists(copy_icon_path):
            copy_button.setIcon(QIcon(copy_icon_path))
        copy_button.setFixedSize(24, 24)
        copy_button.setIconSize(QSize(20, 20))
        copy_button.setStyleSheet("border: none; background: transparent;")
        copy_button.setToolTip("Копировать изображение в буфер обмена")
        copy_button.clicked.connect(self.copy_image_to_clipboard)

        self.chk_given = QCheckBox()
        self.chk_given.setFixedSize(24, 24)
        self.chk_given.setToolTip("Выдано игрокам")
        self.chk_given.setStyleSheet("""
            QCheckBox::indicator { width: 18px; height: 18px; }
            QCheckBox { background: transparent; border: none; }
        """)
        self.chk_given.toggled.connect(self.on_given_toggled)

        bottom_layout.addWidget(name_label, 1)
        bottom_layout.addWidget(copy_button)
        bottom_layout.addWidget(self.chk_given)
        
        main_layout.addWidget(self.image_label, 1)
        main_layout.addLayout(bottom_layout)

    def update_size(self):
        new_width = int(self.base_width * self.scale_factor)
        new_height = int(self.base_height * self.scale_factor)
        self.setFixedSize(new_width, new_height)
        
        if hasattr(self, 'image_label'):
             w = new_width - 10
             h = new_height - 50
             if w > 0 and h > 0:
                 scaled_pixmap = self.pixmap.scaled(
                    w, h,
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                 self.image_label.setPixmap(scaled_pixmap)

    def show_full_image(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            dialog = ImageViewerDialog(self.pixmap, os.path.basename(self.image_path), self)
            dialog.exec()

    def copy_image_to_clipboard(self):
        clipboard = QApplication.clipboard()
        image = QImage(self.image_path)
        clipboard.setImage(image)
        print(f"Copied to clipboard: {self.image_path}")

    def on_given_toggled(self, checked):
        filename = os.path.splitext(os.path.basename(self.image_path))[0]
        
        if checked:
            self.setStyleSheet(self.given_style)
        else:
            self.setStyleSheet(self.default_style)
            
        self.state_changed.emit(self.block_name, filename, checked)

    def set_given(self, checked):
        self.chk_given.blockSignals(True)
        self.chk_given.setChecked(checked)
        if checked:
            self.setStyleSheet(self.given_style)
        else:
            self.setStyleSheet(self.default_style)
        self.chk_given.blockSignals(False)

class ItemPlaceholder(QFrame):
    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.base_width = ITEM_WIDTH
        self.base_height = ITEM_HEIGHT
        self.scale_factor = 1.0
        
        self.setStyleSheet("""
            QFrame {
                background-color: #333333;
                border: 2px dashed #555555;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        label = QLabel(f"Предмет {index}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #777; border: none; background: transparent;")
        layout.addWidget(label)
        
        self.update_size()

    def update_size(self):
        self.setFixedSize(int(self.base_width * self.scale_factor), int(self.base_height * self.scale_factor))

class ItemsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scale_factor = 0.90
        self.all_item_widgets = []
        self.flow_layouts = []
        self.block_groups = {}
        self.given_items = set()
        self.list_dialog_state = {}
        self.forced_checked = set()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        for block_name in BLOCK_NAMES:
            group = QGroupBox(block_name)
            group.setFont(QFont(FONT_FAMILY_BOLD, 14))
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #555;
                    border-radius: 5px;
                    margin-top: 1em;
                    font-weight: bold;
                    color: #ddd;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            
            group_layout = FlowLayout(margin=15, spacing=15)
            self.flow_layouts.append(group_layout)
            
            folder_path = os.path.join(ITEMS_BASE_DIR, block_name)
            items_found = 0
            if os.path.isdir(folder_path):
                for filename in sorted(os.listdir(folder_path)):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        full_path = os.path.join(folder_path, filename)
                        item_widget = ItemWidget(full_path, block_name)
                        item_widget.state_changed.connect(self.on_item_state_changed)
                        group_layout.addWidget(item_widget)
                        self.all_item_widgets.append(item_widget)
                        items_found += 1
            
            if items_found == 0:
                for i in range(1, 5):
                    item = ItemPlaceholder(i)
                    group_layout.addWidget(item)
                    self.all_item_widgets.append(item)

            group.setLayout(group_layout)
            content_layout.addWidget(group)
            self.block_groups[block_name] = group
            
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 5, 10, 5)
        
        self.combo_filter = QComboBox()
        self.combo_filter.setMinimumWidth(200)
        self.combo_filter.addItem("Показать все")
        self.combo_filter.addItems(BLOCK_NAMES)
        self.combo_filter.currentIndexChanged.connect(self.apply_filter)
        bottom_layout.addWidget(self.combo_filter)
        
        self.btn_list = QPushButton()
        self.btn_list.setFixedSize(30, 30)
        list_icon_path = os.path.join(PLAYER_BUTTONS_DIR, "List.png")
        if os.path.exists(list_icon_path):
            self.btn_list.setIcon(QIcon(list_icon_path))
        self.btn_list.setIconSize(QSize(24, 24))
        self.btn_list.setToolTip("Открыть список предметов")
        self.btn_list.clicked.connect(self.open_list_dialog)
        bottom_layout.addWidget(self.btn_list)
        
        self.btn_copy_list = QPushButton()
        self.btn_copy_list.setFixedSize(30, 30)
        copylist_icon_path = os.path.join(PLAYER_BUTTONS_DIR, "copylist.png")
        if os.path.exists(copylist_icon_path):
            self.btn_copy_list.setIcon(QIcon(copylist_icon_path))
        self.btn_copy_list.setIconSize(QSize(24, 24))
        self.btn_copy_list.setToolTip("Копировать полный список предметов")
        self.btn_copy_list.clicked.connect(self.copy_full_list)
        bottom_layout.addWidget(self.btn_copy_list)
        
        bottom_layout.addStretch()
        
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        
        self.lbl_zoom = QLineEdit("95%")
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
        
        self.update_zoom()

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
        for widget in self.all_item_widgets:
            widget.scale_factor = self.scale_factor
            widget.update_size()
        
        for layout in self.flow_layouts:
            layout.invalidate()

    def apply_filter(self, index):
        selected_text = self.combo_filter.currentText()
        
        if selected_text == "Показать все":
            for group in self.block_groups.values():
                group.show()
        else:
            for name, group in self.block_groups.items():
                if name == selected_text:
                    group.show()
                else:
                    group.hide()

    def on_item_state_changed(self, block_name, name, is_checked):
        if is_checked:
            self.given_items.add(name)
        else:
            self.given_items.discard(name)
            self.forced_checked.discard(name)
            
            if block_name != "СПОСОБНОСТИ РЫЦАРЕЙ":
                was_checked_in_list = False
                if name in self.list_dialog_state:
                    was_checked_in_list = (self.list_dialog_state[name] == Qt.CheckState.Checked)
                else:
                    if block_name == "ПРЕДМЕТЫ":
                        was_checked_in_list = True
                
                if was_checked_in_list:
                    reply = QMessageBox.question(self, "Подтверждение", 
                                                 "Вернуть предмет в список для голосования?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    if reply == QMessageBox.StandardButton.Yes:
                        self.forced_checked.add(name)
                        self.list_dialog_state[name] = Qt.CheckState.Checked

    def open_list_dialog(self):
        dialog = ItemListDialog(self.given_items, self.list_dialog_state, self.forced_checked, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.list_dialog_state = dialog.get_state()
            
            for name, state in self.list_dialog_state.items():
                if name in self.given_items:
                    if state == Qt.CheckState.Checked:
                        self.forced_checked.add(name)
                    else:
                        self.forced_checked.discard(name)

    def copy_full_list(self):
        lines = []
        counter = 1
        for block_name in BLOCK_NAMES:
            if block_name == "СПОСОБНОСТИ РЫЦАРЕЙ":
                continue
            folder_path = os.path.join(ITEMS_BASE_DIR, block_name)
            if os.path.isdir(folder_path):
                for filename in sorted(os.listdir(folder_path)):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                        name_no_ext = os.path.splitext(filename)[0]
                        
                        is_checked = False
                        
                        if name_no_ext in self.given_items:
                            if name_no_ext in self.forced_checked:
                                is_checked = True
                            else:
                                is_checked = False
                        else:
                            if name_no_ext in self.list_dialog_state:
                                is_checked = (self.list_dialog_state[name_no_ext] == Qt.CheckState.Checked)
                            else:
                                if block_name == "ПРЕДМЕТЫ":
                                    is_checked = True
                                else:
                                    is_checked = False
                        
                        if is_checked:
                            lines.append(f"{counter}. {name_no_ext}")
                            counter += 1
        
        text = "\n".join(lines)
        QApplication.clipboard().setText(text)

    def get_data(self):
        return {
            'given_items': list(self.given_items),
            'list_dialog_state': {k: v.value for k, v in self.list_dialog_state.items()},
            'forced_checked': list(self.forced_checked)
        }

    def set_data(self, data):
        if not data: return
        self.given_items = set(data.get('given_items', []))
        
        # Restore list dialog state
        raw_state = data.get('list_dialog_state', {})
        self.list_dialog_state = {}
        for k, v in raw_state.items():
            # Convert int back to CheckState enum
            self.list_dialog_state[k] = Qt.CheckState(v)
            
        self.forced_checked = set(data.get('forced_checked', []))
        
        # Update UI widgets
        for widget in self.all_item_widgets:
            if isinstance(widget, ItemWidget):
                filename = os.path.splitext(os.path.basename(widget.image_path))[0]
                if filename in self.given_items:
                    widget.set_given(True)
                else:
                    widget.set_given(False)
