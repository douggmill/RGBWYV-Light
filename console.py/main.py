########################main.py#########################

########################################################
########################Modules#########################
########################################################
import tkinter as tk
from tkinter import ttk, Menu, font as tkfont
from PIL import Image, ImageTk  # for icon
from PIL.ImageTk import PhotoImage  # for icon
import threading
from serial_module import connect_serial, send_data, serial_thread, data_queue, auto_connect, get_connection_status, close_serial
from ini import load_theme, save_theme
import os
import sys
import time
import queue
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ui_ready = False

initial_values = []


########################################################
########################Themes##########################
########################################################

THEMES = {
    "dark": {
        "bg": "#1b1d22",
        "surface": "#25272e",
        "surface2": "#2e313a",
        "header": "#16181d",
        "fg": "#ececec",
        "muted": "#9aa0aa",
        "border": "#3c404a",
        "accent": "#5b8def",
        "button": "#3a3e48",
        "button_fg": "#ececec",
        "button_active": "#4b5160",
        "entry_bg": "#12141a",
        "text_bg": "#12141a",
        "text_fg": "#e6e6e6",
        "select_bg": "#3d5a80",
        "select_fg": "#ffffff",
        "trough": "#3a3e48",
        "ok": "#4caf7a",
        "bad": "#ef5350",
        "tab_sel": "#25272e",
        "tab": "#1f2228",
        "white_accent": "#dfe3e8",
        "white_label": "#e8eaed",
        "white_fg": "#1b1d22",
        "scale_bg": "#25272e",
    },
    "light": {
        "bg": "#eef0f4",
        "surface": "#ffffff",
        "surface2": "#f4f6f9",
        "header": "#ffffff",
        "fg": "#1c1f26",
        "muted": "#5f6673",
        "border": "#d0d5de",
        "accent": "#1565c0",
        "button": "#e8ebf0",
        "button_fg": "#1c1f26",
        "button_active": "#d5dae3",
        "entry_bg": "#ffffff",
        "text_bg": "#ffffff",
        "text_fg": "#1c1f26",
        "select_bg": "#bbdefb",
        "select_fg": "#0d47a1",
        "trough": "#d5dae3",
        "ok": "#2e7d4f",
        "bad": "#c62828",
        "tab_sel": "#ffffff",
        "tab": "#e4e7ed",
        "white_accent": "#607d8b",
        "white_label": "#37474f",
        "white_fg": "#ffffff",
        "scale_bg": "#ffffff",
    },
}

# Channel accents stay vivid in both themes. White uses a theme-aware shade.
CHANNEL_ACCENTS = {
    "red": "#e53935",
    "amber": "#f9a825",
    "green": "#43a047",
    "blue": "#1e88e5",
    "violet": "#8e24aa",
    "white": None,
    "pwm": "#78909c",
    "upper": "#90a4ae",
    "lower": "#546e7a",
    "param": "#5c6bc0",
}

current_theme = "dark"
palette = THEMES["dark"]
themed_widgets = []  # (widget, role)
accent_widgets = []  # (widget, kind, accent_key)


def _accent_color(key):
    if key == "white":
        return palette["white_accent"]
    return CHANNEL_ACCENTS.get(key, palette["accent"])


def _label_accent(key):
    if key == "white":
        return palette["white_label"]
    return CHANNEL_ACCENTS.get(key, palette["accent"])


def _accent_fg(key):
    if key == "white":
        return palette["white_fg"]
    if key in ("amber", "green", "upper"):
        return "#1b1d22"
    return "#ffffff"


def _register(widget, role):
    themed_widgets.append((widget, role))
    return widget


def _register_accent(widget, kind, accent_key):
    accent_widgets.append((widget, kind, accent_key))
    return widget


def _pick_font_family():
    available = set(tkfont.families())
    for name in ("Ubuntu", "Noto Sans", "DejaVu Sans", "Cantarell", "Sans"):
        if name in available:
            return name
    return "TkDefaultFont"


########################################################
#####################Main window########################
########################################################


root = tk.Tk()
root.title("BLE RGBWYV Control")
image_path = os.path.join(BASE_DIR, "AdditiveColorMixing.png")  # Path to icon file
img = Image.open(image_path)  # Open the icon
img = img.resize((32, 32), Image.Resampling.LANCZOS)  # Resize the image to a 32x32 icon size
icon: PhotoImage = ImageTk.PhotoImage(img)  # Convert the image for Tkinter compatibility
root.iconphoto(True, icon)  # Set the window icon
root.geometry("780x840")
root.minsize(700, 720)
root.resizable(True, True)

