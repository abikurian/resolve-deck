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

# Multi-Page Interface State ("color" or "edit")
active_page = "color"

app = FastAPI()

# -------------------------------------------------------------
# 1. SCREEN CAPTURE & SCOPE STREAM CONFIG
# -------------------------------------------------------------
# Adjust this monitor/bounding box to crop DaVinci's Viewer or Scopes.
# You can leave it capturing the central area or specific display.
sct = mss.mss()

def get_scope_frame():
    global active_page
    # Dynamically swap capture region based on active page
    if active_page == "color":
        capture_bbox = {"top": 150, "left": 1200, "width": 720, "height": 405}
    else:  # edit
        capture_bbox = {"top": 100, "left": 960, "width": 960, "height": 540}
    
    img = np.array(sct.grab(capture_bbox))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    # Compress as JPEG for rapid streaming
    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
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
    global active_page
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

            elif action == "add_serial":
                pyautogui.hotkey("alt", "s")

            elif action == "add_parallel":
                pyautogui.hotkey("alt", "p")

            elif action == "undo":
                pyautogui.hotkey("ctrl", "z")

            elif action == "redo":
                pyautogui.hotkey("ctrl", "shift", "z")

            # --- MULTI-PAGE & CLIP MANAGEMENT SHORTCUTS ---
            elif action == "page_edit":
                pyautogui.hotkey("shift", "4")
                active_page = "edit"

            elif action == "page_color":
                pyautogui.hotkey("shift", "6")
                active_page = "color"

            elif action == "disable_clip":
                # Native Resolve shortcut to enable/disable clip
                pyautogui.press("d")

            elif action == "retime":
                # Native Resolve shortcut for Retime/Slowmo controls
                pyautogui.hotkey("ctrl", "r")

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