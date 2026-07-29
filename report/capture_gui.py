"""Render the Tkinter GUI headlessly and save a screenshot of each tab.

Run under a virtual display, e.g.:
    xvfb-run -s "-screen 0 620x520x24" python3.12 report/capture_gui.py
Saves report/assets/gui_tab1.png, gui_tab2.png, gui_tab3.png.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import ImageGrab

from src.gui import ApplicationWindow

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(OUT, exist_ok=True)

app = ApplicationWindow()
app.geometry("600x480+0+0")
app.update_idletasks()
app.update()

notebook = app.winfo_children()[0]
tabs = notebook.tabs()
disp = os.environ.get("DISPLAY", ":99")

for i, tab in enumerate(tabs, start=1):
    notebook.select(tab)
    for _ in range(6):
        app.update_idletasks()
        app.update()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h), xdisplay=disp)
    path = os.path.join(OUT, f"gui_tab{i}.png")
    img.save(path)
    print("saved", path, img.size)

app.destroy()
