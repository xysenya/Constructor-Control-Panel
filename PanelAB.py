from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem, 
                             QGraphicsItem, QMenu, QDialog, QWidget, QVBoxLayout, QPushButton, 
                             QStackedLayout, QInputDialog, QGraphicsSimpleTextItem, QTabWidget, QApplication, QStyleOptionGraphicsItem,
                             QHBoxLayout, QLineEdit, QTextEdit, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPoint, QPointF, QMimeData, QByteArray, QDataStream, QIODevice, QUrl, QEvent
from PyQt6.QtGui import QColor, QBrush, QPen, QFont, QPainter, QCursor, QDrag, QPixmap, QFontMetrics
import config
from map_view import get_cell_layout
from utils import get_font_name, get_fitted_font_size
from editor_window import EditCellDialog
from detailed_view import DetailedView
from Chars import PlayersTab
from OrangeTab import OrangeTab
from ItemsTab import ItemsTab
from PurpleTab import PurpleTab
from text_formatting import RichTextEditor, FormattingToolbar
import os

class LoreTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_story_text = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.combo_lore = QComboBox()
        self.items = [
            "Текущий сюжет", 
            "Глобальный сюжет", 
            "Уровни конструктора", 
            "Послания из других сигнатур"
        ]
        self.combo_lore.addItems(self.items)
        self.combo_lore.setStyleSheet("""
            QComboBox {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                font-size: 14px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.combo_lore.currentTextChanged.connect(self.on_selection_change)
        layout.addWidget(self.combo_lore)
        
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
        self.text_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.text_edit)
        
        self.formatting_toolbar = FormattingToolbar()
        self.formatting_toolbar.set_editor(self.text_edit)
        self.formatting_toolbar.hide()
        layout.addWidget(self.formatting_toolbar)
        
        self.on_selection_change(self.combo_lore.currentText())

    def on_selection_change(self, title):
        if title == "Текущий сюжет":
            self.text_edit.setReadOnly(False)
            self.text_edit.setHtml(self.current_story_text)
        else:
            is_edit_mode = self.formatting_toolbar.isVisible()
            self.text_edit.setReadOnly(not is_edit_mode)
            self.load_text_from_file(title, as_html=True)

    def load_text_from_file(self, title, as_html=False):
        filename = f"{title}.txt"
        path = os.path.join(config.LORE_DIR, filename)
        
        if as_html:
             html_path = os.path.join(config.LORE_DIR, f"{title}.html")
             if os.path.exists(html_path):
                 path = html_path
        
        if os.path.exists(path):
            content = None
            error_msg = ""
            
            encodings = ['utf-8', 'utf-16', 'cp1251']
            for enc in encodings:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        content = f.read()
                    break
                except Exception as e:
                    error_msg = str(e)
            
            if content is not None:
                self.text_edit.blockSignals(True)
                if path.endswith('.html'):
                    base_url = QUrl.fromLocalFile(config.LORE_DIR + os.sep)
                    self.text_edit.document().setBaseUrl(base_url)
                    self.text_edit.setHtml(content)
                else:
                    self.text_edit.setPlainText(content)
                self.text_edit.blockSignals(False)
            else:
                self.text_edit.setText(f"Ошибка чтения файла (пробовали {encodings}): {error_msg}")
        else:
            self.text_edit.setText(f"Файл не найден: {filename}")
            
    def on_text_changed(self):
        if self.combo_lore.currentText() == "Текущий сюжет":
            self.current_story_text = self.text_edit.toHtml()

    def set_edit_mode(self, enabled):
        current_title = self.combo_lore.currentText()
        if current_title == "Текущий сюжет":
            self.text_edit.setReadOnly(False)
        else:
            self.text_edit.setReadOnly(not enabled)
            
        if enabled:
            self.formatting_toolbar.show()
        else:
            self.formatting_toolbar.hide()

    def get_data(self):
        return {
            'current_story_text': self.current_story_text
        }

    def set_data(self, data):
        if not data: return
        self.current_story_text = data.get('current_story_text', '')
        if self.combo_lore.currentText() == "Текущий сюжет":
            self.text_edit.setHtml(self.current_story_text)

class MapCellItem(QGraphicsRectItem):
    def __init__(self, r, c, x, y, w, h, data, parent_view):
        super().__init__(float(x), float(y), float(w), float(h))
        self.r = r
        self.c = c
        self.data = data
        self.parent_view = parent_view
        
        self.setAcceptHoverEvents(True)
        
        self.is_hovered = False
        self.is_active = False 
        self.is_remote_active = False 
        self.is_drop_target = False
        self._drag_started = False
        self._drag_start_pos = QPoint()

    def set_active(self, active):
        self.is_active = active
        self.update()

    def set_remote_active(self, active):
        self.is_remote_active = active
        self.update()

    def set_drop_target(self, active):
        self.is_drop_target = active
        self.update()

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget=None):
        color_str = self.data.get('color', '#CCCCCC')
        if not isinstance(color_str, str) or not color_str.startswith('#'):
            color_str = '#CCCCCC'
        color = QColor(color_str)
        painter.setBrush(QBrush(color))

        pen_width = 0
        if self.is_drop_target:
            pen = QPen(QColor(0, 255, 0), 4)
            pen_width = 4
            painter.setPen(pen)
        elif self.is_remote_active or self.is_active:
            pen = QPen(QColor(*config.REMOTE_HIGHLIGHT_COLOR), 4)
            pen_width = 4
            painter.setPen(pen)
        elif self.is_hovered:
            pen = QPen(QColor(*config.HIGHLIGHT_COLOR), 3)
            pen_width = 3
            painter.setPen(pen)
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        rect = self.rect()
        if pen_width > 0:
            inset = pen_width / 2.0
            rect = rect.adjusted(inset, inset, -inset, -inset)
            
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawRoundedRect(rect, config.CELL_RADIUS, config.CELL_RADIUS)

        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        content_rect = self.rect()
        
        num_text = str(self.data.get('number', '0000'))
        if self.data.get('room_type') == 'Сгенерированная зала':
            num_text = f"-{num_text}-"
        
        name_text = str(self.data.get('name', '')).strip()
        has_name = bool(name_text)
        room_type = self.data.get('room_type', '')
        is_inner_contour = room_type == 'Зала внутреннего контура'

        font_size_num = int(self.data.get('font_size_num', 12))
        is_bold_num = self.data.get('font_weight_num') == 'bold'
        num_font = QFont(get_font_name(is_bold_num), font_size_num)
        painter.setFont(num_font)
        painter.setPen(QColor(self.data.get('text_color', '#000000')))

        if is_inner_contour or not has_name:
            painter.drawText(content_rect, Qt.AlignmentFlag.AlignCenter, num_text)
        else:
            num_rect = QRectF(content_rect.x(), content_rect.y() + content_rect.height() * 0.05, content_rect.width(), content_rect.height() * 0.30)
            painter.drawText(num_rect, Qt.AlignmentFlag.AlignCenter, num_text)
            
            initial_font_size_name = int(self.data.get('font_size_name', 10))
            is_bold_name = self.data.get('font_weight_name') == 'bold'
            
            fitted_font_size = get_fitted_font_size(name_text, is_bold_name, initial_font_size_name, rect.width() * 0.95)
            
            name_font = QFont(get_font_name(is_bold_name), fitted_font_size)
            painter.setFont(name_font)
            painter.setPen(QColor(self.data.get('text_color_name', '#000000')))
            
            formatted_name = name_text.replace(' ', '\n')
            
            name_rect = QRectF(content_rect.x() + 5, content_rect.y() + content_rect.height() * 0.35, content_rect.width() - 10, content_rect.height() * 0.65)
            painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, formatted_name)

    def update_visuals(self):
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.screenPos()
            self._drag_started = False
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.parent_view.on_cell_right_clicked(self.r, self.c)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if not self._drag_started:
            if (event.screenPos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
                return
            self._drag_started = True

        drag = QDrag(self.parent_view)
        mime_data = QMimeData()
        
        item_data = QByteArray()
        data_stream = QDataStream(item_data, QIODevice.OpenModeFlag.WriteOnly)
        data_stream.writeInt(self.r)
        data_stream.writeInt(self.c)
        mime_data.setData("application/x-map-cell", item_data)
        
        drag.setMimeData(mime_data)
        
        transform = self.parent_view.transform()
        scale_x = transform.m11()
        scale_y = transform.m22()
        
        base_size = self.boundingRect().size()
        scaled_size = base_size.toSize()
        scaled_size.setWidth(int(base_size.width() * scale_x))
        scaled_size.setHeight(int(base_size.height() * scale_y))
        
        pixmap = QPixmap(scaled_size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.scale(scale_x, scale_y)
        
        rect = self.rect()
        painter.translate(-rect.x(), -rect.y())
        
        option = QStyleOptionGraphicsItem()
        self.paint(painter, option, None)
        painter.end()
        
        ghost = QPixmap(pixmap.size())
        ghost.fill(Qt.GlobalColor.transparent)
        p = QPainter(ghost)
        p.setOpacity(0.7)
        p.drawPixmap(0, 0, pixmap)
        p.end()
        
        drag.setPixmap(ghost)
        
        hot_spot = event.pos() - rect.topLeft()
        hot_spot_x = int(hot_spot.x() * scale_x)
        hot_spot_y = int(hot_spot.y() * scale_y)
        drag.setHotSpot(QPoint(hot_spot_x, hot_spot_y))
        
        drag.exec(Qt.DropAction.MoveAction)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._drag_started:
                self.parent_view.on_cell_clicked(self.r, self.c)
            self._drag_started = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

class TitleItem(QGraphicsTextItem):
    def __init__(self, text_ref, parent_view):
        super().__init__(text_ref[0])
        self.text_ref = text_ref
        self.parent_view = parent_view
        
        font = QFont(config.FONT_FAMILY_BOLD, config.BASE_FONT_SIZE_TITLE)
        self.setFont(font)
        self.setDefaultTextColor(QColor("white"))
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.parent_view.edit_title()
            event.accept()
        else:
            super().mousePressEvent(event)
            
    def update_text(self):
        self.setPlainText(self.text_ref[0])

class MapGraphicsView(QGraphicsView):
    cell_clicked = pyqtSignal(int, int)
    cell_data_changed = pyqtSignal(int, int, dict)
    zoom_changed = pyqtSignal(float)
    
    def __init__(self, cell_data, campaign_title_ref, parent=None):
        super().__init__(parent)
        self.cell_data = cell_data
        self.campaign_title_ref = campaign_title_ref
        
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setBackgroundBrush(QBrush(QColor(50, 50, 50)))
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setAcceptDrops(True)
        
        self._panning = False
        self._pan_start_pos = QPoint()
        self._last_drop_target = None
        
        self.cell_items = {}
        self.active_cell = None
        self.remote_active_cell = None
        self.cell_layout = get_cell_layout()
        self.title_item = None
        
        self._create_grid()
        self._create_labels()
        self._create_title()
        self._add_scene_padding()
        
        if not self.scene.sceneRect().isEmpty():
             self.centerOn(self.scene.sceneRect().center())

    def showEvent(self, event):
        super().showEvent(event)
        if not event.spontaneous():
            self.zoom_changed.emit(self.transform().m11())

    def _create_grid(self):
        if not self.cell_layout:
            return

        max_y = max(pos[1] + pos[3] for pos in self.cell_layout.values())
        
        for (r, c), (x, y, w, h) in self.cell_layout.items():
            qt_y = max_y - (y + h)
            if (r, c) in self.cell_data:
                item = MapCellItem(r, c, x, qt_y, w, h, self.cell_data[(r, c)], self)
                self.scene.addItem(item)
                self.cell_items[(r, c)] = item

    def _create_labels(self):
        if not self.cell_items: return
        
        font = QFont(config.FONT_FAMILY_BOLD, config.BASE_FONT_SIZE_COORDS)
        
        min_y = min(item.rect().y() for item in self.cell_items.values())
        min_x = min(item.rect().x() for item in self.cell_items.values())
        
        for c in range(config.COLS + config.EXTRA_COLS):
            cell_in_col = None
            max_r = -1
            for r in range(config.ROWS + config.EXTRA_ROWS_TOP + 1):
                if (r, c) in self.cell_items:
                    max_r = max(max_r, r)
            
            if max_r != -1:
                cell_in_col = self.cell_items[(max_r, c)]
                
                x = cell_in_col.rect().x() + cell_in_col.rect().width() / 2
                y = cell_in_col.rect().y() - 20
                
                label_text = ""
                if c < config.COLS:
                    label_text = chr(ord('A') + c)
                elif c == config.COLS:
                    label_text = "X"
                elif c == config.COLS + 1:
                    label_text = "Z"
                
                if label_text:
                    text_item = QGraphicsSimpleTextItem(label_text)
                    text_item.setFont(font)
                    text_item.setBrush(QBrush(QColor("white")))
                    text_item.setZValue(100)
                    
                    bound = text_item.boundingRect()
                    text_item.setPos(x - bound.width() / 2, y - bound.height())
                    self.scene.addItem(text_item)

        for r in range(config.ROWS):
            cell_in_row = None
            for c in range(config.COLS):
                if (r, c) in self.cell_items:
                    cell_in_row = self.cell_items[(r, c)]
                    break
            
            if cell_in_row:
                y = cell_in_row.rect().y() + cell_in_row.rect().height() / 2
                x = min_x - 50
                
                label_text = str(config.ROWS - r)
                
                text_item = QGraphicsSimpleTextItem(label_text)
                text_item.setFont(font)
                text_item.setBrush(QBrush(QColor("white")))
                text_item.setZValue(100)
                
                bound = text_item.boundingRect()
                text_item.setPos(x - bound.width(), y - bound.height() / 2)
                self.scene.addItem(text_item)
                
        for r in range(config.EXTRA_ROWS_TOP + 1):
            cell_in_row = None
            for c in range(config.COLS, config.COLS + config.EXTRA_COLS):
                if (r, c) in self.cell_items:
                    cell_in_row = self.cell_items[(r, c)]
                    break
            
            if cell_in_row:
                y = cell_in_row.rect().y() + cell_in_row.rect().height() / 2
                x = cell_in_row.rect().x() - 20
                
                label_text = str(6 - r)
                
                text_item = QGraphicsSimpleTextItem(label_text)
                text_item.setFont(font)
                text_item.setBrush(QBrush(QColor("white")))
                text_item.setZValue(100)
                
                bound = text_item.boundingRect()
                text_item.setPos(x - bound.width(), y - bound.height() / 2)
                self.scene.addItem(text_item)

    def _create_title(self):
        if not self.cell_items: return
        min_y = min(item.rect().y() for item in self.cell_items.values())
        min_x = min(item.rect().x() for item in self.cell_items.values())
        
        self.title_item = TitleItem(self.campaign_title_ref, self)
        self.title_item.setPos(min_x, min_y - 150)
        self.scene.addItem(self.title_item)

    def _add_scene_padding(self):
        rect = self.scene.itemsBoundingRect()
        padding = 1000
        rect.adjust(-padding, -padding, padding, padding)
        self.scene.setSceneRect(rect)

    def edit_title(self):
        text, ok = QInputDialog.getText(self, "Название похода", "Введите название:", text=self.campaign_title_ref[0])
        if ok:
            self.campaign_title_ref[0] = text
            self.title_item.update_text()

    def on_cell_clicked(self, r, c):
        if self.active_cell:
            if self.active_cell in self.cell_items:
                self.cell_items[self.active_cell].set_active(False)
        
        self.active_cell = (r, c)
        if (r, c) in self.cell_items:
            self.cell_items[(r, c)].set_active(True)
            
        self.cell_clicked.emit(r, c)

    def set_remote_highlight(self, r, c):
        if self.remote_active_cell:
            if self.remote_active_cell in self.cell_items:
                self.cell_items[self.remote_active_cell].set_remote_active(False)
        
        self.remote_active_cell = (r, c)
        if (r, c) in self.cell_items:
            self.cell_items[(r, c)].set_remote_active(True)

    def on_cell_right_clicked(self, r, c):
        menu = QMenu(self)
        edit_action = menu.addAction("Настроить залу...")
        action = menu.exec(QCursor.pos())
        if action == edit_action:
            self.open_edit_dialog(r, c)

    def open_edit_dialog(self, r, c):
        if (r, c) not in self.cell_data:
            return
        dialog = EditCellDialog(self.cell_data[(r, c)], coords=(r, c), parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.cell_data[(r, c)].update(new_data)
            self.update_visuals(r, c)
            self.cell_data_changed.emit(r, c, new_data)

    def update_visuals(self, r, c):
        if (r, c) in self.cell_items:
            self.cell_items[(r, c)].data = self.cell_data[(r, c)]
            self.cell_items[(r, c)].update_visuals()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-map-cell"):
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-map-cell"):
            event.accept()
            
            pos = self.mapToScene(event.position().toPoint())
            item = self.scene.itemAt(pos, self.transform())
            
            target_cell = None
            if isinstance(item, MapCellItem):
                target_cell = item
            
            if self._last_drop_target and self._last_drop_target != target_cell:
                self._last_drop_target.set_drop_target(False)
            
            if target_cell:
                target_cell.set_drop_target(True)
                self._last_drop_target = target_cell
            else:
                self._last_drop_target = None
        else:
            event.ignore()
            
    def dragLeaveEvent(self, event):
        if self._last_drop_target:
            self._last_drop_target.set_drop_target(False)
            self._last_drop_target = None
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        if self._last_drop_target:
            self._last_drop_target.set_drop_target(False)
            
        if event.mimeData().hasFormat("application/x-map-cell"):
            item_data = event.mimeData().data("application/x-map-cell")
            data_stream = QDataStream(item_data, QIODevice.OpenModeFlag.ReadOnly)
            r1 = data_stream.readInt()
            c1 = data_stream.readInt()
            
            if self._last_drop_target:
                r2, c2 = self._last_drop_target.r, self._last_drop_target.c
                
                if (r1, c1) != (r2, c2):
                    self.cell_data[(r1, c1)], self.cell_data[(r2, c2)] = self.cell_data[(r2, c2)], self.cell_data[(r1, c1)]
                    
                    self.cell_data_changed.emit(r1, c1, self.cell_data[(r1, c1)])
                    self.cell_data_changed.emit(r2, c2, self.cell_data[(r2, c2)])
            
            self._last_drop_target = None
            event.accept()
        else:
            event.ignore()

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)
        self.zoom_changed.emit(self.transform().m11())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            delta = event.pos() - self._pan_start_pos
            self._pan_start_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
        else:
            super().mouseMoveEvent(event)
            
    def reset_view(self):
        self.resetTransform()
        if self.cell_items:
            content_rect = QRectF()
            for item in self.scene.items():
                content_rect = content_rect.united(item.sceneBoundingRect())
            self.fitInView(content_rect, Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(0.9, 0.9)
            self.centerOn(content_rect.center())
        self.zoom_changed.emit(self.transform().m11())

    def zoom_in(self):
        self.scale(1.15, 1.15)
        self.zoom_changed.emit(self.transform().m11())

    def zoom_out(self):
        self.scale(1 / 1.15, 1 / 1.15)
        self.zoom_changed.emit(self.transform().m11())

class MainPanel(QWidget):
    remote_highlight_signal = pyqtSignal(int, int)
    cell_data_changed = pyqtSignal(int, int, dict)
    
    def __init__(self, cell_data, campaign_title_ref, parent=None):
        super().__init__(parent)
        
        self.orange_tab = None
        self.purple_tab = None
        self.npc_editor = None
        self.notes_editor = None
        self.lore_tab = None
        self.items_tab = None
        self.players_tab = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        
        self.map_tab_widget = QWidget()
        self.map_stack = QStackedLayout(self.map_tab_widget)
        self.map_stack.setStackingMode(QStackedLayout.StackingMode.StackOne)
        
        self.map_container = QWidget()
        map_layout = QVBoxLayout(self.map_container)
        map_layout.setContentsMargins(0, 0, 0, 0)
        
        self.map_view = MapGraphicsView(cell_data, campaign_title_ref)
        self.map_view.cell_clicked.connect(self.show_detailed_view)
        self.map_view.cell_data_changed.connect(self.cell_data_changed)
        map_layout.addWidget(self.map_view)
        
        self.controls_container = QWidget(self.map_container)
        controls_layout = QHBoxLayout(self.controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(5)

        self.btn_reset = QPushButton("Сброс")
        self.btn_reset.setFixedSize(80, 30)
        self.btn_reset.setStyleSheet("""
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
        self.btn_reset.clicked.connect(self.map_view.reset_view)
        controls_layout.addWidget(self.btn_reset)

        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.clicked.connect(self.map_view.zoom_out)
        controls_layout.addWidget(self.btn_zoom_out)

        self.lbl_zoom = QLineEdit("100%")
        self.lbl_zoom.setReadOnly(True)
        self.lbl_zoom.setFixedSize(60, 30)
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.lbl_zoom)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedSize(30, 30)
        self.btn_zoom_in.clicked.connect(self.map_view.zoom_in)
        controls_layout.addWidget(self.btn_zoom_in)

        self.map_view.zoom_changed.connect(self.update_zoom_label)
        
        self.map_stack.addWidget(self.map_container)
        
        self.detailed_view = DetailedView()
        self.detailed_view.back_signal.connect(self.show_map)
        self.detailed_view.cell_changed_signal.connect(self.on_detail_cell_changed)
        self.detailed_view.data_changed_signal.connect(self.on_detail_data_changed)
        self.map_stack.addWidget(self.detailed_view)
        
        self.tabs.addTab(self.map_tab_widget, "Карта Серого уровня")
        
        for name in config.tab_names[1:]:
            if name == "Персонажи игроков":
                self.players_tab = PlayersTab()
                self.tabs.addTab(self.players_tab, name)
            elif name == "Оранжевый уровень":
                self.orange_tab = OrangeTab()
                self.tabs.addTab(self.orange_tab, name)
            elif name == "Предметы":
                self.items_tab = ItemsTab()
                self.tabs.addTab(self.items_tab, name)
            elif name == "Фиолетовый уровень":
                self.purple_tab = PurpleTab()
                self.tabs.addTab(self.purple_tab, name)
            elif name == "Сюжет":
                self.lore_tab = LoreTab()
                self.tabs.addTab(self.lore_tab, name)
            elif name == "NPC":
                self.npc_editor = RichTextEditor()
                self.npc_editor.set_edit_mode(True)
                self.tabs.addTab(self.npc_editor, name)
            elif name == "Заметки":
                self.notes_editor = RichTextEditor()
                self.notes_editor.set_edit_mode(True)
                self.tabs.addTab(self.notes_editor, name)
            else:
                text_edit = QTextEdit()
                text_edit.setStyleSheet("""
                    QTextEdit {
                        background-color: #2b2b2b;
                        color: #a9b7c6;
                        border: 1px solid #3c3f41;
                        font-family: Consolas, 'Courier New', monospace;
                        font-size: 14px;
                        padding: 8px;
                    }
                """)
                self.tabs.addTab(text_edit, name)
            
        layout.addWidget(self.tabs)
        
    def show_detailed_view(self, r, c):
        if (r, c) in self.map_view.cell_data:
            self.detailed_view.show_cell(r, c, self.map_view.cell_data[(r, c)], self.map_view.cell_data)
            self.map_stack.setCurrentIndex(1)
            self.remote_highlight_signal.emit(r, c)
            
    def on_detail_cell_changed(self, r, c):
        if self.map_view.active_cell:
            if self.map_view.active_cell in self.map_view.cell_items:
                self.map_view.cell_items[self.map_view.active_cell].set_active(False)
        self.map_view.active_cell = (r, c)
        if (r, c) in self.map_view.cell_items:
            self.map_view.cell_items[(r, c)].set_active(True)
        self.remote_highlight_signal.emit(r, c)

    def on_detail_data_changed(self, r, c, key, value):
        if key == '__all__':
            update_dict = value
        else:
            update_dict = {key: value}
        self.cell_data_changed.emit(r, c, update_dict)
            
    def show_map(self):
        if self.map_view.active_cell:
            if self.map_view.active_cell in self.map_view.cell_items:
                self.map_view.cell_items[self.map_view.active_cell].set_active(False)
            self.map_view.active_cell = None
            
        self.map_stack.setCurrentIndex(0)
        self.remote_highlight_signal.emit(-1, -1)
        
    def set_remote_highlight(self, r, c):
        self.map_view.set_remote_highlight(r, c)
        
    def update_cell_view(self, r, c):
        self.map_view.update_visuals(r, c)
        if self.map_stack.currentIndex() == 1:
            if self.detailed_view.r == r and self.detailed_view.c == c:
                self.detailed_view.show_cell(r, c, self.map_view.cell_data[(r, c)], self.map_view.cell_data)
            else:
                self.detailed_view.refresh_navigation()
        
    def resizeEvent(self, event):
        if self.map_container.isVisible():
            self.controls_container.adjustSize()
            self.controls_container.move(20, self.map_container.height() - 50)
        super().resizeEvent(event)

    def update_zoom_label(self, zoom):
        self.lbl_zoom.setText(f"{zoom:.0%}")

    def set_edit_mode_grey(self, enabled):
        self.detailed_view.set_edit_mode(enabled)

    def set_edit_mode_npc(self, enabled):
        if self.npc_editor:
            self.npc_editor.set_edit_mode(enabled)

    def set_edit_mode_lore(self, enabled):
        if self.lore_tab:
            self.lore_tab.set_edit_mode(enabled)

    def set_edit_mode_notes(self, enabled):
        if self.notes_editor:
            self.notes_editor.set_edit_mode(enabled)

    def get_data(self):
        data = {
            'npc_text': self.npc_editor.toHtml() if self.npc_editor else "",
            'notes_text': self.notes_editor.toHtml() if self.notes_editor else "",
            'lore_data': self.lore_tab.get_data() if self.lore_tab else {},
            'orange_data': self.orange_tab.get_data() if self.orange_tab else {},
            'purple_data': self.purple_tab.get_data() if self.purple_tab else {},
            'items_data': self.items_tab.get_data() if self.items_tab else {},
            'players_data': self.players_tab.get_data() if self.players_tab else []
        }
        return data

    def set_data(self, data):
        if not data: return
        if self.npc_editor:
            self.npc_editor.setHtml(data.get('npc_text', ''))
        if self.notes_editor:
            self.notes_editor.setHtml(data.get('notes_text', ''))
        if self.lore_tab:
            self.lore_tab.set_data(data.get('lore_data', {}))
        if self.orange_tab:
            self.orange_tab.set_data(data.get('orange_data', {}))
        if self.purple_tab:
            self.purple_tab.set_data(data.get('purple_data', {}))
        if self.items_tab:
            self.items_tab.set_data(data.get('items_data', {}))
        if self.players_tab:
            self.players_tab.set_data(data.get('players_data', []))