FONT_FAMILY = _pick_font_family()
FONT = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, "bold")
FONT_TITLE = (FONT_FAMILY, 14, "bold")
FONT_SMALL = (FONT_FAMILY, 8)
FONT_VALUE = (FONT_FAMILY, 11, "bold")
FONT_MONO = ("DejaVu Sans Mono", 9)
if "Ubuntu Mono" in set(tkfont.families()):
    FONT_MONO = ("Ubuntu Mono", 9)
elif "Noto Sans Mono" in set(tkfont.families()):
    FONT_MONO = ("Noto Sans Mono", 9)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except tk.TclError:
    pass

theme_var = tk.StringVar(root, value="dark")


#####################File Menu########################
def open_config():
    """Open config.ini with the system's default text editor."""
    config_path = os.path.join(BASE_DIR, "config.ini")
    try:
        if os.name == "nt":
            os.startfile(config_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", config_path], check=False)
        else:
            subprocess.run(["xdg-open", config_path], check=False)
    except Exception as exc:
        print(f"Could not open config file: {exc}")


#####################Commands########################
def save_slider_values():  # send linear slider values
    """Send the slider value over serial in the format adcX,value."""
    command = "save"
    data_to_send = command
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}")


def send_manual_command(event=None):
    """ Sends text from the entry field to the serial device. """
    command = "mode,2"
    data_to_send = command
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}")


def send_RGB_wave_command(event=None):
    """ Sends text from the entry field to the serial device. """
    command = "mode,0"
    data_to_send = command
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}")

def send_audio_command(event=None):
    """ Sends text from the entry field to the serial device. """
    command = "mode,1"
    data_to_send = command
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}")

def send_RGB_retro_command(event=None):
    """ Sends text from the entry field to the serial device. """
    command = "mode,3"
    data_to_send = command
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}")

def on_tab_selected(event):
    if not ui_ready:
        return
    if os.environ.get("RGBWYV_SCREENSHOT_DIR"):
        return
    selected_tab = notebook.index(notebook.select())
    if selected_tab == 0:
        send_manual_command()
    elif selected_tab == 1:
        send_RGB_wave_command()
    elif selected_tab == 2:
        send_audio_command()
    elif selected_tab == 3:
        send_RGB_retro_command()


########################################################
########################Theming#########################
########################################################

