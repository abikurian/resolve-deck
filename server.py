import time
import asyncio
import keyboard
import pyautogui
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

# Disable PyAutoGUI delay for instantaneous jog wheel responsiveness
pyautogui.PAUSE = 0.0

# Multi-Page Interface State ("edit" or "color")
current_page = "edit"

app = FastAPI()

# -------------------------------------------------------------
# 1. WEBSOCKET CONTROLLER PIPELINE (Phone -> PC)
# -------------------------------------------------------------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_page
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
                keyboard.send("shift+backspace")

            elif action == "esc":
                keyboard.send("esc")

            elif action == "prev_clip":
                pyautogui.press("up")

            elif action == "next_clip":
                pyautogui.press("down")

            elif action == "bypass_color":
                pyautogui.hotkey("shift", "d")

            # --- WORKSPACE PAGE SWITCHING ---
            elif action == "page_edit":
                keyboard.send("shift+4")
                current_page = "edit"

            elif action == "page_color":
                keyboard.send("shift+6")
                current_page = "color"

    except WebSocketDisconnect:
        print("Phone controller disconnected.")

# -------------------------------------------------------------
# 2. EMBEDDED CONTROLLER MOBILE UI
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