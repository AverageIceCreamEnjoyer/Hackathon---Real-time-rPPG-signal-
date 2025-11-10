# Caire Python WS Client — Payload & WebSocket Guide

**Car Health Dashboard** is a real-time visualization tool that integrates camera-based physiological data streaming (via WebSocket), animated widgets, and multimedia playback — all in a sleek PyQt5 GUI.

The app combines:
- A **live camera feed** that connects to a backend WebSocket API  
- Real-time **rPPG signal plots** (heart-rate waveform)  
- Animated **speedometer**, **fuel**, and **vital-sign indicators**  
- A built-in **music player** panel  

---


| File | Description |
|------|--------------|
| `health_dashboard.py` | Main GUI window that integrates all components: camera, charts, music, speedometer, and health indicators. |
| `opencv_widget.py` | Handles camera capture, WebSocket communication, and real-time physiological data (rPPG, heart rate, etc.). |
| `speedometer.py` | Custom PyQt5 widget simulating a dynamic car speedometer. |
| `music_player.py` | Music player widget with controls (play/pause, next/previous, etc.). |
| `icons/` | SVG and image assets (heart, lungs, oxygen, fuel, logo, album cover). |
| `.env` | Environment configuration file (WebSocket endpoint, FPS, etc.). |
| `pyproject.toml` | Project dependencies (managed with `uv`). |
| `uv.lock` | Lock file for reproducible installations. |

---

## 🖥️ Features

✅ Real-time camera streaming via WebSocket  
✅ rPPG (remote photoplethysmography) waveform plotting with `pyqtgraph`  
✅ Animated dashboard with health and car metrics  
✅ Neon-style **speedometer** widget  
✅ Built-in **music player**  
✅ **Environment-based configuration** with `.env`  
✅ **Reproducible environment** using `uv.lock`

---

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed (e.g. `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Backend reachable at a WebSocket URL (e.g. `ws://HOST:8003/ws/`)

---

## Install deps

From the project directory:

```bash
uv sync
```

or 

```bash
pip install -r requirements.txt
```

---

**Core environment variables:**

- `BACKEND_WS_BASE` — e.g. `ws://localhost:8003/ws/`
- `API_KEY` — your API key. Get one with the caire team.
- `IMAGES_DIR` — folder with timestamped `.png` files
- `FPS` — target send rate


---

## Outgoing payload (client → server)

The client sends **one message per frame**. The messages should be taged as `"stream"` or `"end"` in the `"state"` field of the message. For the final message, use the `"end"` state. This signals the server that the inference should be over. For the other messages, keep the `"stream"` state.

### Required fields

```jsonc
{
  "datapt_id": "ed21c799-9edd-4706-9256-0324a7697adb", // UUIDv4 (one per session)
  "state": "stream",                                   // or "end" for the last message
  "frame_data": "<BASE64_JPEG_NO_PREFIX>",             // base64 JPEG (or original PNG if FRAME_FORMAT=raw)
  "timestamp": "1747154380.5511632",                   // derived from filename (string)
  "advanced": true                                     // enables advanced data in responses
}
```

- **datapt_id**: a unique identifier for the stream data point. In browser code we generate `crypto.randomUUID()` which is equivalent to Python’s `uuid.uuid4()`.
- **state**: `"stream"` for regular frames, `"end"` for the final message.
- **frame_data**: base64 JPEG **without** `data:image/jpeg;base64,` prefix.
- **timestamp**: UNIX time in seconds (string). Fractional seconds are allowed.
- **advanced**:  
  - `true`: the server will include **advanced continuous signals** (e.g., `advanced.rppg`, `advanced.rppg_timestamps`) in responses.  
  - `false`: the server will not stream those signals.

### Example: “stream” payload (one frame)

```json
{
  "datapt_id": "ed21c799-9edd-4706-9256-0324a7697adb",
  "state": "stream",
  "frame_data": "<base64>",
  "timestamp": "1730868591.123",
  "advanced": true
}
```

### Example: final “end” payload

```json
{
  "datapt_id": "ed21c799-9edd-4706-9256-0324a7697adb",
  "state": "end",
  "frame_data": "<base64_of_last_frame>",
  "timestamp": "1730868621.987",
  "advanced": true
}
```

---

## Incoming responses (server → client)

The server responses are JSON. Two states are expected:

- `state: "ok"` — **intermediate** updates during streaming
- `state: "finished"` — **final** message for the stream

### Example: intermediate response with advanced data

```json
{
  "state": "ok",
  "socket_id": "c73bb619",
  "datapt_id": "0e06d32c-1afb-43de-994a-8293d96d5e05",
  "inference": { "hr": 66 },
  "advanced": {
    "rppg": [0.5120, 0.4296, ...],
    "rppg_timestamps": [1762439955.133, 1762439955.166, ...]
  },
  "confidence": {},
  "feedback": null,
  "model_version": "HR"
}
```

### Example: final response with advanced disabled

```json
{
  "state": "finished",
  "socket_id": "c73bb619",
  "datapt_id": "ed21c799-9edd-4706-9256-0324a7697adb",
  "inference": { "hr": 65 },
  "advanced": null,
  "confidence": {},
  "feedback": null,
  "model_version": "HR"
}
```


---

## Helper functions for server communication

The Python client is structured to make the WebSocket and payload obvious:

- `build_ws_url()` — forms the WS URL with `api_key`.
- `build_payload()` — centralized payload construction per frame.
- `encoder_producer()` — off-thread JPEG/RAW base64 encoding into an asyncio queue.
- `server_listener()` — prints every server message (handles text/binary).
---

