from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, 
                             QPushButton, QHBoxLayout, QLineEdit, QScrollArea, QFrame, QFileDialog, QGridLayout, QGroupBox, QStyleOptionButton, QRadioButton,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, QRect, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPalette, QTextDocument, QTextOption, QFontMetrics, QIcon, QIntValidator
from config import FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, AUDIO_PANEL_SOUNDS_DIR, TIMER_SOUNDS_DIR, OUTER_CONTOUR_COORDS, SCRIPT_DIR, PLAYER_BUTTONS_DIR
from MusicPlayer import MusicPlayer
from VisualTab import VisualTab
from Syntez import SynthesizerTab
from widgets import WrappingButton
import os
import random

class TimeInput(QLineEdit):
    def __init__(self, default_value="00", max_val=None, width=60, height=40, parent=None):
        super().__init__(default_value, parent)
        self.max_val = max_val
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMaxLength(2)
        self.setValidator(QIntValidator(0, 99))
        
        # Style
        self.setFont(QFont(FONT_FAMILY_REGULAR, 20))
        self.setFixedSize(width, height)
        
        self.editingFinished.connect(self.on_editing_finished)

    def focusInEvent(self, event):
        if self.text() == "0" or self.text() == "00":
            self.clear()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.on_editing_finished()

    def on_editing_finished(self):
        text = self.text()
        if not text:
            self.setText("00")
            return

        try:
            val = int(text)
            if self.max_val is not None and val > self.max_val:
                val = self.max_val
            self.setText(f"{val:02d}")
        except ValueError:
            self.setText("00")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            if self.cursorPosition() == 0:
                self.focusPreviousChild()
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Right:
            if self.cursorPosition() == len(self.text()):
                self.focusNextChild()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

class DiceResultWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_results(self, results):
        self.results = results
        self.updateGeometry() # Important to re-calculate height
        self.update()

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        if not self.results:
            return 30 # Minimum height when empty

        dice_size = 40
        spacing = 10
        
        x = 0
        y = 10
        line_height = dice_size + spacing
        
        for _ in self.results:
            if x > 0 and x + dice_size > width:
                x = 0
                y += line_height
            x += dice_size + spacing
            
        return y + dice_size + 10

    def paintEvent(self, event):
        if not self.results:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        dice_size = 40
        spacing = 10
        
        x = 0
        y = 10
        line_height = dice_size + spacing
        
        for result in self.results:
            if x > 0 and x + dice_size > self.width():
                x = 0
                y += line_height
                
            rect = QRectF(x, y, dice_size, dice_size)
            
            painter.setBrush(QBrush(QColor("white")))
            painter.setPen(QPen(QColor("black"), 2))
            painter.drawRoundedRect(rect, 5, 5)
            
            dot_size = 8
            painter.setBrush(QBrush(QColor("black")))
            painter.setPen(Qt.PenStyle.NoPen)
            
            if result == 4 or result == 5:
                painter.drawEllipse(rect.center(), dot_size/2, dot_size/2)
            elif result == 6:
                painter.drawEllipse(QPointF(x + dice_size*0.25, y + dice_size*0.75), dot_size/2, dot_size/2)
                painter.drawEllipse(QPointF(x + dice_size*0.75, y + dice_size*0.25), dot_size/2, dot_size/2)
            
            x += dice_size + spacing