def apply_theme(name, persist=True):
    """Restyle ttk and tk widgets for light or dark mode."""
    global current_theme, palette
    name = "light" if name == "light" else "dark"
    current_theme = name
    palette = THEMES[name]
    theme_var.set(name)
    p = palette

    root.configure(bg=p["bg"])
    root.option_add("*Font", FONT)

    style.configure(".", background=p["bg"], foreground=p["fg"], font=FONT)
    style.configure("TFrame", background=p["bg"])
    style.configure("Surface.TFrame", background=p["surface"])
    style.configure("Header.TFrame", background=p["header"])
    style.configure("TLabel", background=p["bg"], foreground=p["fg"], font=FONT)
    style.configure("Header.TLabel", background=p["header"], foreground=p["fg"], font=FONT_TITLE)
    style.configure("Muted.TLabel", background=p["bg"], foreground=p["muted"], font=FONT_SMALL)
    style.configure("Status.TLabel", background=p["header"], foreground=p["muted"], font=FONT)
    style.configure(
        "TNotebook",
        background=p["bg"],
        borderwidth=0,
        tabmargins=[8, 8, 8, 0],
        lightcolor=p["bg"],
        darkcolor=p["bg"],
        bordercolor=p["bg"],
    )
    style.configure(
        "TNotebook.Tab",
        background=p["tab"],
        foreground=p["fg"],
        lightcolor=p["border"],
        darkcolor=p["border"],
        bordercolor=p["border"],
        padding=[16, 8],
        font=FONT_BOLD,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", p["tab_sel"])],
        foreground=[("selected", p["fg"])],
        lightcolor=[("selected", p["accent"])],
        expand=[("selected", [0, 0, 0, 0])],
    )
    style.configure(
        "TPanedwindow",
        background=p["bg"],
    )
    style.configure(
        "Vertical.TScrollbar",
        background=p["surface2"],
        troughcolor=p["bg"],
        bordercolor=p["border"],
        arrowcolor=p["fg"],
        lightcolor=p["surface2"],
        darkcolor=p["surface2"],
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", p["button_active"])],
    )
    style.configure(
        "Horizontal.TScrollbar",
        background=p["surface2"],
        troughcolor=p["bg"],
        bordercolor=p["border"],
        arrowcolor=p["fg"],
        relief="flat",
    )
    style.configure(
        "TSeparator",
        background=p["border"],
    )

    for widget, role in themed_widgets:
        try:
            if role == "bg":
                widget.configure(bg=p["bg"])
            elif role == "surface":
                widget.configure(bg=p["surface"], highlightbackground=p["border"])
            elif role == "header":
                widget.configure(bg=p["header"])
            elif role == "label":
                widget.configure(bg=p["surface"], fg=p["fg"])
            elif role == "label_bg":
                widget.configure(bg=p["bg"], fg=p["fg"])
            elif role == "header_label":
                widget.configure(bg=p["header"], fg=p["fg"])
            elif role == "muted":
                widget.configure(bg=p["surface"], fg=p["muted"])
            elif role == "muted_bg":
                widget.configure(bg=p["bg"], fg=p["muted"])
            elif role == "header_muted":
                widget.configure(bg=p["header"], fg=p["muted"])
            elif role == "entry":
                widget.configure(
                    bg=p["entry_bg"],
                    fg=p["fg"],
                    insertbackground=p["fg"],
                    highlightbackground=p["border"],
                    highlightcolor=p["accent"],
                    disabledbackground=p["surface2"],
                    disabledforeground=p["muted"],
                    selectbackground=p["select_bg"],
                    selectforeground=p["select_fg"],
                )
            elif role == "text":
                widget.configure(
                    bg=p["text_bg"],
                    fg=p["text_fg"],
                    insertbackground=p["fg"],
                    highlightbackground=p["border"],
                    highlightcolor=p["accent"],
                    selectbackground=p["select_bg"],
                    selectforeground=p["select_fg"],
                )
            elif role == "canvas":
                widget.configure(bg=p["bg"], highlightbackground=p["bg"], highlightcolor=p["bg"])
            elif role == "menu":
                widget.configure(
                    bg=p["header"],
                    fg=p["fg"],
                    activebackground=p["accent"],
                    activeforeground="#ffffff",
                    disabledforeground=p["muted"],
                    relief="flat",
                    bd=0,
                )
            elif role == "button":
                widget.configure(
                    bg=p["button"],
                    fg=p["button_fg"],
                    activebackground=p["button_active"],
                    activeforeground=p["fg"],
                    highlightbackground=p["border"],
                    highlightcolor=p["accent"],
                    disabledforeground=p["muted"],
                )
            elif role == "button_accent":
                widget.configure(
                    bg=p["accent"],
                    fg="#ffffff",
                    activebackground=p["accent"],
                    activeforeground="#ffffff",
                    highlightbackground=p["accent"],
                    highlightcolor=p["accent"],
                )
            elif role == "status":
                refresh_status()
        except tk.TclError:
            pass

    for widget, kind, key in accent_widgets:
        color = _accent_color(key)
        try:
            if kind == "bar":
                widget.configure(bg=color)
            elif kind == "label":
                widget.configure(bg=p["surface"], fg=_label_accent(key))
            elif kind == "label_on_bg":
                widget.configure(bg=p["bg"], fg=_label_accent(key))
            elif kind == "value":
                widget.configure(bg=p["surface"], fg=p["fg"])
            elif kind == "scale":
                scale_fg = _accent_fg(key)
                widget.configure(
                    bg=color,
                    fg=scale_fg,
                    troughcolor=p["trough"],
                    activebackground=color,
                    highlightbackground=p["surface"],
                    highlightcolor=p["surface"],
                )
        except tk.TclError:
            pass

    theme_btn.configure(text="Light mode" if name == "dark" else "Dark mode")
    refresh_status()
    if persist:
        try:
            save_theme(name)
        except Exception as exc:
            print(f"Could not save theme: {exc}")


def toggle_theme():
    apply_theme("light" if current_theme == "dark" else "dark")


def refresh_status():
    status = get_connection_status()
    connected = "Connected" in status
    color = palette["ok"] if connected else palette["bad"]
    label_text = status if status.startswith("Status:") else f"Status: {status}"
    try:
        status_dot.configure(fg=color, bg=palette["header"])
        status_label.configure(text=label_text, fg=color, bg=palette["header"])
    except (NameError, tk.TclError):
        pass


