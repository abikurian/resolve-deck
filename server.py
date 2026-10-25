import io
import time
import asyncio
import cv2
import mss
import numpy as np
import pyautogui
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse

# Disable PyAutoGUI delay for instantaneous jog wheel responsiveness
pyautogui.PAUSE = 0.0

# -------------------------------------------------------------
# COLOR WHEEL CALIBRATION TARGETS
# Replace with coordinates output by calibrate.py:
# color_targets = {"lift": (x1, y1), "gamma": (x2, y2), "gain": (x3, y3)}
# -------------------------------------------------------------
color_targets = {
    "lift": (700, 850),
    "gamma": (960, 850),
    "gain": (1220, 850),
}

app = FastAPI()

# -------------------------------------------------------------
# 1. SCREEN CAPTURE & SCOPE STREAM CONFIG
# -------------------------------------------------------------
# Adjust this monitor/bounding box to crop DaVinci's Viewer or Scopes.
# You can leave it capturing the central area or specific display.
sct = mss.mss()

def get_scope_frame():
    # Grab primary monitor or defined region
    # Format: {"top": 100, "left": 100, "width": 800, "height": 600}
    monitor = sct.monitors[1]
    
    # Target top-center (common viewer/scope placement)
    w = monitor["width"] // 2
    h = monitor["height"] // 2
    capture_bbox = {"top": 60, "left": w // 2, "width": w, "height": h}
    
    img = np.array(sct.grab(capture_bbox))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    # Generate on-the-fly RGB Histogram HUD overlaid at the bottom
    h_h, h_w = 120, frame.shape[1]
    hist_canvas = np.zeros((h_h, h_w, 3), dtype=np.uint8)
    colors = ( (255, 0, 0), (0, 255, 0), (0, 0, 255) ) # B, G, R
    
    for i, col in enumerate(colors):
        hist = cv2.calcHist([frame], [i], None, [256], [0, 256])
        cv2.normalize(hist, hist, 0, h_h - 10, cv2.NORM_MINMAX)
        pts = []
        for x_idx, val in enumerate(hist):
            px = int(x_idx * (h_w / 256.0))
            py = int(h_h - val[0])
            pts.append([px, py])
        pts = np.array(pts, np.int32).reshape((-1, 1, 2))
        cv2.polylines(hist_canvas, [pts], False, col, 2)
        
    # Combine preview image and generated scope
    combined = np.vstack((cv2.resize(frame, (h_w, 240)), hist_canvas))
    
    # Compress as lightweight JPEG for rapid streaming
    _, jpeg = cv2.imencode('.jpg', combined, [cv2.IMWRITE_JPEG_QUALITY, 60])
    return jpeg.tobytes()

def generate_video_stream():
    while True:
        frame_bytes = get_scope_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS throttle

@app.get("/stream")
def video_feed():
    return StreamingResponse(generate_video_stream(), 
                             media_type="multipart/x-mixed-replace; boundary=frame")

# -------------------------------------------------------------
# 2. WEBSOCKET CONTROLLER PIPELINE (Phone -> PC)
# -------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Phone controller connected.")
    active_wheel = None
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            # --- JOG / SHUTTLE WHEEL ---
            if action == "jog":
                delta = data.get("delta", 0)
                if delta > 0:
                    pyautogui.press("right", presses=int(abs(delta)))
                elif delta < 0:
                    pyautogui.press("left", presses=int(abs(delta)))
                    
            elif action == "play_pause":
                pyautogui.press("space")

            elif action == "cut":
                # DaVinci Split / Blade Shortcut: Ctrl + \
                pyautogui.hotkey("ctrl", "\\")

            # --- 3-WAY COLOR WHEEL TELEMETRY ---
            elif action == "color":
                wheel_name = data.get("wheel") # lift, gamma, gain
                dx = float(data.get("dx", 0.0))
                dy = float(data.get("dy", 0.0))
                
                # Finger lifted / released puck
                if dx == 0 and dy == 0:
                    pyautogui.mouseUp()
                    active_wheel = None
                else:
                    if wheel_name in color_targets:
                        base_x, base_y = color_targets[wheel_name]
                        target_x = int(base_x + dx * 40)
                        target_y = int(base_y + dy * 40)
                        
                        if active_wheel != wheel_name:
                            pyautogui.mouseUp()
                            pyautogui.moveTo(base_x, base_y)
                            pyautogui.mouseDown()
                            active_wheel = wheel_name
                            
                        pyautogui.moveTo(target_x, target_y)

    except WebSocketDisconnect:
        pyautogui.mouseUp()
        print("Phone controller disconnected.")

# -------------------------------------------------------------
# 3. EMBEDDED CONTROLLER MOBILE UI
# -------------------------------------------------------------
@app.get("/")
def get_ui():
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)

if __name__ == "__main__":
    import uvicorn
    # Listens across your entire local LAN so iPhone can reach it
    uvicorn.run(app, host="0.0.0.0", port=8000)