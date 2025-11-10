from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, QSlider, QProgressBar
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QSize

class MusicPlayerWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget {
                background-color: #1a1d24;
                border-radius: 15px;
                color: #f5f5f5;
                font-family: 'Segoe UI';
                font-size: 16px;
            }
            QPushButton {
                background-color: white;
                border: 2px solid #00ffea;
                border-radius: 25px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #00ffea;
                color: #0e1117;
            }
            QProgressBar {
                background-color: #111;
                border-radius: 5px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #00ffea;
                border-radius: 5px;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #222;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00ffea;
                width: 14px;
                border-radius: 7px;
                margin: -4px 0;
            }
        """)

        # --- Widgets ---
        self.track_label = QLabel("No track playing")
        self.track_label.setAlignment(Qt.AlignCenter)
        self.track_label.setStyleSheet("font-weight: bold; font-size: 18px;")

        self.progress = QProgressBar()
        self.progress.setValue(0)

        # Control buttons
        self.prev_btn = QPushButton()
        self.prev_btn.setIcon(QIcon("icons/prev.svg"))
        self.prev_btn.setIconSize(QSize(24, 24))

        self.play_btn = QPushButton()
        self.play_btn.setIcon(QIcon("icons/play.svg"))
        self.play_btn.setIconSize(QSize(32, 32))

        self.next_btn = QPushButton()
        self.next_btn.setIcon(QIcon("icons/next.svg"))
        self.next_btn.setIconSize(QSize(24, 24))

        # Volume slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)

        # --- Layout ---
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.next_btn)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.addWidget(self.track_label)
        layout.addWidget(self.progress)
        layout.addLayout(controls_layout)
        layout.addWidget(QLabel("Volume"))
        layout.addWidget(self.volume_slider)

        self.setLayout(layout)

        # --- Simulation of playback progress ---
        self.playing = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

        self.play_btn.clicked.connect(self.toggle_play)

    def toggle_play(self):
        self.playing = not self.playing
        if self.playing:
            self.play_btn.setIcon(QIcon("icons/pause.svg"))
            self.timer.start(200)
        else:
            self.play_btn.setIcon(QIcon("icons/play.svg"))
            self.timer.stop()

    def update_progress(self):
        val = self.progress.value()
        if val < 100:
            self.progress.setValue(val + 1)
        else:
            self.progress.setValue(0)
