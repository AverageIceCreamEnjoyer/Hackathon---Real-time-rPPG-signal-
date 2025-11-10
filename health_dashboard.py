import sys
import random
import time 
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout, QWidget, QFrame, QGridLayout)
from PyQt5.QtCore import QTimer, QTime, QDate, Qt, QByteArray
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtSvg import QSvgWidget
import pyqtgraph as pg

from speedometer import Speedometer
from music_player import MusicPlayerWidget  
from opencv_widget import CameraWidget
import re
import numpy as np

fixed_width = 500
slice_number = 3
points_to_plot = 500

class HealthDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Health Panel")
        logo_icon = QIcon("icons/logo.jpeg")  

        # 2 different buffers for x and y data
        self.buffer_time = []
        self.buffer_y = []

        # x and y data for plotting
        self.y_data = []
        self.x_data = []

        # start time for x axis with a defined step
        self.begin_time = 0
        self.step_size = 10
        self.setWindowIcon(logo_icon)
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet("""background-color: #0e1117; color: #f5f5f5;font-family: 'Segoe UI'; font-size: 18px;""")

        self.title_label = QLabel("<h1>Car Health Dashboard</h1>")

        # Time label
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.time_label.setAlignment(Qt.AlignCenter)

        # Date label
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)

        # Heart Icon and label
        with open("icons/heart-rate-svgrepo-com.svg", "r") as f:
            svg_content = f.read()
        self.heart_icon = QSvgWidget()  # path to your SVG
        svg_content = re.sub(r'fill="[^"]+"', 'fill="red"', svg_content)
        self.heart_icon.load(QByteArray(svg_content.encode()))
        self.heart_icon.setFixedSize(40, 40)  # set icon size
        self.heart_label = QLabel("Heart Rate: -- bpm")
        self.heart_label.setFixedWidth(fixed_width)
        self.heart_label.setStyleSheet("font-size: 40px;")


        # Breathing Icon and label
        with open("icons/lungs-svgrepo-com(1).svg", "r") as f:
            svg_content = f.read()
        self.breathing_icon = QSvgWidget()  # path to your SVG
        self.breathing_icon.load(QByteArray(svg_content.encode()))
        self.breathing_icon.setFixedSize(40, 40)  # set icon size
        self.breathing_label = QLabel("Breathing Rate: 20 bpm")
        self.breathing_label.setFixedWidth(fixed_width)
        self.breathing_label.setStyleSheet("font-size: 40px;")

        # Oxygen Icon and label
        with open("icons/oxygen-svgrepo-com.svg", "r") as f:
            svg_content = f.read()
        self.oxygen_icon = QSvgWidget()  # path to your SVG
        svg_content = re.sub(r'fill="[^"]+"', 'fill="blue"', svg_content)
        self.oxygen_icon.load(QByteArray(svg_content.encode()))
        self.oxygen_icon.setFixedSize(40, 40)  # set icon size
        self.oxygen_label = QLabel("Oxygen Level: 70 %")
        self.oxygen_label.setFixedWidth(fixed_width)
        self.oxygen_label.setStyleSheet("font-size: 40px;")


        # Fuel icon and progress bar
        with open("icons/fuel-svgrepo-com.svg", "r") as f:
            svg_content = f.read()
        self.fuel_icon = QSvgWidget()  # path to your SVG
        svg_content = svg_content.replace('fill="#000000"', 'fill="#00ff00"')
        self.fuel_icon.load(QByteArray(svg_content.encode()))
        self.fuel_icon.setFixedSize(30, 30)  # set icon size
        self.fuel_bar = QProgressBar()
        self.fuel_bar.setStyleSheet("""
    QProgressBar {
        border-radius: 10px;
        height: 20px;
        text-align: center;
        color: #f5f5f5;
    }
    QProgressBar::chunk {
        border-radius: 10px;
        background-color: #00ff00;  /* green bar */
    }
""")
        self.fuel_bar.setTextVisible(False)
        self.fuel_bar.setAlignment(Qt.AlignCenter)
        self.fuel_bar_value = random.randint(60, 80)
        self.fuel_bar.setValue(self.fuel_bar_value)

        # Speedometer and label
        self.speed_label = QLabel("SPEED")
        self.speed_label.setAlignment(Qt.AlignRight)
        self.speed_label.setStyleSheet("font-size: 20px; color: #777b7e;")   
        self.speedometer = Speedometer()
        self.speedometer.setMinimumSize(250, 250)

        # PyQtGraph chart for real-time rPPG data
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0e1117")
        self.plot_widget.setYRange(-5, 5)
        self.plot_widget.setLabel('bottom', 'Time', units='s')  
        self.plot_widget.setLabel('left', 'rPPG', units='a.u.')   # Y-axis label
        pen = pg.mkPen(color="#00ffea", width=3)
        self.rppg_curve = self.plot_widget.plot([], [], pen=pen)

        # Song-Player widget
        self.image_label = QLabel()
        pixmap = QPixmap("icons/song_cover.jpeg")  # your image path
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)     # scales with label size
        self.image_label.setFixedSize(550, 300) 
        self.music_player = MusicPlayerWidget()
        self.music_player.setMaximumHeight(200)

        

        self.init_ui()
        self.update_time_date()  # Initial time/date update


        timer = QTimer(self)
        timer.timeout.connect(self.update_time_date)
        timer.start(5000)  # update every 5 seconds


        self.timer = QTimer()
        self.timer.timeout.connect(self.check_buffer)
        self.timer.start(50)  # check every 50 ms



    def init_ui(self):
        container = QWidget()
        container_layout = QGridLayout()

        container_layout.addWidget(self.title_label, 0, 0, 1, 2)

        # top side layout
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.date_label)  
        time_layout.addWidget(self.time_label)
        container_layout.addLayout(time_layout, 0, 2)
        

        # bottom left side layout
        layout = QVBoxLayout()
        layout.setSpacing(20)   
        heart_layout = QHBoxLayout()
        heart_layout.addWidget(self.heart_icon)
        heart_layout.addWidget(self.heart_label)
        layout.addLayout(heart_layout)

        breathing_layout = QHBoxLayout()
        breathing_layout.addWidget(self.breathing_icon)
        breathing_layout.addWidget(self.breathing_label)
        layout.addLayout(breathing_layout)

        oxygen_layout = QHBoxLayout()
        oxygen_layout.addWidget(self.oxygen_icon)
        oxygen_layout.addWidget(self.oxygen_label)
        layout.addLayout(oxygen_layout)

        # Wrapping the layout in a frame
        frame = QFrame()
        frame.setLayout(layout)
        frame.setStyleSheet("background-color: #1a1d24; border-radius: 15px; padding: 10px;")
        container_layout.addWidget(frame, 2, 0, 1, 1)


        # Top mid layout
        layout = QVBoxLayout()
        layout.addWidget(self.speed_label)
        layout.addWidget(self.speedometer)
        fuel_frame = QFrame()   
        fuel_frame.setStyleSheet("background-color: #111; max-height: 50px;")
        fuel_layout = QHBoxLayout()
        fuel_frame.setLayout(fuel_layout)
        fuel_layout.addWidget(self.fuel_icon)
        fuel_layout.addWidget(self.fuel_bar)    
        layout.addWidget(fuel_frame)

        frame = QFrame()
        frame.setLayout(layout)
        frame.setStyleSheet("background-color: #1a1d24; border-radius: 15px; padding: 10px;")
        container_layout.addWidget(frame, 1, 1, 1, 1)

        # bottom right  chart layout
        layout = QVBoxLayout()
        layout.addWidget(self.plot_widget)
        frame = QFrame()
        frame.setLayout(layout)
        container_layout.addWidget(frame, 2, 1, 1, 2)
        frame.setStyleSheet("background-color: #1a1d24; border-radius: 15px; padding: 10px;")

        # top left image and music player layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        layout.addWidget(self.music_player)
        container_layout.addLayout(layout, 1, 0, 1, 1)

        # OpenCV camera widget
        self.camera_widget = CameraWidget(camera_index=0)
        self.camera_widget.setMinimumSize(700, 350)
        self.camera_widget.data_signal.connect(self.update_from_camera)
        container_layout.addWidget(self.camera_widget, 1, 2)  


        container.setLayout(container_layout)
        self.setCentralWidget(container)

    def update_from_camera(self, rppg_list, rppg_timestamps, heart_rate) -> None:
        """Updating the buffer from camera data"""
        if rppg_list:
            self.buffer_y.extend(rppg_list)
            self.buffer_time.extend(np.linspace(self.begin_time, self.begin_time + self.step_size, len(rppg_list)))
            self.begin_time += self.step_size
            self.heart_label.setText(f"Heart Rate: {heart_rate} bpm")
            
    def check_buffer(self) -> None:
        """Check the buffer and update the plot if enough data is available"""
        if len(self.buffer_time) > 1:
            self.y_data.extend(self.buffer_y[:slice_number])
            self.x_data.extend(np.array(self.buffer_time[:slice_number]).tolist())

            del self.buffer_y[:slice_number]
            del self.buffer_time[:slice_number]
            if len(self.x_data) > points_to_plot:
                # Slicing the data
                self.x_data = self.x_data[-points_to_plot:]
                self.y_data = self.y_data[-points_to_plot:]
            self.rppg_curve.setData(self.x_data, self.y_data)



    def update_time_date(self) -> None:
        """Update the time and date labels + fuel bar"""
        current_time = QTime.currentTime().toString("HH:mm")  # hours and minutes
        current_date = QDate.currentDate()
        weekday = current_date.longDayName(current_date.dayOfWeek())  # e.g., "Thursday"
        formatted_date = f"{current_date.toString('dd MMM yyyy')}, {weekday}"

        self.fuel_bar_value -= 0.5
        self.fuel_bar.setValue(max(0, self.fuel_bar_value))

        self.time_label.setText(current_time)
        self.date_label.setText(formatted_date)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HealthDashboard()
    window.showFullScreen()
    sys.exit(app.exec_())