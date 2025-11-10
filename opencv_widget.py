
import asyncio
import base64
import uuid
import time
import os
import cv2
import numpy as np
import websockets
import orjson
from collections import deque

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
from dotenv import load_dotenv

load_dotenv()

# ---------------- Config ----------------
BACKEND_WS_BASE = os.getenv("BACKEND_WS_BASE", "CAIRE_WS_ENDPOINT")
API_KEY = os.getenv("API_KEY", "YOUR_CAIRE_API_KEY")
FPS = float(os.getenv("FPS", "30"))  # GUI frame rate
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "70"))
FRAME_BUFFER_SIZE = int(os.getenv("FRAME_BUFFER_SIZE", "30"))  # max frames to buffer


# ---------------- Helpers ----------------
def build_ws_url():
    from urllib.parse import urlencode
    params = {"api_key": API_KEY, "client": "qtClient"}
    return f"{BACKEND_WS_BASE.rstrip('/')}/?{urlencode(params)}"

def encode_frame_jpeg(frame: np.ndarray, quality: int) -> str:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise RuntimeError("JPEG encoding failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")

def build_payload(datapt_id: str, timestamp: str, frame_b64: str):
    return {
        "datapt_id": datapt_id,
        "state": "stream",
        "timestamp": timestamp,
        "frame_data": frame_b64,
        "advanced": True,
    }

class CameraThread(QThread):
    """Thread to capture video frames and communicate with the server."""
    frame_received = pyqtSignal(QImage)
    server_message = pyqtSignal(str)
    data_received = pyqtSignal(list, list, str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.running = True
        self.loop = None
        self.frame_buffer = deque(maxlen=FRAME_BUFFER_SIZE)

    def stop(self):
        self.running = False
        self.wait()

    def handle_server_message(self, msg: str):
        try:
            data = orjson.loads(msg)
            rppg = data.get("advanced", {}).get("rppg", [])[-256:]
            rppg_timestamps = data.get("advanced", {}).get("rppg_timestamps", [])[-256:]
            heart_rate = str(data.get("inference", {}).get("hr", ""))
            if rppg:
                # Send the rPPG data to the QWidget
                self.data_received.emit(rppg, rppg_timestamps, heart_rate)
        except Exception as e:
            print("Error parsing server message:", e)



    # ---------------- Send frames to server ----------------

    async def send_frames(self, ws): 
        cap = cv2.VideoCapture(self.camera_index) 
        if not cap.isOpened(): 
            self.server_message.emit("Cannot open camera")
            return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, FPS)
        start = time.perf_counter()
        frame_count = 0
        while self.running:
            next_time = start + frame_count / FPS
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.01)
                continue

            # Convert frame to Qt image
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qt_image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            self.frame_received.emit(qt_image)

            # Encode and send to server
            b64 = encode_frame_jpeg(frame, JPEG_QUALITY)
            payload = build_payload(str(uuid.uuid4()), str(time.time()), b64)
            await ws.send(orjson.dumps(payload).decode("utf-8"))
            frame_count += 1
            await asyncio.sleep(max(0, next_time - time.perf_counter()))
        cap.release()


    # ---------------- Receive server messages ----------------
    async def listen_to_server(self, ws):
        try:
            async for msg in ws:
                if isinstance(msg, (bytes, bytearray)):
                    msg = msg.decode("utf-8", errors="ignore")
                self.handle_server_message(msg)
        except Exception as e:
            self.server_message.emit(f"Server connection closed: {e}")

    # ---------------- WebSocket task ----------------
    async def websocket_task(self):
        ws_url = build_ws_url()
        self.server_message.emit(f"Connecting to {ws_url}")

        async with websockets.connect(ws_url, max_size=2**22, compression=None) as ws:
            self.server_message.emit("Connected to server")

            sender = asyncio.create_task(self.send_frames(ws))
            listener = asyncio.create_task(self.listen_to_server(ws))
            done, pending = await asyncio.wait( [sender, listener], return_when=asyncio.FIRST_EXCEPTION )

            for task in pending:
                task.cancel()

    # ---------------- Run thread ----------------
    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.websocket_task())
        except Exception as e:
            self.server_message.emit(f"WebSocket error: {e}")
        finally:
            self.loop.close()





# ---------------- Camera Widget ----------------
class CameraWidget(QWidget):
    """Widget to display camera feed and handle communication within a QThread."""
    data_signal = pyqtSignal(list, list, str)

    def __init__(self, camera_index=0):
        super().__init__()
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                border-radius: 15px;
                background-color: #0e1117;
            }
        """)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)
        self.setLayout(layout)

        self.thread = CameraThread(camera_index)
        self.thread.frame_received.connect(self.update_frame)
        self.thread.server_message.connect(self.display_message)
        self.thread.data_received.connect(self.forward_data)
        self.thread.start()

    def forward_data(self, rppg, rppg_timestamps, heart_rate):
        """Forward the received data via signal to the main widget."""
        self.data_signal.emit(rppg, rppg_timestamps, heart_rate)

    def update_frame(self, qt_image):
        """Update the video frame on the UI"""
        pix = QPixmap.fromImage(qt_image).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    def display_message(self, msg):
        # log or show messages if needed
        pass

    def closeEvent(self, event):
        self.thread.stop()
        super().closeEvent(event)