from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt, QRectF, QSize, QUrl, QRect
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QStackedLayout, QSizePolicy
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath, QMovie, QPixmap, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from config import FONT_FAMILY_REGULAR, FONT_FAMILY_BOLD, SCRIPT_DIR, ORANGE_LVL_DIR
import os
import config

class ProgressBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_hours = 5
        self.current_seconds = 5 * 3600
        self.setFixedHeight(20) 
        self.border_color = None # None means no border
        self.red_effect_ratio = 0.0 # 0.0 to 1.0, how much red to blend in

    def update_progress(self, seconds, red_ratio=0.0):
        self.current_seconds = seconds
        self.red_effect_ratio = red_ratio
        self.update()

    def set_border_color(self, color):
        self.border_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        spacing = 10
        block_width = (width - (self.total_hours - 1) * spacing) / self.total_hours
        
        total_duration = self.total_hours * 3600
        
        time_passed = total_duration - self.current_seconds
        if time_passed < 0: time_passed = 0
        if time_passed > total_duration: time_passed = total_duration
        
        radius = height / 2
        
        # Calculate colors based on red effect
        white_color = QColor("white")
        grey_color = QColor("#333333")
        
        if self.red_effect_ratio > 0:
            # Blend white towards red
            r = white_color.red() + (255 - white_color.red()) * self.red_effect_ratio # Stay 255
            g = white_color.green() * (1 - self.red_effect_ratio)
            b = white_color.blue() * (1 - self.red_effect_ratio)
            white_color = QColor(int(r), int(g), int(b))
        
        for i in range(self.total_hours):
            x = i * (block_width + spacing)
            rect = QRectF(x, 0, block_width, height)
            
            hour_start = i * 3600
            hour_end = (i + 1) * 3600
            
            fill_ratio = 0.0
            if time_passed > hour_start:
                if time_passed >= hour_end:
                    fill_ratio = 1.0
                else:
                    fill_ratio = (time_passed - hour_start) / 3600
            
            # Draw border if set
            if self.border_color:
                painter.setPen(QPen(QColor(self.border_color), 2))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
            
            if fill_ratio == 0.0:
                # Fully remaining (white/red)
                painter.setBrush(QBrush(white_color))
                painter.drawRoundedRect(rect, radius, radius)
            elif fill_ratio == 1.0:
                # Fully passed (grey)
                painter.setBrush(QBrush(grey_color))
                painter.drawRoundedRect(rect, radius, radius)
            else:
                # Partially filled
                split_x = rect.x() + rect.width() * fill_ratio
                
                # Draw grey part (left)
                path_grey = QPainterPath()
                path_grey.moveTo(split_x, 0)
                path_grey.lineTo(rect.x() + radius, 0)
                path_grey.arcTo(rect.x(), 0, radius * 2, radius * 2, 90, 90)
                path_grey.lineTo(rect.x(), rect.height() - radius)
                path_grey.arcTo(rect.x(), rect.y(), radius * 2, radius * 2, 180, 90)
                path_grey.lineTo(split_x, rect.height())
                path_grey.closeSubpath()
                
                painter.setBrush(QBrush(grey_color))
                painter.drawPath(path_grey)
                
                # Draw white/red part (right)
                path_white = QPainterPath()
                path_white.moveTo(split_x, 0)
                path_white.lineTo(rect.right() - radius, 0)
                path_white.arcTo(rect.right() - radius * 2, 0, radius * 2, radius * 2, 90, -90)
                path_white.lineTo(rect.right(), rect.height() - radius)
                path_white.arcTo(rect.right() - radius * 2, rect.y(), radius * 2, radius * 2, 0, -90)
                path_white.lineTo(split_x, rect.height())
                path_white.closeSubpath()
                
                painter.setBrush(QBrush(white_color))
                painter.drawPath(path_white)
                
                # Redraw border on top if needed
                if self.border_color:
                     painter.setBrush(Qt.BrushStyle.NoBrush)
                     painter.drawRoundedRect(rect, radius, radius)

class ScalableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(1, 1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        if not self._pixmap or self._pixmap.isNull():
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        scaled_pixmap = self._pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Center the image
        x = (self.width() - scaled_pixmap.width()) // 2
        y = (self.height() - scaled_pixmap.height()) // 2
        
        painter.drawPixmap(x, y, scaled_pixmap)

class TimerWindow(QWidget):
    window_closed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Таймер")
        self.resize(800, 600)
        self.setStyleSheet("background-color: black;")
        
        # Установка иконки
        icon_path = os.path.join(config.SCRIPT_DIR, "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # --- Main Timer Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        
        # Header container (for Orange Level mode)
        self.header_container = QWidget()
        self.header_layout = QVBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.lbl_title = QLabel("ОСТАТОЧНОЕ ВРЕМЯ ПОХОДА")
        self.lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 48))
        self.lbl_title.setStyleSheet("color: white;")
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.lbl_title)
        
        self.lbl_time = QLabel("05:00:00")
        self.lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 150))
        self.lbl_time.setStyleSheet("color: white;")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_layout.addWidget(self.lbl_time)
        
        self.main_layout.addWidget(self.header_container)
        
        self.main_layout.addSpacing(20)
        
        self.progress_bar = ProgressBarWidget()
        self.main_layout.addWidget(self.progress_bar)
        
        # --- Orange Level Image (Hidden by default) ---
        self.orange_level_widget = ScalableImageLabel()
        self.orange_level_widget.hide()
        self.main_layout.addWidget(self.orange_level_widget)
        
        # --- Overlay (Child Widget, not in layout) ---
        self.overlay_widget = QLabel(self)
        self.overlay_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay_widget.hide()
        
        # --- Video Label (Child Widget, not in layout) ---
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        self.video_label.hide()
        
        # --- Break Timer (Child Widget, not in layout) ---
        self.lbl_break_timer = QLabel("10:00", self)
        self.lbl_break_timer.setFont(QFont(FONT_FAMILY_REGULAR, 60))
        self.lbl_break_timer.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 10px;")
        self.lbl_break_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_break_timer.hide()
        self.lbl_break_timer.adjustSize()
        
        self.movie = None
        self.orange_pixmap = None
        self.is_orange_mode = False
        self.custom_overlay_path = None
        
        self.current_text_color = "white" # Track current text color for red effect

    def update_time(self, time_str, seconds, red_ratio=0.0, blink_visible=True):
        self.lbl_time.setText(time_str)
        self.progress_bar.update_progress(seconds, red_ratio)
        
        # Calculate final color based on red effect
        base_color = QColor(self.current_text_color)
        if red_ratio > 0:
            # Blend current text color towards red
            r = base_color.red() + (255 - base_color.red()) * red_ratio
            g = base_color.green() * (1 - red_ratio)
            b = base_color.blue() * (1 - red_ratio)
            final_color = QColor(int(r), int(g), int(b))
        else:
            final_color = base_color
            
        # Apply to Title (always visible)
        self.lbl_title.setStyleSheet(f"color: {final_color.name()};")
            
        # Apply to Time (blinking)
        if blink_visible:
            self.lbl_time.setStyleSheet(f"color: {final_color.name()};")
        else:
            # Use transparent color instead of hiding widget to prevent layout shift
            self.lbl_time.setStyleSheet("color: transparent;")
            
        # Ensure widget is always visible in layout
        self.lbl_time.show()

    def set_title(self, title):
        self.lbl_title.setText(title)

    def set_background_color(self, color_hex):
        self.setStyleSheet(f"background-color: {color_hex};")
        
        # Determine text color based on background brightness
        bg_color = QColor(color_hex)
        is_light = bg_color.lightness() > 128
        self.current_text_color = "black" if is_light else "white"
        
        self.lbl_title.setStyleSheet(f"color: {self.current_text_color};")
        self.lbl_time.setStyleSheet(f"color: {self.current_text_color};")
        
        # Border for progress bar if background is light
        if is_light:
            self.progress_bar.set_border_color("black")
        else:
            self.progress_bar.set_border_color(None)

    def set_custom_overlay_path(self, path):
        self.custom_overlay_path = path

    def set_overlay(self, overlay_type):
        print(f"Setting overlay: {overlay_type}")
        if self.movie:
            self.movie.stop()
            self.movie = None
            
        if overlay_type == "None":
            self.overlay_widget.hide()
            self.overlay_widget.clear()
        elif overlay_type == "Black":
            self.overlay_widget.show()
            self.overlay_widget.setStyleSheet("background-color: black;")
            self.overlay_widget.clear()
            self.overlay_widget.raise_() # Bring to front
        elif overlay_type == "Cube":
            self.overlay_widget.show()
            self.overlay_widget.setStyleSheet("background-color: black;")
            self.load_gif("Background2.gif")
            self.overlay_widget.raise_()
        elif overlay_type == "Constructor":
            self.overlay_widget.show()
            self.overlay_widget.setStyleSheet("background-color: black;")
            self.load_gif("Background1.gif")
            self.overlay_widget.raise_()
        elif overlay_type == "Custom":
            self.overlay_widget.show()
            self.overlay_widget.setStyleSheet("background-color: black;")
            if self.custom_overlay_path and os.path.exists(self.custom_overlay_path):
                pixmap = QPixmap(self.custom_overlay_path)
                self.overlay_widget.setPixmap(pixmap.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.overlay_widget.clear()
            self.overlay_widget.raise_()
            
        # Ensure break timer is always on top of overlay
        if self.lbl_break_timer.isVisible():
            self.lbl_break_timer.raise_()
            
        # Ensure video is on top if visible
        if self.video_label.isVisible():
            self.video_label.raise_()

    def load_gif(self, filename):
        path = os.path.join(SCRIPT_DIR, "VisualTab", filename)
        print(f"Loading GIF from: {path}")
        if os.path.exists(path):
            self.movie = QMovie(path)
            self.overlay_widget.setMovie(self.movie)
            self.movie.start()
            self.scale_movie() # Initial scale
        else:
            print(f"GIF not found: {path}")

    def scale_movie(self):
        if not self.movie:
            return
        original_size = self.movie.frameRect().size()
        if original_size.isEmpty():
            return
        scaled_size = original_size.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.movie.setScaledSize(scaled_size)

    def update_break_timer(self, time_str):
        self.lbl_break_timer.setText(time_str)
        self.lbl_break_timer.adjustSize()
        self.position_break_timer()

    def show_break_timer(self, show):
        if show:
            self.lbl_break_timer.show()
            self.lbl_break_timer.raise_()
            self.position_break_timer()
        else:
            self.lbl_break_timer.hide()
            
    def position_break_timer(self):
        # Position in bottom right corner with margin
        margin = 20
        x = self.width() - self.lbl_break_timer.width() - margin
        y = self.height() - self.lbl_break_timer.height() - margin
        self.lbl_break_timer.move(x, y)

    def show_video(self, show):
        if show:
            self.video_label.show()
            self.video_label.raise_()
            self.video_label.resize(self.size())
        else:
            self.video_label.hide()
            self.video_label.clear()

    def set_video_frame(self, image):
        if self.video_label.isVisible():
            pixmap = QPixmap.fromImage(image)
            self.video_label.setPixmap(pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def set_orange_level_image(self, image_data):
        try:
            if isinstance(image_data, str) and image_data == "None":
                self.is_orange_mode = False
                self.orange_level_widget.hide()
                self.orange_level_widget.setPixmap(None)
                self.orange_pixmap = None
                
                # Restore normal layout
                self.lbl_title.show()
                self.lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 150))
                self.progress_bar.show()
                self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.main_layout.setContentsMargins(50, 50, 50, 50)
                
            elif isinstance(image_data, QPixmap):
                self.is_orange_mode = True
                self.orange_pixmap = image_data
                self.orange_level_widget.setPixmap(self.orange_pixmap)
                self.orange_level_widget.show()
                
                # Switch to compact layout
                self.lbl_title.hide()
                self.lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 40))
                self.progress_bar.hide()
                
                self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                self.main_layout.setContentsMargins(20, 20, 20, 20)
                
            else:
                # Assume filename string
                filename = image_data
                # Check if filename is absolute or relative
                if os.path.isabs(filename):
                    path = filename
                else:
                    # Try VisualTab first (legacy)
                    path = os.path.join(SCRIPT_DIR, "VisualTab", filename)
                    if not os.path.exists(path):
                        # Try OrangeLVL
                        path = os.path.join(ORANGE_LVL_DIR, filename)
                
                if os.path.exists(path):
                    self.is_orange_mode = True
                    self.orange_pixmap = QPixmap(path)
                    self.orange_level_widget.setPixmap(self.orange_pixmap)
                    self.orange_level_widget.show()
                    
                    # Switch to compact layout
                    self.lbl_title.hide()
                    self.lbl_time.setFont(QFont(FONT_FAMILY_REGULAR, 40))
                    self.progress_bar.hide()
                    
                    self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
                    self.main_layout.setContentsMargins(20, 20, 20, 20)
                else:
                    print(f"Image not found: {path}")
        except Exception as e:
            print(f"Error setting orange level image: {e}")

    def resizeEvent(self, event):
        self.overlay_widget.resize(event.size())
        
        # Rescale custom image if present
        if self.overlay_widget.isVisible() and self.custom_overlay_path and not self.movie:
             if os.path.exists(self.custom_overlay_path):
                pixmap = QPixmap(self.custom_overlay_path)
                self.overlay_widget.setPixmap(pixmap.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))

        self.video_label.resize(event.size())
        self.scale_movie()
        self.position_break_timer()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.window_closed.emit()
        super().closeEvent(event)


