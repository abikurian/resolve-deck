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
print(f'capture_bbox = {{"top": {y1}, "left": {x1}, "width": {width}, "height": {height}}}\n')

print("Hover your mouse over the dead center of the Lift wheel in...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
lift_x, lift_y = pyautogui.position()
print(f"Locked Lift: {lift_x}, {lift_y}\n")

print("Hover your mouse over the dead center of the Gamma wheel in...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
gamma_x, gamma_y = pyautogui.position()
print(f"Locked Gamma: {gamma_x}, {gamma_y}\n")

print("Hover your mouse over the dead center of the Gain wheel in...")
for i in range(3, 0, -1):
    print(i)
    time.sleep(1)
gain_x, gain_y = pyautogui.position()
print(f"Locked Gain: {gain_x}, {gain_y}\n")

print("Paste this line into your server configuration:")
print(f'color_targets = {{"lift": ({lift_x}, {lift_y}), "gamma": ({gamma_x}, {gamma_y}), "gain": ({gain_x}, {gain_y})}}')
    