class ManagementTab(QWidget):
    white_room_move_requested = pyqtSignal(bool, bool) # (clockwise, with_sound)

    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self.timer = timer
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- TIMER SECTION ---
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
        layout.addWidget(timer_group)
        
        # --- SOUND SIGNALS SECTION ---
        sound_group = QGroupBox("ЗВУКОВЫЕ СИГНАЛЫ")
        sound_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        sound_layout = QGridLayout()
        
        btn_error = WrappingButton("//ОШИБКА//")
        btn_error.setMinimumHeight(60)
        btn_error.setStyleSheet("background-color: black; color: red; font-weight: bold;")
        btn_error.clicked.connect(lambda: self.play_sound("Error.wav"))
        sound_layout.addWidget(btn_error, 0, 0)
        
        btn_complete = WrappingButton("Испытание\nзавершено")
        btn_complete.setMinimumHeight(60)
        btn_complete.setStyleSheet("background-color: #008000; color: white; font-weight: bold;")
        btn_complete.clicked.connect(lambda: self.play_sound("ChallengeComplete.wav"))
        sound_layout.addWidget(btn_complete, 0, 1)
        
        btn_begin = WrappingButton("Вступление")
        btn_begin.setMinimumHeight(60)
        btn_begin.setStyleSheet("background-color: #ffff00; color: black; font-weight: bold;")
        btn_begin.clicked.connect(lambda: self.play_sound("Beginning.wav"))
        sound_layout.addWidget(btn_begin, 1, 0)
        
        btn_vote = WrappingButton("Начать\nголосование")
        btn_vote.setMinimumHeight(60)
        btn_vote.clicked.connect(lambda: self.play_sound("Voting.wav"))
        sound_layout.addWidget(btn_vote, 1, 1)
        
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        # --- WHITE ROOM MOVEMENT SECTION ---
        move_group = QGroupBox("ПЕРЕМЕЩЕНИЕ БЕЛОЙ ЗАЛЫ")
        move_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        move_layout = QVBoxLayout()
        
        # Top row buttons
        top_btns_layout = QHBoxLayout()
        
        self.btn_white_move = WrappingButton("Белая зала\nперемещается")
        self.btn_white_move.setMinimumHeight(60)
        self.btn_white_move.setStyleSheet("""
            QPushButton { background-color: white; color: black; font-weight: bold; }
            QPushButton:disabled { background-color: #a5a5a5; color: #242424; }
        """)
        self.btn_white_move.clicked.connect(lambda: self.on_white_move_click(True))
        top_btns_layout.addWidget(self.btn_white_move)
        
        self.btn_silent_move = WrappingButton("Перемещение\n(без звука)")
        self.btn_silent_move.setMinimumHeight(60)
        self.btn_silent_move.clicked.connect(lambda: self.on_white_move_click(False))
        top_btns_layout.addWidget(self.btn_silent_move)
        
        move_layout.addLayout(top_btns_layout)
        
        # Bottom row buttons
        bottom_btns_layout = QHBoxLayout()
        
        btn_to_orange = WrappingButton("На оранжевый\nуровень")
        btn_to_orange.setMinimumHeight(60)
        btn_to_orange.setStyleSheet("background-color: #ed7d31; color: white; font-weight: bold;")
        btn_to_orange.clicked.connect(lambda: self.play_white_room_sound("Перем - оранжевый.wav"))
        bottom_btns_layout.addWidget(btn_to_orange)
        
        btn_to_grey = WrappingButton("На серый\nуровень")
        btn_to_grey.setMinimumHeight(60)
        btn_to_grey.setStyleSheet("background-color: #666666; color: white; font-weight: bold;")
        btn_to_grey.clicked.connect(lambda: self.play_white_room_sound("Перем - серый.wav"))
        bottom_btns_layout.addWidget(btn_to_grey)
        
        btn_to_purple = WrappingButton("На фиолетовый\nуровень")
        btn_to_purple.setMinimumHeight(60)
        btn_to_purple.setStyleSheet("background-color: #785dc8; color: white; font-weight: bold;")
        btn_to_purple.clicked.connect(lambda: self.play_white_room_sound("Перем - фиолетовый.wav"))
        bottom_btns_layout.addWidget(btn_to_purple)
        
        move_layout.addLayout(bottom_btns_layout)
        
        radio_layout = QHBoxLayout()
        self.radio_cw = QRadioButton("По часовой стрелке")
        self.radio_ccw = QRadioButton("Против часовой стрелки")
        self.radio_cw.setChecked(True)
        self.radio_cw.setEnabled(False)
        self.radio_ccw.setEnabled(False)
        
        radio_layout.addWidget(self.radio_cw)
        radio_layout.addWidget(self.radio_ccw)
        move_layout.addLayout(radio_layout)
        
        move_group.setLayout(move_layout)
        layout.addWidget(move_group)
        
        # --- GREETING SECTION ---
        greet_group = QGroupBox("ПРИВЕТСТВИЕ")
        greet_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        greet_layout = QHBoxLayout()
        
        btn_orange = WrappingButton("Оранжевый уровень")
        btn_orange.setStyleSheet("background-color: #ed7d31; color: white; font-weight: bold;")
        btn_orange.clicked.connect(lambda: self.play_sound("Оранжевый.wav"))
        greet_layout.addWidget(btn_orange)
        
        btn_purple = WrappingButton("Фиолетовый уровень")
        btn_purple.setStyleSheet("background-color: #785dc8; color: white; font-weight: bold;")
        btn_purple.clicked.connect(lambda: self.play_sound("Фиолетовый.wav"))
        greet_layout.addWidget(btn_purple)
        
        greet_group.setLayout(greet_layout)
        layout.addWidget(greet_group)
        
        # --- VOTING SECTION ---
        vote_group = QGroupBox("ГОЛОСОВАНИЕ")
        vote_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        vote_layout = QGridLayout()
        
        vote_buttons = [
            ("Кровь", "Кровь.wav"), ("Луна", "Луна.wav"), ("Твердь", "Твердь.wav"), ("Пепел", "Пепел.wav"),
            ("Небо", "Небо.wav"), ("Солнце", "Солнце.wav"), ("Пустота", "Пустота.wav")
        ]
        
        for i, (name, file) in enumerate(vote_buttons):
            btn = WrappingButton(name)
            btn.clicked.connect(lambda checked, f=file: self.play_sound(f))
            vote_layout.addWidget(btn, i // 4, i % 4)
            
        btn_reward = WrappingButton("Великая награда\nпокровительства")
        btn_reward.clicked.connect(lambda: self.play_sound("ВеликаяНаграда.wav"))
        vote_layout.addWidget(btn_reward, 2, 0, 1, 4)
        
        vote_group.setLayout(vote_layout)
        layout.addWidget(vote_group)
        
        # --- DICE ROLL SECTION ---
        dice_group = QGroupBox("БРОСОК КУБИКОВ")
        dice_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        dice_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        self.btn_minus = WrappingButton("-")
        self.btn_minus.setFixedSize(40, 40)
        self.btn_minus.clicked.connect(self.dec_dice)
        
        self.input_dice_count = QLineEdit("1")
        self.input_dice_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_dice_count.setFont(QFont(FONT_FAMILY_BOLD, 16))
        self.input_dice_count.setFixedSize(60, 40)
        
        self.btn_plus = WrappingButton("+")
        self.btn_plus.setFixedSize(40, 40)
        self.btn_plus.clicked.connect(self.inc_dice)
        
        self.btn_roll = WrappingButton("Бросок")
        self.btn_roll.setFixedHeight(40)
        self.btn_roll.clicked.connect(self.roll_dice)
        
        input_layout.addWidget(self.btn_minus)
        input_layout.addWidget(self.input_dice_count)
        input_layout.addWidget(self.btn_plus)
        input_layout.addSpacing(20)
        input_layout.addWidget(self.btn_roll)
        dice_layout.addLayout(input_layout)
        
        self.dice_results_widget = DiceResultWidget()
        dice_layout.addWidget(self.dice_results_widget)
        
        self.lbl_success = QLabel("Успехов: 0")
        self.lbl_success.setFont(QFont(FONT_FAMILY_BOLD, 12))
        dice_layout.addWidget(self.lbl_success)
        
        dice_group.setLayout(dice_layout)
        layout.addWidget(dice_group)
        
        layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setLayout(layout)
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def on_white_move_click(self, with_sound):
        clockwise = self.radio_cw.isChecked()
        self.white_room_move_requested.emit(clockwise, with_sound)

    def update_white_room_controls(self, cell_data):
        has_white_room = False
        for coord in OUTER_CONTOUR_COORDS:
            if coord in cell_data and cell_data[coord].get('room_type') == 'Белая зала':
                has_white_room = True
                break
        
        self.radio_cw.setEnabled(has_white_room)
        self.radio_ccw.setEnabled(has_white_room)
        self.btn_white_move.setEnabled(has_white_room)
        self.btn_silent_move.setEnabled(has_white_room)

    def dec_dice(self):
        try:
            count = int(self.input_dice_count.text())
            if count > 1:
                self.input_dice_count.setText(str(count - 1))
        except ValueError:
            self.input_dice_count.setText("1")

    def inc_dice(self):
        try:
            count = int(self.input_dice_count.text())
            if count < 12:
                self.input_dice_count.setText(str(count + 1))
        except ValueError:
            self.input_dice_count.setText("1")

    def roll_dice(self):
        try:
            count = int(self.input_dice_count.text())
            if not (1 <= count <= 12):
                count = 1
                self.input_dice_count.setText("1")
        except ValueError:
            count = 1
            self.input_dice_count.setText("1")
            
        results = [random.randint(1, 6) for _ in range(count)]
        self.dice_results_widget.set_results(results)
        
        successes = 0
        for r in results:
            if r == 4 or r == 5:
                successes += 1
            elif r == 6:
                successes += 2
                
        self.lbl_success.setText(f"Успехов: {successes}")

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

    def play_sound(self, filename):
        path = os.path.join(AUDIO_PANEL_SOUNDS_DIR, filename)
        if os.path.exists(path):
            self.timer.play_sound_signal.emit(path)
        else:
            print(f"Sound not found: {path}")

    def play_white_room_sound(self, filename):
        # Sounds are in WhiteRoomMove folder
        path = os.path.join(SCRIPT_DIR, "WhiteRoomMove", filename)
        if os.path.exists(path):
            self.timer.play_sound_signal.emit(path)
        else:
            print(f"Sound not found: {path}")

class TimerTab(QWidget):
    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self.timer = timer
        self.sound_inputs = {}
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- TITLE SECTION ---
        title_group = QGroupBox("ЗАГОЛОВОК ТАЙМЕРА")
        title_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        title_layout = QVBoxLayout()
        
        self.input_title = QLineEdit("ОСТАТОЧНОЕ ВРЕМЯ ПОХОДА")
        self.input_title.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        self.input_title.textChanged.connect(self.timer.set_title)
        title_layout.addWidget(self.input_title)
        
        title_group.setLayout(title_layout)
        layout.addWidget(title_group)
        
        # --- TIME SETTINGS ---
        time_group = QGroupBox("НАСТРОЙКА ВРЕМЕНИ")
        time_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        time_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        self.input_h = TimeInput("05")
        self.input_m = TimeInput("00", max_val=59)
        self.input_s = TimeInput("00", max_val=59)
        
        input_layout.addStretch()
        input_layout.addWidget(self.input_h)
        input_layout.addWidget(QLabel(":"))
        input_layout.addWidget(self.input_m)
        input_layout.addWidget(QLabel(":"))
        input_layout.addWidget(self.input_s)
        input_layout.addStretch()
        time_layout.addLayout(input_layout)
        
        btn_layout = QHBoxLayout()
        btn_apply = WrappingButton("Применить настройку")
        btn_apply.clicked.connect(self.apply_time)
        btn_reset = WrappingButton("⟳")
        btn_reset.setFixedWidth(40)
        btn_reset.clicked.connect(self.reset_inputs)
        
        btn_layout.addWidget(btn_apply)
        btn_layout.addWidget(btn_reset)
        time_layout.addLayout(btn_layout)
        
        # --- ADDED: Timer Controls (Start/Stop/Adjust) ---
        controls_layout = QHBoxLayout()
        self.btn_start = WrappingButton("Запуск")
        self.btn_start.setStyleSheet("background-color: #70ad47; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.on_start_pause)
        
        self.btn_stop = WrappingButton("Стоп")
        self.btn_stop.setStyleSheet("background-color: #c83232; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.on_stop)
        
        controls_layout.addWidget(self.btn_start)
        controls_layout.addWidget(self.btn_stop)
        time_layout.addLayout(controls_layout)
        
        # Time Adjustments
        time_adj_layout = QGridLayout()
        times = [5, 10, 15, 30, 60]
        for i, mins in enumerate(times):
            btn_plus = WrappingButton(f"+{mins} мин")
            btn_plus.clicked.connect(lambda checked, m=mins: self.timer.add_time(m))
            time_adj_layout.addWidget(btn_plus, 0, i)
            
            btn_minus = WrappingButton(f"-{mins} мин")
            btn_minus.clicked.connect(lambda checked, m=mins: self.timer.subtract_time(m))
            time_adj_layout.addWidget(btn_minus, 1, i)
            
        time_layout.addLayout(time_adj_layout)
        
        time_group.setLayout(time_layout)
        layout.addWidget(time_group)
        
        # --- SPECIAL EFFECTS ---
        sfx_group = QGroupBox("СПЕЦЭФФЕКТЫ")
        sfx_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        sfx_layout = QGridLayout()
        
        sfx_layout.addWidget(QLabel("Начало краснения:"), 0, 0)
        self.red_h = TimeInput("00", width=40)
        self.red_m = TimeInput("10", max_val=59, width=40)
        self.red_s = TimeInput("00", max_val=59, width=40)
        sfx_layout.addWidget(self.red_h, 0, 1); sfx_layout.addWidget(self.red_m, 0, 2); sfx_layout.addWidget(self.red_s, 0, 3)
        
        btn_apply_red = WrappingButton("Применить")
        btn_apply_red.clicked.connect(self.apply_red_effect)
        sfx_layout.addWidget(btn_apply_red, 0, 4)
        
        sfx_layout.addWidget(QLabel("Начало моргания:"), 1, 0)
        self.blink_h = TimeInput("00", width=40)
        self.blink_m = TimeInput("00", max_val=59, width=40)
        self.blink_s = TimeInput("10", max_val=59, width=40)
        sfx_layout.addWidget(self.blink_h, 1, 1); sfx_layout.addWidget(self.blink_m, 1, 2); sfx_layout.addWidget(self.blink_s, 1, 3)
        
        btn_apply_blink = WrappingButton("Применить")
        btn_apply_blink.clicked.connect(self.apply_blink_effect)
        sfx_layout.addWidget(btn_apply_blink, 1, 4)
        
        sfx_group.setLayout(sfx_layout)
        layout.addWidget(sfx_group)
        
        # --- SOUND SIGNALS ---
        sound_group = QGroupBox("ЗВУКОВЫЕ СИГНАЛЫ")
        sound_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        sound_layout = QGridLayout()
        
        # Mute button row
        mute_layout = QHBoxLayout()
        mute_layout.addStretch()
        self.btn_mute = QPushButton()
        self.btn_mute.setFixedSize(30, 30)
        self.btn_mute.setStyleSheet("background-color: transparent; border: none;")
        self.btn_mute.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, "SoundLoud.png")))
        self.btn_mute.setIconSize(QSize(24, 24))
        self.btn_mute.clicked.connect(self.toggle_mute)
        mute_layout.addWidget(self.btn_mute)
        
        sound_layout.addLayout(mute_layout, 0, 0, 1, 5) # Span across all columns
        
        signals = [
            ("5 часов", 5*3600), ("4 часа", 4*3600), ("3 часа", 3*3600), ("2 часа", 2*3600), ("1 час", 3600),
            ("30 минут", 1800), ("15 минут", 900), ("10 минут", 600), ("5 минут", 300), ("1 минута", 60), ("Конец", 0)
        ]
        
        for i, (label, seconds) in enumerate(signals):
            row = i + 1 # Shift down by 1 because of mute button
            sound_layout.addWidget(QLabel(label), row, 0)
            
            inp = QLineEdit()
            inp.setReadOnly(True)
            self.sound_inputs[seconds] = inp
            
            # Try to load default
            default_path = os.path.join(TIMER_SOUNDS_DIR, f"{label}.wav")
            if os.path.exists(default_path):
                inp.setText(os.path.basename(default_path))
                self.timer.set_sound_signal(seconds, default_path)
            
            sound_layout.addWidget(inp, row, 1)
            
            btn_add = WrappingButton("+")
            btn_add.setFixedWidth(30)
            btn_add.clicked.connect(lambda checked, s=seconds: self.add_sound(s))
            sound_layout.addWidget(btn_add, row, 2)
            
            btn_clear = WrappingButton("x")
            btn_clear.setFixedWidth(30)
            btn_clear.clicked.connect(lambda checked, s=seconds: self.clear_sound(s))
            sound_layout.addWidget(btn_clear, row, 3)
            
            btn_play = WrappingButton("▶")
            btn_play.setFixedWidth(30)
            btn_play.clicked.connect(lambda checked, s=seconds: self.play_preview(s))
            sound_layout.addWidget(btn_play, row, 4)
            
        sound_group.setLayout(sound_layout)
        layout.addWidget(sound_group)
        
        layout.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setLayout(layout)
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def apply_time(self):
        try:
            h = int(self.input_h.text())
            m = int(self.input_m.text())
            s = int(self.input_s.text())
            self.timer.set_time(h, m, s)
        except ValueError:
            pass

    def reset_inputs(self):
        self.input_h.setText("00")
        self.input_m.setText("00")
        self.input_s.setText("00")

    def apply_red_effect(self):
        try:
            h = int(self.red_h.text())
            m = int(self.red_m.text())
            s = int(self.red_s.text())
            total_seconds = h * 3600 + m * 60 + s
            self.timer.set_red_effect_start(total_seconds)
        except ValueError:
            pass

    def apply_blink_effect(self):
        try:
            h = int(self.blink_h.text())
            m = int(self.blink_m.text())
            s = int(self.blink_s.text())
            total_seconds = h * 3600 + m * 60 + s
            self.timer.set_blink_effect_start(total_seconds)
        except ValueError:
            pass

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

    def add_sound(self, seconds):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "Audio (*.wav *.mp3)")
        if file_path:
            self.sound_inputs[seconds].setText(os.path.basename(file_path))
            self.timer.set_sound_signal(seconds, file_path)

    def clear_sound(self, seconds):
        self.sound_inputs[seconds].clear()
        self.timer.set_sound_signal(seconds, None)

    def play_preview(self, seconds):
        if seconds in self.timer.sound_signals:
            path = self.timer.sound_signals[seconds]
            self.timer.play_sound_signal.emit(path)

    def toggle_mute(self):
        is_muted = not self.timer.is_muted
        self.timer.set_muted(is_muted)
        
        icon_name = "SoundOff.png" if is_muted else "SoundLoud.png"
        self.btn_mute.setIcon(QIcon(os.path.join(PLAYER_BUTTONS_DIR, icon_name)))

