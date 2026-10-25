import pyautogui
import time

print("Hover your mouse over the TOP-LEFT corner of the DaVinci video viewer in...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
x1, y1 = pyautogui.position()
print(f"Locked Top-Left: {x1}, {y1}\n")

print("Hover your mouse over the BOTTOM-RIGHT corner of the viewer in...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
x2, y2 = pyautogui.position()
print(f"Locked Bottom-Right: {x2}, {y2}\n")

width = x2 - x1
height = y2 - y1

print("DONE. Paste this exact line into line 31 of your server.py:")
print(f'capture_bbox = {{"top": {y1}, "left": {x1}, "width": {width}, "height": {height}}}')    