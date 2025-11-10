from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont
import random
import math

class Speedometer(QWidget):
    """A widget used to simulate a speedometer display."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.speed = 0
        self.max_speed = 240

        # Timer to simulate speed
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_speed)
        self.timer.start(500)

        # Arc settings for 120° sweep
        self.start_angle = 210   # starting angle in degrees (left side)
        self.arc_span = 120      # sweep angle in degrees

    def update_speed(self):
        self.speed = random.randint(60, 80)
        self.update()  # trigger repaint



    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect()
        cx = rect.width() / 2
        cy = rect.height() / 2
        radius = min(cx, cy) * 0.95

        # Draw outer arc (neon glow)
        pen = QPen(QColor("#00ffea"), 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(
            int(cx-radius), int(cy-radius), 2*int(radius), 2*int(radius),
            int(self.start_angle), int(self.arc_span*20.5)
        )

        # Draw ticks and numbers
        painter.setPen(QPen(QColor("#00ffea"), 2))
        font = QFont("Segoe UI", 10)
        painter.setFont(font)

        for i in range(0, self.max_speed+1, 60):
            # Map speed to arc span
            angle_deg = self.start_angle + (i / self.max_speed) * self.arc_span
            angle_rad = math.radians(angle_deg)

            # Tick positions
            x1 = cx + (radius-10) * math.cos(angle_rad)
            y1 = cy + (radius-10) * math.sin(angle_rad)
            x2 = cx + radius * math.cos(angle_rad)
            y2 = cy + radius * math.sin(angle_rad)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

            # Number positions
            num_radius = radius - 25
            x_text = cx + num_radius * math.cos(angle_rad)
            y_text = cy + num_radius * math.sin(angle_rad)
            painter.drawText(int(x_text)-10, int(y_text)+5, str(i))

        # Draw needle
        needle_angle_deg = self.start_angle + (self.speed / self.max_speed) * self.arc_span
        needle_angle_rad = math.radians(needle_angle_deg)
        needle_length = radius - 30
        painter.setPen(QPen(QColor("#ff00ff"), 4))
        x_needle = cx + needle_length * math.cos(needle_angle_rad)
        y_needle = cy + needle_length * math.sin(needle_angle_rad)
        painter.drawLine(int(cx), int(cy), int(x_needle), int(y_needle))

        # Center circle
        painter.setBrush(QBrush(QColor("#ff00ff")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(int(cx)-5, int(cy)-5, 10, 10)

        # Digital speed text
        painter.setPen(QColor("#f5f5f5"))
        painter.setFont(QFont("Segoe UI", 18, QFont.Bold))
        text_rect = rect.adjusted(0, 50, 0, 0)  # left, top, right, bottom offsets^
        painter.drawText(text_rect, Qt.AlignCenter, f"{self.speed} km/h")