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

app = FastAPI()

# -------------------------------------------------------------
# 1. SCREEN CAPTURE & SCOPE STREAM CONFIG
# -------------------------------------------------------------
sct = mss.mss()

def get_scope_frame():
    # Default placeholder coordinates for the viewer
    capture_bbox = {"top": 150, "left": 960, "width": 960, "height": 540} 
    img = np.array(sct.grab(capture_bbox))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # Compress and stream
    frame = cv2.resize(frame, (854, 480))
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
    await websocket.accept()
    print("Phone controller connected.")
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

            elif action == "disable_clip":
                # Native Resolve shortcut to enable/disable clip
                pyautogui.press("d")

            elif action == "retime":
                # Native Resolve shortcut for Retime/Slowmo controls
                pyautogui.hotkey("ctrl", "r")

            # --- ADVANCED EDITING & NAVIGATION SHORTCUTS ---
            elif action == "mark_in":
                pyautogui.press("i")

            elif action == "mark_out":
                pyautogui.press("o")

            elif action == "delete":
                pyautogui.press("backspace")

            elif action == "ripple_del":
                pyautogui.press("delete")

            elif action == "prev_clip":
                pyautogui.press("up")

            elif action == "next_clip":
                pyautogui.press("down")

            elif action == "bypass_color":
                pyautogui.hotkey("shift", "d")

    except WebSocketDisconnect:
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