menu_bar = Menu(root, tearoff=0)  # Create menu bar
root.config(menu=menu_bar)
file_menu = Menu(menu_bar, tearoff=0)  # Add File menu
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Open Config", command=open_config)  # Add "Open Config" option
file_menu.add_command(label="Save Values", command=save_slider_values)
view_menu = Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="View", menu=view_menu)
view_menu.add_radiobutton(label="Dark mode", variable=theme_var, value="dark", command=lambda: apply_theme("dark"))
view_menu.add_radiobutton(label="Light mode", variable=theme_var, value="light", command=lambda: apply_theme("light"))
_register(menu_bar, "menu")
_register(file_menu, "menu")
_register(view_menu, "menu")


########################################################
########################Header##########################
########################################################

header = tk.Frame(root, height=52)
header.pack(fill="x", side="top")
header.pack_propagate(False)
_register(header, "header")

title_label = tk.Label(header, text="BLE RGBWYV Control", font=FONT_TITLE, anchor="w")
title_label.pack(side="left", padx=(18, 10), pady=12)
_register(title_label, "header_label")

theme_btn = tk.Button(
    header,
    text="Light mode",
    command=toggle_theme,
    relief="flat",
    bd=0,
    padx=14,
    pady=5,
    cursor="hand2",
    font=FONT,
    highlightthickness=1,
)
theme_btn.pack(side="right", padx=(8, 16), pady=10)
_register(theme_btn, "button")

status_dot = tk.Label(header, text="●", font=(FONT_FAMILY, 11), padx=0)
status_dot.pack(side="right", padx=(8, 0))
_register(status_dot, "header")

status_label = tk.Label(header, text="Status: Disconnected", font=FONT, anchor="e")
status_label.pack(side="right", padx=(0, 4))
_register(status_label, "status")


########################################################
########################Layout##########################
########################################################

tabs_container = ttk.Frame(root, style="TFrame")
console_container = tk.Frame(root)
_register(console_container, "bg")
console_container.pack(side="bottom", fill="x")
tabs_container.pack(fill="both", expand=True)


########################################################
########################Setup Tabs######################
########################################################

notebook = ttk.Notebook(tabs_container)  # Create the Notebook widget (tabs container)
notebook.bind("<<NotebookTabChanged>>", on_tab_selected)
notebook.pack(fill="both", expand=True, padx=12, pady=(4, 8))


####################Setup Tab Sliders##################
last_sent_time = {}
last_pending_value = {}
pending_timers = {}


def send_slider_value(adc_name, value, cooldown=0.1):
    now = time.time()
    last_time = last_sent_time.get(adc_name, 0)

    def send_now(value_to_send):
        last_sent_time[adc_name] = time.time()
        command = f"{adc_name},{value_to_send}"
        send_data(command)
        timer_id = pending_timers.pop(adc_name, None)
        if timer_id is not None:
            try:
                root.after_cancel(timer_id)
            except Exception:
                pass
        last_pending_value.pop(adc_name, None)

    if now - last_time >= cooldown:
        send_now(value)
    else:
        last_pending_value[adc_name] = value

        if adc_name not in pending_timers:
            wait_ms = max(1, int((cooldown - (now - last_time)) * 1000))

            def delayed_send(name=adc_name):
                pending_timers.pop(name, None)
                latest_value = last_pending_value.get(name)
                if latest_value is not None:
                    send_now(latest_value)

            pending_timers[adc_name] = root.after(wait_ms, delayed_send)


def make_slider_card(parent, title, adc_name, accent_key, from_=1000, to=0, length=220, unit=""):
    """Build a flat mixer card: title, optional unit, vertical slider, numeric readout."""
    card = tk.Frame(parent, highlightthickness=1, highlightbackground=palette["border"], bd=0)
    card.pack(fill="x", expand=False, anchor="n")
    _register(card, "surface")

    bar = tk.Frame(card, height=4, bd=0)
    bar.pack(fill="x")
    bar.pack_propagate(False)
    _register_accent(bar, "bar", accent_key)

    name_label = tk.Label(card, text=title, font=FONT_BOLD, anchor="center", justify="center")
    name_label.pack(fill="x", padx=6, pady=(8, 0))
    _register(name_label, "label")
    _register_accent(name_label, "label", accent_key)

    if unit:
        unit_label = tk.Label(card, text=unit, font=FONT_SMALL, anchor="center", justify="center")
        unit_label.pack(fill="x", padx=6, pady=(0, 2))
        _register(unit_label, "muted")

    value_label = tk.Label(card, text="0", font=FONT_VALUE, anchor="center", justify="center")
    _register(value_label, "label")
    _register_accent(value_label, "value", accent_key)

    def on_change(val, name=adc_name, lbl=value_label):
        try:
            lbl.config(text=str(int(float(val))))
        except (TypeError, ValueError):
            lbl.config(text=str(val))
        send_slider_value(name, val)

    slider = tk.Scale(
        card,
        from_=from_,
        to=to,
        resolution=1,
        orient="vertical",
        length=length,
        showvalue=0,
        width=16,
        sliderlength=22,
        bd=0,
        highlightthickness=0,
        relief="flat",
        sliderrelief="flat",
        troughcolor=palette["trough"],
        font=FONT_SMALL,
        command=on_change,
    )
    slider.pack(padx=10, pady=4)
    _register_accent(slider, "scale", accent_key)
    value_label.pack(pady=(0, 10))
    try:
        value_label.config(text=str(int(float(slider.get()))))
    except (TypeError, ValueError):
        pass
    return slider