class Timer(QObject):
    time_updated = pyqtSignal(str)
    play_sound_signal = pyqtSignal(str)
    title_updated = pyqtSignal(str)
    confirm_end_sound_signal = pyqtSignal(str) # New signal for confirmation
    timer_window_state_changed = pyqtSignal(bool) # New signal for window state
    
    # Intro signals
    intro_finished = pyqtSignal()
    intro_position_changed = pyqtSignal(int, int) # position, duration
    stop_all_audio = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 5 * 3600
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.is_running = False
        self.is_paused = False
        self.is_muted = False
        self.timer_window = None
        self.title = "ОСТАТОЧНОЕ ВРЕМЯ ПОХОДА"
        
        self.sound_signals = {}
        self.last_sound_played_at = None # Track last sound to prevent looping
        
        # Special Effects
        self.red_effect_start_seconds = 600 # 10 minutes default
        self.blink_effect_start_seconds = 10 # 10 seconds default
        self.blink_state = True # Visible
        
        # Blink Timer (Independent from main timer for better visual effect)
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.on_blink_tick)
        self.blink_timer.setInterval(500) # 500ms blink interval
        
        # Break Timer Logic
        self.break_total_seconds = 600
        self.break_current_seconds = 600
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.update_break)
        self.break_running = False
        
        # Intro Logic
        self.intro_player = QMediaPlayer()
        self.intro_audio = QAudioOutput()
        self.intro_player.setAudioOutput(self.intro_audio)
        self.intro_video_sink = QVideoSink()
        self.intro_player.setVideoOutput(self.intro_video_sink)
        
        self.intro_player.mediaStatusChanged.connect(self.on_intro_status_changed)
        self.intro_player.positionChanged.connect(self.on_intro_position_changed)
        self.intro_player.durationChanged.connect(self.on_intro_duration_changed)
        self.intro_video_sink.videoFrameChanged.connect(self.on_video_frame_changed)

    def set_time(self, hours, minutes, seconds):
        self.total_seconds = hours * 3600 + minutes * 60 + seconds
        self.last_sound_played_at = None
        self._notify_update()

    def add_time(self, minutes):
        self.total_seconds += minutes * 60
        self.last_sound_played_at = None
        self._notify_update()

    def subtract_time(self, minutes):
        self.total_seconds -= minutes * 60
        if self.total_seconds < 0:
            self.total_seconds = 0
        self.last_sound_played_at = None
        self._notify_update()
        
    def set_red_effect_start(self, seconds):
        self.red_effect_start_seconds = seconds
        self._notify_update()
        
    def set_blink_effect_start(self, seconds):
        self.blink_effect_start_seconds = seconds
        self._notify_update()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            self.timer.start(1000)
            # Resume blinking if needed
            if self.total_seconds <= self.blink_effect_start_seconds:
                self.blink_timer.start()

    def pause(self):
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.timer.stop()
            # Stop blinking, ensure visible
            self.blink_timer.stop()
            self.blink_state = True
            self._notify_update()

    def resume(self):
        if self.is_running and self.is_paused:
            self.is_paused = False
            self.timer.start(1000)
            # Resume blinking if needed
            if self.total_seconds <= self.blink_effect_start_seconds:
                self.blink_timer.start()

    def stop(self):
        self.is_running = False
        self.is_paused = False
        self.timer.stop()
        self.total_seconds = 5 * 3600
        self.blink_state = True
        self.blink_timer.stop()
        self.last_sound_played_at = None
        self._notify_update()

    def set_muted(self, muted):
        self.is_muted = muted

    def set_title(self, title):
        self.title = title
        self.title_updated.emit(title)
        if self.timer_window:
            self.timer_window.set_title(title)

    def update(self):
        # Sound Logic: Play only if not played recently for this second
        if not self.is_muted and self.total_seconds in self.sound_signals:
            if self.total_seconds != self.last_sound_played_at:
                # Special case for 0 seconds
                if self.total_seconds == 0:
                    self.confirm_end_sound_signal.emit(self.sound_signals[0])
                else:
                    self.play_sound_signal.emit(self.sound_signals[self.total_seconds])

                self.last_sound_played_at = self.total_seconds

        if self.total_seconds > 0:
            self.total_seconds -= 1
        else:
            # If reached 0, we stop counting down but keep running for blink effect
            pass
        
        # Handle blinking activation
        if self.total_seconds <= self.blink_effect_start_seconds:
            if not self.blink_timer.isActive() and self.is_running and not self.is_paused:
                self.blink_timer.start()
        else:
            if self.blink_timer.isActive():
                self.blink_timer.stop()
            self.blink_state = True
        
        self._notify_update()

    def on_blink_tick(self):
        self.blink_state = not self.blink_state
        self._notify_update()

    def get_time_str(self):
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        seconds = self.total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _notify_update(self):
        time_str = self.get_time_str()
        self.time_updated.emit(time_str)
        
        # Calculate red ratio
        red_ratio = 0.0
        if self.total_seconds <= self.red_effect_start_seconds and self.red_effect_start_seconds > 0:
            red_ratio = 1.0 - (self.total_seconds / self.red_effect_start_seconds)
            if red_ratio < 0: red_ratio = 0
            if red_ratio > 1: red_ratio = 1
            
        if self.timer_window and self.timer_window.isVisible():
            self.timer_window.update_time(time_str, self.total_seconds, red_ratio, self.blink_state)

    def create_window(self):
        if not self.timer_window:
            self.timer_window = TimerWindow()
            self.timer_window.set_title(self.title)
            self.timer_window.window_closed.connect(self.on_window_closed)
        self.timer_window.show()
        self.timer_window.update_time(self.get_time_str(), self.total_seconds)
        self.timer_window_state_changed.emit(True)

    def on_window_closed(self):
        self.control_intro("stop")
        self.timer_window = None
        self.timer_window_state_changed.emit(False)

    def set_sound_signal(self, seconds, file_path):
        if file_path:
            self.sound_signals[seconds] = file_path
        elif seconds in self.sound_signals:
            del self.sound_signals[seconds]

    # --- Visual Tab Methods ---
    def set_background_color(self, color):
        if self.timer_window:
            self.timer_window.set_background_color(color)

    def set_overlay(self, overlay_type):
        if self.timer_window:
            self.timer_window.set_overlay(overlay_type)

    def set_custom_overlay(self, path):
        if self.timer_window:
            self.timer_window.set_custom_overlay_path(path)
            # If currently showing custom overlay, refresh it
            if self.timer_window.overlay_widget.isVisible() and not self.timer_window.movie:
                 # Check if we are in custom mode implicitly by checking if movie is None and widget visible
                 # But better to just re-trigger set_overlay if needed, or let user click radio button
                 pass

    def set_break_timer_state(self, enabled, total_seconds):
        self.break_total_seconds = total_seconds
        self.break_current_seconds = total_seconds
        if self.timer_window:
            self.timer_window.show_break_timer(enabled)
            self.timer_window.update_break_timer(self.get_break_time_str())
        
        if not enabled:
            self.break_timer.stop()
            self.break_running = False

    def control_break_timer(self, action):
        if action == "play":
            if not self.break_running:
                self.break_running = True
                self.break_timer.start(1000)
        elif action == "pause":
            if self.break_running:
                self.break_running = False
                self.break_timer.stop()
        elif action == "stop":
            self.break_running = False
            self.break_timer.stop()
            self.break_current_seconds = self.break_total_seconds
            if self.timer_window:
                self.timer_window.update_break_timer(self.get_break_time_str())

    def update_break(self):
        if self.break_current_seconds > 0:
            self.break_current_seconds -= 1
            if self.timer_window:
                self.timer_window.update_break_timer(self.get_break_time_str())
        else:
            self.break_timer.stop()
            self.break_running = False

    def get_break_time_str(self):
        minutes = self.break_current_seconds // 60
        seconds = self.break_current_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    # --- Intro Methods ---
    def set_intro_state(self, enabled):
        if enabled:
            path = os.path.join(SCRIPT_DIR, "VisualTab", "Intro.mp4")
            if os.path.exists(path):
                self.intro_player.setSource(QUrl.fromLocalFile(path))
                if self.timer_window:
                    self.timer_window.show_video(True)
            else:
                print(f"Intro video not found: {path}")
        else:
            self.intro_player.stop()
            if self.timer_window:
                self.timer_window.show_video(False)

    def control_intro(self, action):
        if action == "play":
            self.stop_all_audio.emit()
            self.intro_player.play()
        elif action == "pause":
            self.intro_player.pause()
        elif action == "stop":
            self.intro_player.stop()
            self.intro_player.setPosition(0)

    def seek_intro(self, position):
        self.intro_player.setPosition(position)
        
    def set_intro_volume(self, value):
        self.intro_audio.setVolume(value / 100.0)

    def on_intro_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.set_intro_state(False)
            self.intro_finished.emit()

    def on_intro_position_changed(self, position):
        self.intro_position_changed.emit(position, self.intro_player.duration())

    def on_intro_duration_changed(self, duration):
        self.intro_position_changed.emit(self.intro_player.position(), duration)

    def on_video_frame_changed(self, frame):
        if self.timer_window:
            image = frame.toImage()
            self.timer_window.set_video_frame(image)

    def set_orange_level_image(self, image_data):
        if self.timer_window:
            self.timer_window.set_orange_level_image(image_data)
