import os
import asyncio
import tempfile
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QTextEdit, QSlider, QSpinBox, QPushButton, QFileDialog, 
                             QMessageBox, QGroupBox, QProgressBar, QLineEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import edge_tts

from config import FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, PLAYER_BUTTONS_DIR, SYNTH_SPEECH_DIR

# Доступные голоса (можно расширить список)
VOICES = {
    "Дмитрий (Russian)": "ru-RU-DmitryNeural",
    "Светлана (Russian)": "ru-RU-SvetlanaNeural",
    "Guy (English)": "en-US-GuyNeural",
    "Jenny (English)": "en-US-JennyNeural"
}

class TTSWorker(QThread):
    """Поток для асинхронной генерации речи"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, text, voice, pitch_shift, output_file=None):
        super().__init__()
        self.text = text
        self.voice = voice
        self.pitch_shift = pitch_shift # int 0 to 200 representing percentage drop
        self.output_file = output_file

    def run(self):
        try:
            # Создаем новый цикл событий для этого потока
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.generate())
            loop.close()
        except Exception as e:
            self.error.emit(str(e))

    async def generate(self):
        # Формируем параметр pitch. 
        # 0% на слайдере = 0Hz (нормальный голос)
        # 100% на слайдере = -50Hz
        # 200% на слайдере = -100Hz
        
        hz_shift = int(self.pitch_shift / 2) 
        pitch_str = f"-{hz_shift}Hz" if hz_shift > 0 else "+0Hz"
        
        communicate = edge_tts.Communicate(self.text, self.voice, pitch=pitch_str)
        
        if self.output_file:
            final_path = self.output_file
        else:
            # Временный файл для превью
            temp_dir = tempfile.gettempdir()
            final_path = os.path.join(temp_dir, "preview_tts.mp3")

        await communicate.save(final_path)
        self.finished.emit(final_path)


class SynthesizerTab(QWidget):
    # Сигнал отправляется, когда файл успешно создан для привязки к ячейке
    # (путь_к_файлу, координата_строкой)
    audio_assigned = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Заголовок ---
        lbl_title = QLabel("СИНТЕЗАТОР РЕЧИ")
        lbl_title.setFont(QFont(FONT_FAMILY_BOLD, 24))
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # --- Выбор голоса ---
        voice_layout = QHBoxLayout()
        lbl_voice = QLabel("Голос:")
        lbl_voice.setFont(QFont(FONT_FAMILY_BOLD, 12))
        
        self.combo_voice = QComboBox()
        self.combo_voice.addItems(VOICES.keys())
        self.combo_voice.setCurrentText("Дмитрий (Russian)") # По умолчанию
        self.combo_voice.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        
        voice_layout.addWidget(lbl_voice)
        voice_layout.addWidget(self.combo_voice, 1)
        layout.addLayout(voice_layout)

        # --- Текстовое поле ---
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Введите текст для озвучивания...")
        self.text_input.setFont(QFont(FONT_FAMILY_REGULAR, 12))
        self.text_input.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #cccccc;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.text_input)

        # --- Настройка тона ---
        tone_group = QGroupBox("Настройка голоса")
        tone_group.setFont(QFont(FONT_FAMILY_BOLD, 10))
        tone_layout = QHBoxLayout(tone_group)
        
        lbl_tone = QLabel("Понижение тона (%):")
        
        self.slider_tone = QSlider(Qt.Orientation.Horizontal)
        self.slider_tone.setRange(0, 200) 
        self.slider_tone.setValue(110) # Default 110%
        
        self.spin_tone = QSpinBox()
        self.spin_tone.setRange(0, 200) 
        self.spin_tone.setValue(110) # Default 110%
        self.spin_tone.setFixedWidth(60)
        
        # Связь слайдера и спинбокса
        self.slider_tone.valueChanged.connect(self.spin_tone.setValue)
        self.spin_tone.valueChanged.connect(self.slider_tone.setValue)
        
        tone_layout.addWidget(lbl_tone)
        tone_layout.addWidget(self.slider_tone)
        tone_layout.addWidget(self.spin_tone)
        
        layout.addWidget(tone_group)

        # --- Кнопки управления (Play / Save) ---
        controls_layout = QHBoxLayout()
        
        # Кнопка Play
        self.btn_play = QPushButton()
        self.btn_play.setFixedSize(50, 50)
        icon_path = os.path.join(PLAYER_BUTTONS_DIR, "play.png")
        if os.path.exists(icon_path):
            self.btn_play.setIcon(QIcon(icon_path))
            self.btn_play.setIconSize(QSize(32, 32))
        else:
            self.btn_play.setText("▶")
            
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #4472c4;
                border-radius: 25px;
                border: 2px solid #5582d4;
            }
            QPushButton:hover {
                background-color: #5582d4;
            }
            QPushButton:disabled {
                background-color: #333;
                border-color: #555;
            }
        """)
        self.btn_play.clicked.connect(self.on_play_clicked)
        
        # Кнопка Сохранить
        self.btn_save = QPushButton("Сохранить как...")
        self.btn_save.setFixedHeight(50)
        self.btn_save.setFont(QFont(FONT_FAMILY_BOLD, 12))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        self.btn_save.clicked.connect(self.on_save_clicked)
        
        controls_layout.addWidget(self.btn_play)
        controls_layout.addSpacing(20)
        controls_layout.addWidget(self.btn_save, 1)
        
        layout.addLayout(controls_layout)
        
        # --- Назначение на ячейку ---
        assign_layout = QHBoxLayout()
        
        lbl_assign = QLabel("Назначить на ячейку:")
        lbl_assign.setFont(QFont(FONT_FAMILY_BOLD, 12))
        
        self.input_cell = QLineEdit()
        self.input_cell.setPlaceholderText("A2")
        self.input_cell.setFixedWidth(60)
        self.input_cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_cell.setFont(QFont(FONT_FAMILY_BOLD, 12))
        self.input_cell.setStyleSheet("padding: 5px;")
        
        self.btn_assign = QPushButton("Применить")
        self.btn_assign.setFixedHeight(40)
        self.btn_assign.setFont(QFont(FONT_FAMILY_BOLD, 11))
        self.btn_assign.setStyleSheet("""
            QPushButton {
                background-color: #70ad47;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #7ec252;
            }
        """)
        self.btn_assign.clicked.connect(self.on_assign_clicked)
        
        assign_layout.addWidget(lbl_assign)
        assign_layout.addWidget(self.input_cell)
        assign_layout.addWidget(self.btn_assign)
        assign_layout.addStretch()
        
        layout.addLayout(assign_layout)
        
        # Прогресс бар (скрытый по умолчанию)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Бесконечный прогресс
        self.progress.hide()
        self.progress.setStyleSheet("QProgressBar { height: 5px; background: #333; border: none; } QProgressBar::chunk { background: #4472c4; }")
        layout.addWidget(self.progress)
        
        layout.addStretch()

    def get_selected_voice_id(self):
        name = self.combo_voice.currentText()
        return VOICES.get(name, "ru-RU-DmitryNeural")

    def set_loading(self, loading):
        if loading:
            self.btn_play.setEnabled(False)
            self.btn_save.setEnabled(False)
            self.btn_assign.setEnabled(False)
            self.progress.show()
        else:
            self.btn_play.setEnabled(True)
            self.btn_save.setEnabled(True)
            self.btn_assign.setEnabled(True)
            self.progress.hide()

    def on_play_clicked(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Внимание", "Введите текст для озвучивания.")
            return

        self.set_loading(True)
        
        voice = self.get_selected_voice_id()
        pitch = self.slider_tone.value()
        
        self.worker = TTSWorker(text, voice, pitch)
        self.worker.finished.connect(self.play_audio)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def play_audio(self, file_path):
        self.set_loading(False)
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()

    def on_save_clicked(self):
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Внимание", "Введите текст для озвучивания.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить аудио", "", "MP3 Audio (*.mp3);;WAV Audio (*.wav)")
        if not file_path:
            return

        self.set_loading(True)
        
        voice = self.get_selected_voice_id()
        pitch = self.slider_tone.value()
        
        self.worker = TTSWorker(text, voice, pitch, output_file=file_path)
        self.worker.finished.connect(self.save_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def save_finished(self, path):
        self.set_loading(False)
        QMessageBox.information(self, "Успех", f"Файл успешно сохранен:\n{path}")

    def on_assign_clicked(self):
        text = self.text_input.toPlainText().strip()
        coord = self.input_cell.text().strip().upper()
        
        if not text:
            QMessageBox.warning(self, "Внимание", "Введите текст для озвучивания.")
            return
        
        if not coord:
            QMessageBox.warning(self, "Внимание", "Введите координату ячейки (например, A2).")
            return
            
        self.set_loading(True)
        
        voice = self.get_selected_voice_id()
        pitch = self.slider_tone.value()
        
        # Формируем путь для сохранения в новую папку
        filename = f"Synth_{coord}.mp3"
        save_dir = SYNTH_SPEECH_DIR
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        file_path = os.path.join(save_dir, filename)
        
        # Передаем coord в воркер через замыкание или просто запоминаем
        self.current_assign_coord = coord
        
        self.worker = TTSWorker(text, voice, pitch, output_file=file_path)
        self.worker.finished.connect(self.assign_finished)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def assign_finished(self, path):
        self.set_loading(False)
        # Отправляем сигнал в Main Window
        self.audio_assigned.emit(path, self.current_assign_coord)

    def handle_error(self, error_msg):
        self.set_loading(False)
        QMessageBox.critical(self, "Ошибка", f"Ошибка синтеза речи:\n{error_msg}\n\nУбедитесь, что установлен edge-tts (pip install edge-tts) и есть интернет.")