########################################################
#########################Tab1###########################
########################################################
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Manual Color Mixer")  # Add this frame as a tab

tab1_inner = tk.Frame(tab1)
tab1_inner.pack(fill="both", expand=True, padx=16, pady=16)
_register(tab1_inner, "bg")

tab1_hint = tk.Label(tab1_inner, text="Manual mix  ·  0–1000", font=FONT_SMALL, anchor="w")
tab1_hint.pack(fill="x", pady=(0, 10))
_register(tab1_hint, "muted_bg")

slider_row = tk.Frame(tab1_inner)
slider_row.pack(fill="both", expand=True)
_register(slider_row, "bg")

slider_names = ["Red", "Amber", "Green", "Blue", "Violet", "White", "PWM ƒ"]
slider_units = ["%", "%", "%", "%", "%", "%", "×10 kHz"]
slider_accents = ["red", "amber", "green", "blue", "violet", "white", "pwm"]
sliders = []
for i in range(7):  # Place sliders dynamically for adc49 to adc55
    adc_name = f"adc{49 + i}"  # Naming sliders adc49 to adc55
    to_value = 100 if i == 6 else 0  # Set 'to' as 100 for adc55 and 0 for others
    card_holder = tk.Frame(slider_row)
    card_holder.pack(side="left", expand=True, fill="both", padx=5)
    _register(card_holder, "bg")
    slider = make_slider_card(
        card_holder,
        slider_names[i],
        adc_name,
        slider_accents[i],
        from_=1000,
        to=to_value,
        length=220,
        unit=slider_units[i],
    )
    sliders.append(slider)


########################################################
#########################Tab2###########################
########################################################
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Classic RGB")  # Add this frame as a tab

tab2_inner = tk.Frame(tab2)
tab2_inner.pack(fill="both", expand=True, padx=16, pady=16)
_register(tab2_inner, "bg")

tab2_hint = tk.Label(tab2_inner, text="Classic RGB rainbow  ·  velocity, pastel, brightness", font=FONT_SMALL, anchor="w")
tab2_hint.pack(fill="x", pady=(0, 10))
_register(tab2_hint, "muted_bg")

slider2_row = tk.Frame(tab2_inner)
slider2_row.pack(fill="both", expand=True)
_register(slider2_row, "bg")

slider2_names = ["Velocity", "Pastel", "Brightness"]
sliders2 = []
for i in range(3):  # Place sliders dynamically
    adc_name = f"adc{56 + i}"  # Naming sliders adc56 to adc58
    card_holder = tk.Frame(slider2_row)
    card_holder.pack(side="left", expand=True, fill="both", padx=8)
    _register(card_holder, "bg")
    slider2 = make_slider_card(
        card_holder,
        slider2_names[i],
        adc_name,
        "param",
        from_=1000,
        to=0,
        length=220,
    )
    sliders2.append(slider2)


########################################################
#########################Tab3###########################
########################################################
tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Audio Effect")

tab3_outer = tk.Frame(tab3)
tab3_outer.pack(fill="both", expand=True, padx=12, pady=12)
_register(tab3_outer, "bg")

tab3_hint = tk.Label(
    tab3_outer,
    text="Audio effect  ·  band weights for each color, then upper and lower thresholds",
    font=FONT_SMALL,
    anchor="w",
)
tab3_hint.pack(fill="x", pady=(0, 8))
_register(tab3_hint, "muted_bg")

# Scrollable Canvas in Tab3
frame_container = tk.Frame(tab3_outer)
frame_container.pack(fill="both", expand=True)
_register(frame_container, "bg")

canvas3 = tk.Canvas(frame_container, highlightthickness=0, bd=0)
_register(canvas3, "canvas")
scrollbar = ttk.Scrollbar(frame_container, orient="vertical", command=canvas3.yview)
scrollbar.pack(side="right", fill="y")