class PanelC(QWidget):
    white_room_move_requested = pyqtSignal(bool, bool)
    intro_volume_changed = pyqtSignal(int)

    def __init__(self, timer, parent=None):
        super().__init__(parent)
        self.timer = timer
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Timer Display
        self.lbl_timer_display = QLabel("Остаточное время похода: 05:00:00")
        self.lbl_timer_display.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        self.lbl_timer_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_timer_display)
        
        # Tabs
        self.tabs = QTabWidget()
        self.management_tab = ManagementTab(self.timer)
        self.management_tab.white_room_move_requested.connect(self.white_room_move_requested.emit)
        
        self.visual_tab = VisualTab(self.timer)
        self.visual_tab.background_color_changed.connect(self.timer.set_background_color)
        self.visual_tab.overlay_changed.connect(self.timer.set_overlay)
        self.visual_tab.custom_overlay_changed.connect(self.timer.set_custom_overlay)
        self.visual_tab.break_timer_state_changed.connect(self.timer.set_break_timer_state)
        self.visual_tab.break_timer_control.connect(self.timer.control_break_timer)
        self.visual_tab.intro_state_changed.connect(self.timer.set_intro_state)
        self.visual_tab.intro_control.connect(self.timer.control_intro)
        self.visual_tab.intro_seek.connect(self.timer.seek_intro)
        self.visual_tab.intro_volume_changed.connect(self.intro_volume_changed.emit)
        # self.visual_tab.orange_level_changed.connect(self.timer.set_orange_level_image) # REMOVED
        self.visual_tab.open_timer_window_requested.connect(self.timer.create_window)
        
        self.synthesizer_tab = SynthesizerTab()
        
        self.tabs.addTab(self.management_tab, "Управление")
        self.tabs.addTab(TimerTab(self.timer), "Таймер")
        self.tabs.addTab(MusicPlayer(), "Плеер")
        self.tabs.addTab(self.visual_tab, "Визуал")
        self.tabs.addTab(self.synthesizer_tab, "Синтезатор")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
        self.timer.time_updated.connect(self.update_timer_display)
        self.timer.intro_finished.connect(self.visual_tab.intro_finished)
        self.timer.intro_position_changed.connect(lambda pos, dur: self.visual_tab.update_intro_slider(pos, dur))
        self.intro_volume_changed.connect(self.timer.set_intro_volume)

    def update_timer_display(self, time_str):
        self.lbl_timer_display.setText(f"Остаточное время похода: {time_str}")

    def update_white_room_controls(self, cell_data):
        self.management_tab.update_white_room_controls(cell_data)

    def start_preview_timer(self):
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(50) # ~20 FPS

    def update_preview(self):
        if self.timer and self.timer.timer_window and self.timer.timer_window.isVisible():
            pixmap = self.timer.timer_window.grab()
            self.visual_tab.update_preview(pixmap)
        else:
            self.visual_tab.update_preview(None)
