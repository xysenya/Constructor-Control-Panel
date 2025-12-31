from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QScrollArea, QSlider, QFrame, QMenu, QInputDialog, 
                             QStyle, QSizePolicy, QGroupBox, QListWidget, QListWidgetItem, QAbstractItemView, QMessageBox)
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QTime, QRect, QTimer, QPoint
from PyQt6.QtGui import QAction, QFont, QIcon, QCursor, QPainter, QFontMetrics, QColor, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
from config import FONT_FAMILY_REGULAR, FONT_FAMILY_BOLD, PLAYER_BUTTONS_DIR, BASE_MUSIC_DIR

class MarqueeLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.full_text = text
        self.offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scroll_text)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.is_scrolling = False
        self.scroll_speed = 1 # pixels per tick
        self.scroll_delay = 1000 # ms before starting scroll
        self._start_scroll_timer = QTimer(self)
        self._start_scroll_timer.setSingleShot(True)
        self._start_scroll_timer.timeout.connect(lambda: self.timer.start(30)) # Start scrolling after delay

    def setText(self, text):
        self.full_text = text
        self.offset = 0
        self.is_scrolling = False
        self.timer.stop()
        self._start_scroll_timer.stop()
        self.update() # Trigger repaint to re-evaluate scrolling

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.full_text)
        
        # Calculate vertical position to center text
        y = (self.height() + metrics.ascent() - metrics.descent()) // 2
        
        if text_width > self.width():
            if not self.is_scrolling and not self.timer.isActive() and not self._start_scroll_timer.isActive():
                self._start_scroll_timer.start(self.scroll_delay)
            self.is_scrolling = True
            
            # Draw scrolling text using x, y coordinates to avoid clipping by rect width
            painter.drawText(-self.offset, y, self.full_text)
            
            # Draw second copy for seamless loop
            if self.offset > 0: 
                painter.drawText(text_width - self.offset + 20, y, self.full_text)
                
        else:
            if self.is_scrolling: 
                self.is_scrolling = False
                self.timer.stop()
                self._start_scroll_timer.stop()
                self.offset = 0
            
            # Draw normal text (elided if it fits exactly or logic fails, but mostly just draw it)
            # Use drawText with rect for alignment support when not scrolling
            elided = metrics.elidedText(self.full_text, Qt.TextElideMode.ElideRight, self.width())
            painter.drawText(self.rect(), self.alignment(), elided)

    def scroll_text(self):
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self.full_text)
        
        self.offset += self.scroll_speed
        # Reset offset when the first copy has scrolled past the start of the second copy
        if self.offset >= text_width + 20: # 20 is the gap
            self.offset = 0
        self.update()
        
    def resizeEvent(self, event):
        # On resize, re-evaluate if scrolling is needed
        self.offset = 0 # Reset offset
        self.is_scrolling = False # Reset scrolling state
        self.timer.stop()
        self._start_scroll_timer.stop()
        self.update() # Trigger repaint to re-evaluate scrolling
        super().resizeEvent(event)

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.pos().x()) / self.width()
            val = max(self.minimum(), min(self.maximum(), val))
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
            event.accept()
        super().mousePressEvent(event)