canvas3.config(yscrollcommand=scrollbar.set)
canvas3.pack(side="left", fill="both", expand=True)

# Create an inner frame to hold all sliders and buttons
inner_frame = tk.Frame(canvas3)
_register(inner_frame, "bg")
canvas3_window = canvas3.create_window((0, 0), window=inner_frame, anchor="nw")


# Scroll function for mouse wheel (Windows, macOS, and Linux)
def _pointer_over_audio(event):
    widget = event.widget
    while widget is not None:
        if widget in (canvas3, inner_frame, tab3, tab3_outer, frame_container):
            return True
        try:
            widget = widget.master
        except Exception:
            break
    return False


def _on_mouse_wheel(event):
    if not _pointer_over_audio(event):
        return
    if getattr(event, "num", None) == 5:
        canvas3.yview_scroll(1, "units")
    elif getattr(event, "num", None) == 4:
        canvas3.yview_scroll(-1, "units")
    else:
        delta = event.delta
        if sys.platform == "darwin":
            canvas3.yview_scroll(int(-1 * delta), "units")
        else:
            canvas3.yview_scroll(int(-1 * (delta // 120)), "units")


canvas3.bind_all("<MouseWheel>", _on_mouse_wheel)
canvas3.bind_all("<Button-4>", _on_mouse_wheel)
canvas3.bind_all("<Button-5>", _on_mouse_wheel)


def resize_all3(event):  # Resize function
    """Resize sliders, background, and button when canvas resizes."""
    inner_frame.update_idletasks()
    canvas3.config(scrollregion=canvas3.bbox("all"))
    if event is not None and event.widget is canvas3:
        canvas3.itemconfigure(canvas3_window, width=event.width)


slider3_names = ["63Hz", "160Hz", "400Hz", "1kHz", "2.5kHz", "6.25kHz", "16kHz"]
row_names = ["Red", "Amber", "Green", "Blue", "Violet", "Upper", "Lower"]
row_accents = ["red", "amber", "green", "blue", "violet", "upper", "lower"]
sliders3 = []

# Column headers
header_pad = tk.Frame(inner_frame, width=72)
header_pad.grid(row=0, column=0, padx=(4, 8), pady=(0, 6), sticky="w")
_register(header_pad, "bg")
for col, band in enumerate(slider3_names):
    col_label = tk.Label(inner_frame, text=band, font=FONT_BOLD)
    col_label.grid(row=0, column=col + 1, pady=(0, 6))
    _register(col_label, "label_bg")

for index in range(49):  # 7 rows * 7 columns
    row = index // 7
    col = index % 7
    adc_name = f"adc{index}"

    if col == 0:
        row_wrap = tk.Frame(inner_frame)
        row_wrap.grid(row=row + 1, column=0, padx=(4, 8), pady=4, sticky="e")
        _register(row_wrap, "bg")
        swatch = tk.Frame(row_wrap, width=8, height=18)
        swatch.pack(side="left", padx=(0, 6))
        swatch.pack_propagate(False)
        _register_accent(swatch, "bar", row_accents[row])
        row_label = tk.Label(row_wrap, text=row_names[row], font=FONT_BOLD, anchor="e")
        row_label.pack(side="left")
        _register(row_label, "label_bg")
        _register_accent(row_label, "label_on_bg", row_accents[row])

    cell = tk.Frame(inner_frame, highlightthickness=1, bd=0)
    cell.grid(row=row + 1, column=col + 1, padx=5, pady=5)
    _register(cell, "surface")

    value_label = tk.Label(cell, text="0", font=FONT_SMALL)
    _register(value_label, "label")
    _register_accent(value_label, "value", row_accents[row])

    def on_change(val, name=adc_name, lbl=value_label):
        try:
            lbl.config(text=str(int(float(val))))
        except (TypeError, ValueError):
            lbl.config(text=str(val))
        send_slider_value(name, val)

    slider3 = tk.Scale(
        cell,
        from_=1000,
        to=0,
        resolution=1,
        orient="vertical",
        length=110,
        showvalue=0,
        width=14,
        sliderlength=18,
        bd=0,
        highlightthickness=0,
        relief="flat",
        sliderrelief="flat",
        font=FONT_SMALL,
        command=on_change,
    )

    slider3.set(0)  # Temporarily set to 0
    slider3.pack(padx=6, pady=(6, 2))
    value_label.pack(pady=(0, 6))
    _register_accent(slider3, "scale", row_accents[row])
    sliders3.append(slider3)


# resize_all3(None)  # Ensure scroll region is set
canvas3.bind("<Configure>", resize_all3)


########################################################
#########################Tab4###########################
########################################################
tab4 = ttk.Frame(notebook)
notebook.add(tab4, text="Color Swells")  # Add this frame as a tab

tab4_inner = tk.Frame(tab4)
tab4_inner.pack(fill="both", expand=True, padx=16, pady=16)
_register(tab4_inner, "bg")

tab4_hint = tk.Label(tab4_inner, text="Color swells  ·  velocity, pastel, brightness", font=FONT_SMALL, anchor="w")
tab4_hint.pack(fill="x", pady=(0, 10))
_register(tab4_hint, "muted_bg")

slider4_row = tk.Frame(tab4_inner)
slider4_row.pack(fill="both", expand=True)
_register(slider4_row, "bg")

slider4_names = ["Velocity", "Pastel", "Brightness"]
sliders4 = []
for i in range(3):  # Place sliders dynamically
    adc_name = f"adc{56 + i}"  # Naming sliders adc56 to adc58
    card_holder = tk.Frame(slider4_row)
    card_holder.pack(side="left", expand=True, fill="both", padx=8)
    _register(card_holder, "bg")
    slider4 = make_slider_card(
        card_holder,
        slider4_names[i],
        adc_name,
        "param",
        from_=1000,
        to=0,
        length=220,
    )
    sliders4.append(slider4)


#######################################################
###################Serial Terminal#####################
#######################################################

term_header = tk.Frame(console_container)
term_header.pack(fill="x", padx=16, pady=(10, 4))
_register(term_header, "bg")

term_title = tk.Label(term_header, text="Console", font=FONT_BOLD, anchor="w")
term_title.pack(side="left")
_register(term_title, "label_bg")

################Serial Term Text Box###################

frame = tk.Frame(console_container, highlightthickness=1, bd=0)  # Create a Frame to hold the Text and Scrollbar
frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))
_register(frame, "surface")
term_scroll = ttk.Scrollbar(frame)  # Create a Scrollbar
term_scroll.pack(side=tk.RIGHT, fill=tk.Y)
text_box = tk.Text(
    frame,
    height=6,
    width=80,
    yscrollcommand=term_scroll.set,
    font=FONT_MONO,
    relief="flat",
    bd=0,
    highlightthickness=0,
    padx=8,
    pady=8,
    wrap="word",
)  # Create a Text widget
text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
term_scroll.config(command=text_box.yview)  # Link the Scrollbar to the Text widget
_register(text_box, "text")


################Serial Term Entry Box##################
def send_data_from_entry():
    data_to_send = entry_box.get()
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}\n")
    text_box.yview(tk.END)  # Scroll to the bottom
    entry_box.delete(0, tk.END)  # Clear the entry box


