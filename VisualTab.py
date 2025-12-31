from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QFileDialog, QScrollArea, QSlider, QFrame, QMenu, QInputDialog, 
                             QStyle, QSizePolicy, QGroupBox, QRadioButton, QCheckBox, QButtonGroup, QLineEdit, QGridLayout)
from PyQt6.QtCore import Qt, QUrl, QSize, pyqtSignal, QTime, QRect, QTimer, QPoint
from PyQt6.QtGui import QAction, QFont, QIcon, QCursor, QPainter, QFontMetrics, QColor, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
from config import FONT_FAMILY_REGULAR, FONT_FAMILY_BOLD, PLAYER_BUTTONS_DIR
from widgets import WrappingButton

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.pos().x()) / self.width()
            val = max(self.minimum(), min(self.maximum(), val))
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
            event.accept()
        super().mousePressEvent(event)

class VisualTab(QWidget):
    # Signals to control the TimerWindow
    background_color_changed = pyqtSignal(str)
    overlay_changed = pyqtSignal(str) # "None", "Black", "Cube", "Constructor", "Custom"
    custom_overlay_changed = pyqtSignal(str) # path to custom image
    break_timer_state_changed = pyqtSignal(bool, int) # enabled, total_seconds
    break_timer_control = pyqtSignal(str) # "play", "pause", "stop"
    
    # Intro signals
    intro_state_changed = pyqtSignal(bool)
    intro_control = pyqtSignal(str) # "play", "pause", "stop"
    intro_seek = pyqtSignal(int)
    intro_volume_changed = pyqtSignal(int)
    
    # Timer Window Control
    open_timer_window_requested = pyqtSignal()

    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self.timer = timer
        self.last_overlay_button = None
        self.custom_image_path = None
        
        # For video preview
        self.video_sink = None 
        
        self.init_ui()
        
        # Connect to timer window state changes
        self.timer.timer_window_state_changed.connect(self.on_timer_window_state_changed)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # --- PREVIEW Block ---
        preview_group = QGroupBox("ПРЕДПРОСМОТР")
        preview_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("Окно таймера не открыто")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(320, 180) # 16:9 aspect ratio
        self.preview_label.setStyleSheet("background-color: #222; color: #888; border: 1px solid #444;")
        preview_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(preview_group)
        
        # --- Reset Button ---
        self.btn_reset = QPushButton("Вернуть таймер")
        self.btn_reset.clicked.connect(self.reset_visuals)
        main_layout.addWidget(self.btn_reset)
        
        # --- Open Timer Window Button ---
        self.btn_open_timer = QPushButton("Открыть окно таймера")
        self.btn_open_timer.setStyleSheet("background-color: #4472c4; color: white; font-weight: bold;")
        self.btn_open_timer.clicked.connect(self.open_timer_window)
        self.btn_open_timer.hide() # Initially hidden, will be updated by signal
        main_layout.addWidget(self.btn_open_timer)
        
        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # --- TIMER Block ---
        timer_group = QGroupBox("ТАЙМЕР")
        timer_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        timer_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_start = WrappingButton("Запуск")
        self.btn_start.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.on_start_pause)
        
        self.btn_stop = WrappingButton("Стоп")
        self.btn_stop.setStyleSheet("background-color: #c83232; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.on_stop)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        timer_layout.addLayout(btn_layout)
        
        time_adj_layout = QGridLayout()
        times = [5, 10, 15, 30, 60]
        for i, mins in enumerate(times):
            btn_plus = WrappingButton(f"+{mins} мин")
            btn_plus.clicked.connect(lambda checked, m=mins: self.timer.add_time(m))
            time_adj_layout.addWidget(btn_plus, 0, i)
            
            btn_minus = WrappingButton(f"-{mins} мин")
            btn_minus.clicked.connect(lambda checked, m=mins: self.timer.subtract_time(m))
            time_adj_layout.addWidget(btn_minus, 1, i)
            
        timer_layout.addLayout(time_adj_layout)
        timer_group.setLayout(timer_layout)
        content_layout.addWidget(timer_group)
        
        # --- BACKGROUND Block ---
        bg_group = QGroupBox("ФОН")
        bg_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        bg_layout = QHBoxLayout(bg_group)
        
        self.bg_color_group = QButtonGroup(self)
        self.bg_color_group.setExclusive(True)
        
        colors = ["#000000", "#ffffff", "#a5a5a5", "#ed7d31", "#7030a0"]
        for color in colors:
            btn = QPushButton()
            btn.setFixedSize(30, 30)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {color}; border: 1px solid #555; }}
                QPushButton:checked {{ border: 2px solid #00ff00; }}
            """)
            btn.clicked.connect(lambda checked, c=color: self.on_bg_color_selected(c))
            self.bg_color_group.addButton(btn)
            bg_layout.addWidget(btn)
        
        bg_layout.addStretch()
        content_layout.addWidget(bg_group)
        
        # --- OVERLAY Block ---
        overlay_group = QGroupBox("ЗАСТАВКА")
        overlay_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        overlay_layout = QVBoxLayout(overlay_group)
        
        self.overlay_group = QButtonGroup(self)
        self.overlay_group.setExclusive(True)
        
        self.rb_black = QRadioButton("Черный экран")
        self.rb_cube = QRadioButton("Куб")
        self.rb_constructor = QRadioButton("Конструктор")
        self.rb_custom = QRadioButton("Свой файл")
        self.rb_custom.setEnabled(False) # Disabled by default until file selected
        
        for rb in [self.rb_black, self.rb_cube, self.rb_constructor, self.rb_custom]:
            rb.clicked.connect(lambda checked, btn=rb: self.handle_radio_click(btn))
            self.overlay_group.addButton(rb)
            overlay_layout.addWidget(rb)
            
        # Custom file selection
        custom_file_layout = QHBoxLayout()
        self.btn_browse_custom = QPushButton("Обзор...")
        self.btn_browse_custom.clicked.connect(self.browse_custom_image)
        self.lbl_custom_filename = QLabel("")
        self.lbl_custom_filename.setStyleSheet("color: #888;")
        
        custom_file_layout.addWidget(self.btn_browse_custom)
        custom_file_layout.addWidget(self.lbl_custom_filename)
        custom_file_layout.addStretch()
        overlay_layout.addLayout(custom_file_layout)
        
        # Break Timer
        self.chk_break_timer = QCheckBox("Таймер перерыва")
        self.chk_break_timer.setEnabled(False)
        self.chk_break_timer.toggled.connect(self.on_break_timer_toggled)
        overlay_layout.addWidget(self.chk_break_timer)
        
        break_timer_controls = QHBoxLayout()
        self.input_break_min = QLineEdit("10")
        self.input_break_sec = QLineEdit("00")
        
        for inp in [self.input_break_min, self.input_break_sec]:
            inp.setFixedWidth(40)
            inp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_break_play = QPushButton()
        self.btn_break_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        self.btn_break_play.setFixedSize(30, 30)
        self.btn_break_play.setIconSize(QSize(20, 20))
        self.btn_break_play.clicked.connect(self.on_break_play_pause)
        
        self.btn_break_stop = QPushButton("■")
        self.btn_break_stop.setFixedSize(30, 30)
        self.btn_break_stop.clicked.connect(lambda: self.break_timer_control.emit("stop"))
        
        break_timer_controls.addWidget(self.input_break_min)
        break_timer_controls.addWidget(QLabel(":"))
        break_timer_controls.addWidget(self.input_break_sec)
        break_timer_controls.addSpacing(10)
        break_timer_controls.addWidget(self.btn_break_play)
        break_timer_controls.addWidget(self.btn_break_stop)
        break_timer_controls.addStretch()
        
        self.break_timer_widget = QWidget()
        self.break_timer_widget.setLayout(break_timer_controls)
        self.break_timer_widget.setEnabled(False)
        overlay_layout.addWidget(self.break_timer_widget)
        
        content_layout.addWidget(overlay_group)
        
        # --- INTRO Block ---
        intro_group = QGroupBox("ИНТРО")
        intro_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        intro_layout = QVBoxLayout(intro_group)
        
        self.chk_intro = QCheckBox("Вывести интро")
        self.chk_intro.toggled.connect(self.on_intro_toggled)
        intro_layout.addWidget(self.chk_intro)
        
        self.intro_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.intro_slider.setEnabled(False)
        self.intro_slider.sliderMoved.connect(self.on_intro_seek)
        self.intro_slider.sliderPressed.connect(lambda: self.intro_control.emit("pause"))
        self.intro_slider.sliderReleased.connect(lambda: self.intro_control.emit("play"))
        intro_layout.addWidget(self.intro_slider)
        
        intro_controls = QHBoxLayout()
        self.btn_intro_play = QPushButton()
        self.btn_intro_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        self.btn_intro_play.setFixedSize(30, 30)
        self.btn_intro_play.setIconSize(QSize(20, 20))
        self.btn_intro_play.clicked.connect(self.on_intro_play_pause)
        self.btn_intro_play.setEnabled(False)
        
        self.btn_intro_stop = QPushButton("■")
        self.btn_intro_stop.setFixedSize(30, 30)
        self.btn_intro_stop.clicked.connect(lambda: self.intro_control.emit("stop"))
        self.btn_intro_stop.setEnabled(False)
        
        intro_controls.addWidget(self.btn_intro_play)
        intro_controls.addWidget(self.btn_intro_stop)
        intro_controls.addSpacing(10)
        
        # Volume slider for intro
        lbl_vol_intro = QLabel("🔊")
        lbl_vol_intro.setStyleSheet("color: white; font-size: 16px;")
        intro_controls.addWidget(lbl_vol_intro)
        
        self.intro_vol_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.intro_vol_slider.setRange(0, 100)
        self.intro_vol_slider.setValue(100)
        self.intro_vol_slider.setFixedWidth(100)
        self.intro_vol_slider.valueChanged.connect(self.intro_volume_changed.emit)
        self.intro_vol_slider.setEnabled(False)
        intro_controls.addWidget(self.intro_vol_slider)
        
        intro_controls.addStretch()
        
        intro_layout.addLayout(intro_controls)
        
        content_layout.addWidget(intro_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def browse_custom_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.custom_image_path = file_path
            filename = os.path.basename(file_path)
            
            # Elide text if too long
            metrics = QFontMetrics(self.lbl_custom_filename.font())
            elided_text = metrics.elidedText(filename, Qt.TextElideMode.ElideRight, 150) # Approx width
            self.lbl_custom_filename.setText(elided_text)
            self.lbl_custom_filename.setToolTip(filename)
            
            self.rb_custom.setEnabled(True)
            self.custom_overlay_changed.emit(file_path)
            
            # If custom radio is already checked, update the overlay immediately
            if self.rb_custom.isChecked():
                self.overlay_changed.emit("Custom")

    def on_start_pause(self):
        if not self.timer.is_running:
            self.timer.start()
            self.btn_start.setText("Пауза")
            self.btn_start.setStyleSheet("background-color: #ffc000; color: black; font-weight: bold;")
        elif self.timer.is_paused:
            self.timer.resume()
            self.btn_start.setText("Пауза")
            self.btn_start.setStyleSheet("background-color: #ffc000; color: black; font-weight: bold;")
        else:
            self.timer.pause()
            self.btn_start.setText("Возобновить")
            self.btn_start.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold;")

    def on_stop(self):
        self.timer.stop()
        self.btn_start.setText("Запуск")
        self.btn_start.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold;")

    def update_preview(self, pixmap):
        if pixmap:
            self.preview_label.setPixmap(pixmap.scaled(
                self.preview_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.preview_label.setText("Окно таймера не открыто")

    def on_preview_frame_changed(self, frame):
        image = frame.toImage()
        if not image.isNull():
            pixmap = QPixmap.fromImage(image)
            self.update_preview(pixmap)

    def handle_radio_click(self, clicked_button):
        if self.last_overlay_button == clicked_button:
            self.overlay_group.setExclusive(False)
            clicked_button.setChecked(False)
            self.overlay_group.setExclusive(True)
            self.last_overlay_button = None
            self.on_overlay_changed(None)
        else:
            self.last_overlay_button = clicked_button
            self.on_overlay_changed(clicked_button)

    def on_bg_color_selected(self, color):
        self.background_color_changed.emit(color)

    def on_overlay_changed(self, button):
        if button is None:
            self.overlay_changed.emit("None")
            self.chk_break_timer.setEnabled(False)
            self.chk_break_timer.setChecked(False)
            return
            
        self.chk_break_timer.setEnabled(True)
        
        if button == self.rb_black:
            self.overlay_changed.emit("Black")
        elif button == self.rb_cube:
            self.overlay_changed.emit("Cube")
        elif button == self.rb_constructor:
            self.overlay_changed.emit("Constructor")
        elif button == self.rb_custom:
            self.overlay_changed.emit("Custom")

    def on_break_timer_toggled(self, checked):
        self.break_timer_widget.setEnabled(checked)
        if checked:
            try:
                mins = int(self.input_break_min.text())
                secs = int(self.input_break_sec.text())
                total_seconds = mins * 60 + secs
                self.break_timer_state_changed.emit(True, total_seconds)
            except ValueError:
                self.break_timer_state_changed.emit(True, 600) # Default 10 mins
        else:
            self.break_timer_state_changed.emit(False, 0)

    def on_break_play_pause(self):
        if self.btn_break_play.property("state") == "playing":
            self.break_timer_control.emit("pause")
            self.btn_break_play.setProperty("state", "paused")
            self.btn_break_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        else:
            self.break_timer_control.emit("play")
            self.btn_break_play.setProperty("state", "playing")
            self.btn_break_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "pause.png")))
            
    def on_intro_toggled(self, checked):
        self.intro_state_changed.emit(checked)
        self.intro_slider.setEnabled(checked)
        self.btn_intro_play.setEnabled(checked)
        self.btn_intro_stop.setEnabled(checked)
        self.intro_vol_slider.setEnabled(checked)
        
        if not checked:
            self.btn_intro_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
            self.btn_intro_play.setProperty("state", "paused")
            self.intro_slider.setValue(0)

    def on_intro_play_pause(self):
        if self.btn_intro_play.property("state") == "playing":
            self.intro_control.emit("pause")
            self.btn_intro_play.setProperty("state", "paused")
            self.btn_intro_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "play.png")))
        else:
            self.intro_control.emit("play")
            self.btn_intro_play.setProperty("state", "playing")
            self.btn_intro_play.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "pause.png")))

    def on_intro_seek(self, position):
        self.intro_seek.emit(position)

    def update_intro_slider(self, position, duration):
        self.intro_slider.setRange(0, duration)
        self.intro_slider.setValue(position)

    def intro_finished(self):
        self.chk_intro.setChecked(False)

    def reset_visuals(self):
        # Uncheck all overlay radio buttons
        if self.last_overlay_button:
            self.overlay_group.setExclusive(False)
            self.last_overlay_button.setChecked(False)
            self.overlay_group.setExclusive(True)
            self.last_overlay_button = None
            
        # Uncheck break timer
        self.chk_break_timer.setChecked(False)
        self.chk_break_timer.setEnabled(False)
        
        # Uncheck intro
        self.chk_intro.setChecked(False)
        
        # Reset overlay
        self.overlay_changed.emit("None")
        
        # We don't reset the background color per instructions

    def open_timer_window(self):
        self.open_timer_window_requested.emit()

    def on_timer_window_state_changed(self, is_open):
        if is_open:
            self.btn_open_timer.hide()
        else:
            self.btn_open_timer.show()