class TrackWidget(QWidget):
    play_requested = pyqtSignal() 
    rename_requested = pyqtSignal()
    delete_requested = pyqtSignal()
    slider_moved = pyqtSignal(int) # position
    size_changed = pyqtSignal() # Signal to notify parent about size change

    def __init__(self, index, file_path, is_standard=False, parent=None):
        super().__init__(parent)
        self.index = index
        self.file_path = file_path
        self.display_name = os.path.basename(file_path)
        self.duration = 0
        self.is_playing = False
        self.is_standard = is_standard
        
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)

        # Top Row: Index, Button, Name
        top_row = QHBoxLayout()
        
        self.lbl_index = QLabel(f"{self.index + 1}.")
        self.lbl_index.setFixedWidth(30)
        self.lbl_index.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        
        self.btn_play = QPushButton()
        self.btn_play.setFixedSize(30, 30) # Back to 30x30
        self.btn_play.setStyleSheet("background-color: transparent; border: none;")
        self.btn_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        self.btn_play.setIconSize(QSize(14, 14)) # Smaller icon size
        self.btn_play.clicked.connect(self.play_requested.emit)
        
        self.lbl_name = MarqueeLabel(self.display_name)
        self.lbl_name.setFont(QFont(FONT_FAMILY_BOLD, 12))
        # Context menu policy
        self.lbl_name.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lbl_name.customContextMenuRequested.connect(self.show_context_menu)
        
        top_row.addWidget(self.lbl_index)
        top_row.addWidget(self.btn_play)
        top_row.addWidget(self.lbl_name)
        
        self.layout.addLayout(top_row)

        # Bottom Row: Slider and Time (Hidden by default)
        self.seek_container = QWidget()
        seek_layout = QHBoxLayout(self.seek_container)
        seek_layout.setContentsMargins(40, 5, 0, 5) # Added bottom margin too
        
        self.slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.on_slider_moved)
        
        self.lbl_time = QLabel("00:00/00:00")
        self.lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 10))
        
        seek_layout.addWidget(self.slider)
        seek_layout.addWidget(self.lbl_time)
        
        self.layout.addWidget(self.seek_container)
        self.seek_container.hide()

        # Style
        if self.is_standard:
            self.setStyleSheet("background-color: #2e5e2e; color: white; border-radius: 5px;")
        else:
            self.setStyleSheet("color: white;")

    def update_index(self, new_index):
        self.index = new_index
        self.lbl_index.setText(f"{self.index + 1}.")

    def update_display_name(self):
        self.lbl_name.setText(self.display_name)

    def set_playing_state(self, is_playing):
        self.is_playing = is_playing
        if is_playing:
            self.btn_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "pause.png")))
            self.seek_container.show()
        else:
            self.btn_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
            pass 
        
        # Notify parent to resize item
        self.size_changed.emit()

    def set_inactive(self):
        self.is_playing = False
        self.btn_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        self.seek_container.hide()
        self.size_changed.emit()

    def show_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 8px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #4a4a4a;
            }
        """)
        action_rename = menu.addAction("Изменить название")
        action_delete = menu.addAction("Удалить трек")
        
        res = menu.exec(self.lbl_name.mapToGlobal(pos))
        
        if res == action_rename:
            self.rename_requested.emit()
        elif res == action_delete:
            self.delete_requested.emit()

    def on_slider_moved(self, position):
        self.slider_moved.emit(position)

class MusicPlayer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Audio Backend
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5) # Default volume 50%
        self.last_volume = 0.5 # To restore after unmute
        
        self.tracks = [] # List of TrackWidget objects (stored inside QListWidget items)
        self.current_track_index = -1
        self.is_looping = False
        
        self.init_ui()
        self.setup_connections()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Top Area ---
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        self.btn_load_std = QPushButton("Загрузить стандартный набор")
        self.btn_load_std.setStyleSheet("background-color: #505050; color: white; padding: 8px;")
        self.btn_load_std.clicked.connect(self.load_standard_tracks)
        
        self.btn_add_file = QPushButton("Добавить аудиофайл")
        self.btn_add_file.setStyleSheet("background-color: #4472c4; color: white; padding: 8px; font-weight: bold;")
        self.btn_add_file.clicked.connect(self.add_file)
        
        top_layout.addWidget(self.btn_load_std)
        top_layout.addWidget(self.btn_add_file)
        
        main_layout.addWidget(top_widget)
        
        # --- List Widget for Tracks (Supports Drag & Drop) ---
        self.track_list = QListWidget()
        self.track_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.track_list.setStyleSheet("QListWidget { border: none; background-color: transparent; } QListWidget::item { background-color: transparent; }")
        self.track_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.track_list.setFocusPolicy(Qt.FocusPolicy.NoFocus) # Remove focus rect
        
        # Handle drag and drop reordering
        self.track_list.model().rowsMoved.connect(self.on_rows_moved)
        
        main_layout.addWidget(self.track_list)
        
        # --- Bottom Control Panel ---
        self.control_panel = QFrame()
        self.control_panel.setStyleSheet("background-color: #353535; border-top: 1px solid #555;")
        self.control_panel.setFixedHeight(140)
        
        cp_layout = QVBoxLayout(self.control_panel)
        
        # 1. Track Name
        self.cp_lbl_name = MarqueeLabel("Нет трека")
        self.cp_lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cp_lbl_name.setFont(QFont(FONT_FAMILY_BOLD, 14))
        self.cp_lbl_name.setStyleSheet("color: white;")
        cp_layout.addWidget(self.cp_lbl_name)
        
        # 2. Slider + Time
        slider_layout = QHBoxLayout()
        self.cp_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.cp_slider.sliderMoved.connect(self.set_position)
        self.cp_slider.sliderPressed.connect(self.player.pause)
        self.cp_slider.sliderReleased.connect(self.player.play)
        
        self.cp_lbl_time = QLabel("00:00/00:00")
        self.cp_lbl_time.setStyleSheet("color: white;")
        self.cp_lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 10))
        
        slider_layout.addWidget(self.cp_slider)
        slider_layout.addWidget(self.cp_lbl_time)
        cp_layout.addLayout(slider_layout)
        
        # 3. Buttons & Volume
        btns_layout = QHBoxLayout()
        
        # Left aligned controls
        self.btn_prev = QPushButton()
        self.btn_prev.setFixedSize(40, 40)
        self.btn_prev.setStyleSheet("background-color: transparent; border: none;")
        self.btn_prev.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "backwards.png")))
        self.btn_prev.setIconSize(QSize(24, 24)) # Reduced from 32
        self.btn_prev.clicked.connect(self.play_prev)
        
        self.btn_play_pause = QPushButton()
        self.btn_play_pause.setFixedSize(50, 50)
        self.btn_play_pause.setStyleSheet("background-color: transparent; border: none;")
        self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        self.btn_play_pause.setIconSize(QSize(32, 32)) # Reduced from 48
        self.btn_play_pause.clicked.connect(self.toggle_play)
        
        self.btn_next = QPushButton()
        self.btn_next.setFixedSize(40, 40)
        self.btn_next.setStyleSheet("background-color: transparent; border: none;")
        self.btn_next.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "forwards.png")))
        self.btn_next.setIconSize(QSize(24, 24)) # Reduced from 32
        self.btn_next.clicked.connect(self.play_next)
        
        btns_layout.addWidget(self.btn_prev)
        btns_layout.addSpacing(5)
        btns_layout.addWidget(self.btn_play_pause)
        btns_layout.addSpacing(5)
        btns_layout.addWidget(self.btn_next)
        
        btns_layout.addSpacing(20)
        
        # Volume Control
        self.btn_vol = QPushButton()
        self.btn_vol.setFixedSize(30, 30)
        self.btn_vol.setStyleSheet("background-color: transparent; border: none;")
        self.btn_vol.setIconSize(QSize(24, 24))
        self.btn_vol.clicked.connect(self.toggle_mute)
        self.update_volume_icon(50) # Initial icon
        btns_layout.addWidget(self.btn_vol)
        
        self.vol_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(50)
        self.vol_slider.setFixedWidth(100)
        self.vol_slider.valueChanged.connect(self.set_volume)
        btns_layout.addWidget(self.vol_slider)
        
        # Spacer
        btns_layout.addStretch()
        
        # Loop button (Right aligned)
        self.btn_loop = QPushButton()
        self.btn_loop.setFixedSize(40, 40)
        self.btn_loop.setCheckable(True)
        self.btn_loop.setStyleSheet("background-color: transparent; border: none;")
        self.btn_loop.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "repeatoff.png")))
        self.btn_loop.setIconSize(QSize(32, 32))
        self.btn_loop.toggled.connect(self.toggle_loop)
        
        btns_layout.addWidget(self.btn_loop)
        
        cp_layout.addLayout(btns_layout)
        
        main_layout.addWidget(self.control_panel)

    def setup_connections(self):
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)

    def add_file(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Выберите аудиофайлы", "", "Audio (*.mp3 *.wav *.ogg)")
        if file_paths:
            for file_path in file_paths:
                self.add_track_to_list(file_path)

    def load_standard_tracks(self):
        if not os.path.exists(BASE_MUSIC_DIR):
            print(f"Base music directory not found: {BASE_MUSIC_DIR}")
            return
            
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Загрузка стандартного набора")
        msg_box.setText("Как вы хотите загрузить стандартный набор треков?")
        
        btn_add = msg_box.addButton("Добавить", QMessageBox.ButtonRole.ActionRole)
        btn_replace = msg_box.addButton("Заменить", QMessageBox.ButtonRole.ActionRole)
        btn_cancel = msg_box.addButton("Отмена", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == btn_cancel:
            return
            
        if clicked_button == btn_replace:
            self.clear_playlist()
            
        # Load tracks
        for filename in os.listdir(BASE_MUSIC_DIR):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg')):
                file_path = os.path.join(BASE_MUSIC_DIR, filename)
                self.add_track_to_list(file_path, is_standard=True)

    def clear_playlist(self):
        self.player.stop()
        self.track_list.clear()
        self.current_track_index = -1
        self.set_paused_ui()
        self.cp_lbl_name.setText("Нет трека")
        self.cp_lbl_time.setText("00:00/00:00")
        self.cp_slider.setValue(0)

    def add_track_to_list(self, file_path, is_standard=False):
        index = self.track_list.count()
        track_widget = TrackWidget(index, file_path, is_standard=is_standard)
        
        # Connect signals
        # Use closures to capture the widget instance, not index, because index changes
        track_widget.play_requested.connect(lambda w=track_widget: self.play_track_by_widget(w))
        track_widget.rename_requested.connect(lambda w=track_widget: self.rename_track(w))
        track_widget.delete_requested.connect(lambda w=track_widget: self.delete_track(w))
        track_widget.slider_moved.connect(self.set_position)
        track_widget.size_changed.connect(lambda w=track_widget: self.on_track_size_changed(w))
        
        item = QListWidgetItem(self.track_list)
        item.setSizeHint(track_widget.sizeHint())
        
        self.track_list.addItem(item)
        self.track_list.setItemWidget(item, track_widget)
        
        # Store widget reference in item for easy access if needed, though setItemWidget does it
        # We need to keep track of widgets to update indices
        self.update_indices()

    def on_track_size_changed(self, widget):
        # Find item for this widget and update its size hint
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if self.track_list.itemWidget(item) == widget:
                item.setSizeHint(widget.sizeHint())
                break

    def update_indices(self):
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            widget = self.track_list.itemWidget(item)
            if widget:
                widget.update_index(i)

    def on_rows_moved(self, parent, start, end, destination, row):
        # Called after drag and drop reordering
        self.update_indices()
        
        # If the playing track moved, we need to update current_track_index
        # But since we track by index, and index changed, we need to find where the playing widget went
        # Actually, it's easier to just rely on the widget identity.
        # Let's find the index of the currently playing widget
        if self.current_track_index != -1:
            # This logic is tricky because current_track_index is just an int.
            # We need to know WHICH widget is playing.
            # Let's store the playing widget reference instead of index?
            # Or just search for the widget that has is_playing = True
            for i in range(self.track_list.count()):
                item = self.track_list.item(i)
                widget = self.track_list.itemWidget(item)
                if widget and widget.is_playing:
                    self.current_track_index = i
                    break

    def play_track_by_widget(self, widget):
        # Find index of this widget
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if self.track_list.itemWidget(item) == widget:
                self.play_track(i)
                return

    def play_track(self, index):
        if 0 <= index < self.track_list.count():
            # If clicking the same track that is playing
            if index == self.current_track_index:
                self.toggle_play()
                return

            # Stop previous
            if self.current_track_index != -1 and self.current_track_index < self.track_list.count():
                item = self.track_list.item(self.current_track_index)
                widget = self.track_list.itemWidget(item)
                if widget:
                    widget.set_inactive()
            
            self.current_track_index = index
            item = self.track_list.item(index)
            widget = self.track_list.itemWidget(item)
            
            if widget:
                self.player.setSource(QUrl.fromLocalFile(widget.file_path))
                self.player.play()
                
                # Update UI
                widget.set_playing_state(True)
                self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "pause.png")))
                self.cp_lbl_name.setText(widget.display_name)

    def delete_track(self, widget):
        # Find index
        index = -1
        for i in range(self.track_list.count()):
            item = self.track_list.item(i)
            if self.track_list.itemWidget(item) == widget:
                index = i
                break
        
        if index != -1:
            # If deleting playing track
            if index == self.current_track_index:
                self.player.stop()
                self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
                self.cp_lbl_name.setText("Нет трека")
                self.cp_lbl_time.setText("00:00/00:00")
                self.cp_slider.setValue(0)
                self.current_track_index = -1
            elif index < self.current_track_index:
                self.current_track_index -= 1
                
            self.track_list.takeItem(index)
            self.update_indices()

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
            if self.current_track_index != -1:
                item = self.track_list.item(self.current_track_index)
                widget = self.track_list.itemWidget(item)
                if widget: widget.set_playing_state(False)
        elif self.current_track_index != -1:
            self.player.play()
            self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "pause.png")))
            item = self.track_list.item(self.current_track_index)
            widget = self.track_list.itemWidget(item)
            if widget: widget.set_playing_state(True)
        elif self.track_list.count() > 0:
            # If nothing selected but tracks exist, play first
            self.play_track(0)

    def set_paused_ui(self):
        self.btn_play_pause.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        if self.current_track_index != -1:
            item = self.track_list.item(self.current_track_index)
            widget = self.track_list.itemWidget(item)
            if widget: widget.set_playing_state(False)

    def play_next(self):
        if self.track_list.count() == 0: return
        next_index = (self.current_track_index + 1) % self.track_list.count()
        self.play_track(next_index)

    def play_prev(self):
        if self.track_list.count() == 0: return
        prev_index = (self.current_track_index - 1) % self.track_list.count()
        self.play_track(prev_index)

    def toggle_loop(self, checked):
        self.is_looping = checked
        if checked:
            self.btn_loop.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "repeaton.png")))
        else:
            self.btn_loop.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "repeatoff.png")))

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)
        self.update_volume_icon(value)

    def toggle_mute(self):
        current_vol = self.audio_output.volume()
        if current_vol > 0:
            self.last_volume = current_vol
            self.audio_output.setVolume(0)
            self.vol_slider.blockSignals(True)
            self.vol_slider.setValue(0)
            self.vol_slider.blockSignals(False)
            self.update_volume_icon(0)
        else:
            self.audio_output.setVolume(self.last_volume)
            val = int(self.last_volume * 100)
            self.vol_slider.blockSignals(True)
            self.vol_slider.setValue(val)
            self.vol_slider.blockSignals(False)
            self.update_volume_icon(val)

    def update_volume_icon(self, value):
        icon_name = "SoundOff.png"
        if value > 50:
            icon_name = "SoundLoud.png"
        elif value > 0:
            icon_name = "SoundLow.png"
        
        self.btn_vol.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, icon_name)))

    def rename_track(self, widget):
        new_name, ok = QInputDialog.getText(self, "Изменить название", "Введите новое название трека:", text=widget.display_name)
        if ok and new_name:
            widget.display_name = new_name
            widget.update_display_name()
            
            # Check if this widget corresponds to current track index
            # (We can't just check index because it might have moved, but widget ref is stable)
            if self.current_track_index != -1:
                item = self.track_list.item(self.current_track_index)
                if self.track_list.itemWidget(item) == widget:
                    self.cp_lbl_name.setText(new_name)

    def on_position_changed(self, position):
        # Update bottom slider
        self.cp_slider.setValue(position)
        
        # Update row slider if active
        if self.current_track_index != -1:
            item = self.track_list.item(self.current_track_index)
            widget = self.track_list.itemWidget(item)
            if widget:
                widget.slider.setValue(position)
            
        self.update_time_labels(position, self.player.duration())

    def on_duration_changed(self, duration):
        self.cp_slider.setRange(0, duration)
        if self.current_track_index != -1:
            item = self.track_list.item(self.current_track_index)
            widget = self.track_list.itemWidget(item)
            if widget:
                widget.slider.setRange(0, duration)
        self.update_time_labels(self.player.position(), duration)

    def update_time_labels(self, position, duration):
        def format_time(ms):
            seconds = (ms // 1000) % 60
            minutes = (ms // 60000)
            return f"{minutes:02d}:{seconds:02d}"
            
        text = f"{format_time(position)}/{format_time(duration)}"
        self.cp_lbl_time.setText(text)
        if self.current_track_index != -1:
            item = self.track_list.item(self.current_track_index)
            widget = self.track_list.itemWidget(item)
            if widget:
                widget.lbl_time.setText(text)

    def set_position(self, position):
        self.player.setPosition(position)

    def on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.is_looping:
                self.player.play()
            else:
                self.play_next()