def on_enter(event=None):
    data = entry_box.get()
    if data:
        send_data_from_entry()
        print(f"Sending: {data}")  # Replace with your send_data function
        entry_box.delete(0, tk.END)  # Clear the entry box after sending


cmd_row = tk.Frame(console_container)
cmd_row.pack(fill="x", padx=16, pady=(0, 14))
_register(cmd_row, "bg")

entry_box = tk.Entry(
    cmd_row,
    font=FONT_MONO,
    relief="flat",
    bd=0,
    highlightthickness=1,
)
entry_box.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
entry_box.bind("<Return>", on_enter)  # Bind Enter key to on_enter function
_register(entry_box, "entry")


################Serial Term Help Button################
def send_help():
    data_to_send = "help"
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}\n")
    text_box.yview(tk.END)  # Scroll to the bottom


def make_flat_button(parent, text, command, accent=False):
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        relief="flat",
        bd=0,
        padx=14,
        pady=6,
        cursor="hand2",
        font=FONT_BOLD,
        highlightthickness=1,
    )
    btn.pack(side="left", padx=(0, 6))
    _register(btn, "button_accent" if accent else "button")
    return btn


help_button = make_flat_button(cmd_row, "Help", send_help)
save_button = make_flat_button(cmd_row, "Save", save_slider_values, accent=True)


########################################################
########################Serial##########################
########################################################
initial_values = []  # Ensure this exists globally
def read_initial_values():
    global initial_values
    initial_values = []

    # Clear the queue first, just in case
    while not data_queue.empty():
        try:
            data_queue.get_nowait()
        except queue.Empty:
            break

    # Send the request
    send_data("read")

    # Wait and collect response lines for a short time
    collected_lines = []
    timeout = time.time() + 2  # Wait up to 2 seconds
    while time.time() < timeout:
        try:
            line = data_queue.get(timeout=0.1)
            if line.startswith("[RX]:"):
                collected_lines.append(line)
        except queue.Empty:
            continue

    # Parse collected lines
    for line in collected_lines:
        clean_line = line.replace("[RX]:", "").strip()
        if clean_line:
            parts = clean_line.split(',')
            for part in parts:
                part = part.strip()
                if part:
                    try:
                        initial_values.append(int(part))
                    except ValueError:
                        print(f"Skipping non-int: {part}")

    print("Parsed initial values:", initial_values)



def populate_slider_values():
    print("Applying initial values to sliders...")

    # Set values for sliders3
    for idx, slider in enumerate(sliders3):
        if idx < len(initial_values):
            slider.set(initial_values[idx])
        else:
            slider.set(0)

    # Set values for sliders2 (positions 56, 57, 58)
    target_indices2 = [56, 57, 58]
    for i, slider in enumerate(sliders2):
        if target_indices2[i] < len(initial_values):
            slider.set(initial_values[target_indices2[i]])
        else:
            slider.set(0)

    # Set values for sliders (positions 49 to 55)
    target_indices = [49, 50, 51, 52, 53, 54, 55]
    for i, slider in enumerate(sliders):
        if target_indices[i] < len(initial_values):
            slider.set(initial_values[target_indices[i]])
        else:
            slider.set(0)

    # Tab 4 shares adc56-58 with tab 2
    for i, slider in enumerate(sliders4):
        if target_indices2[i] < len(initial_values):
            slider.set(initial_values[target_indices2[i]])
        else:
            slider.set(0)

    if len(initial_values) > 59:
        mode = int(initial_values[59])
        if mode == 0:
            notebook.select(1)
        elif mode == 1:
            notebook.select(2)
        elif mode == 2:
            notebook.select(0)
        elif mode == 3:
            notebook.select(3)

# Initialize the serial connection
def connect():
    port = auto_connect()
    if port and connect_serial(port):
        refresh_status()
        start_serial_thread()
        read_initial_values()
        return True
    print("No device found.")
    refresh_status()
    return False


def start_serial_thread():
    """Start the serial reading thread."""
    serial_thread_instance = threading.Thread(target=serial_thread, daemon=True)
    serial_thread_instance.start()
    root.after(16, check_for_data)


def check_for_data():
    """Check for new serial data and update the GUI."""
    if not data_queue.empty():
        message = data_queue.get_nowait()  # Non-blocking get
        text_box.insert(tk.END, message + "\n")
        text_box.see(tk.END)

    refresh_status()

    root.after(16, check_for_data)


def on_quit():
    close_serial()
    root.destroy()


def _run_screenshot_pass():
    """Capture each tab in both themes when RGBWYV_SCREENSHOT_DIR is set."""
    out = os.environ.get("RGBWYV_SCREENSHOT_DIR")
    if not out:
        return
    os.makedirs(out, exist_ok=True)
    tabs = ["manual", "classic_rgb", "audio", "color_swells"]
    root.update_idletasks()
    root.update()
    time.sleep(0.2)
    for theme_name in ("dark", "light"):
        apply_theme(theme_name, persist=False)
        for index, name in enumerate(tabs):
            notebook.select(index)
            root.update_idletasks()
            root.update()
            time.sleep(0.2)
            path = os.path.join(out, f"{theme_name}_{name}.png")
            try:
                from PIL import ImageGrab
                x = root.winfo_rootx()
                y = root.winfo_rooty()
                w = root.winfo_width()
                h = root.winfo_height()
                grabbed = ImageGrab.grab(bbox=(x, y, x + w, y + h))
                grabbed.save(path)
            except Exception:
                try:
                    subprocess.run(
                        ["import", "-window", str(root.winfo_id()), path],
                        check=True,
                    )
                except Exception as exc:
                    print(f"Screenshot failed for {path}: {exc}")
                    continue
            print(f"Wrote {path}")
    root.after(100, root.destroy)


root.protocol("WM_DELETE_WINDOW", on_quit)

# Apply the saved theme (default dark) once every widget is in place.
try:
    saved_theme = load_theme()
except Exception:
    saved_theme = "dark"
apply_theme(saved_theme, persist=False)

ui_ready = True
if connect():
    populate_slider_values()

#######################################################
########################Main###########################
#######################################################


if os.environ.get("RGBWYV_SCREENSHOT_DIR"):
    ui_ready = False
    root.after(400, _run_screenshot_pass)

root.mainloop()  # Start the Tkinter event loop
