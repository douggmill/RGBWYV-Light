########################main.py#########################

########################################################
########################Modules#########################
########################################################
import tkinter as tk
from tkinter import ttk, Menu
from PIL import Image, ImageTk  # for icon
from PIL.ImageTk import PhotoImage  # for icon
import threading
from serial_module import connect_serial, send_data, serial_thread, data_queue, auto_connect, get_connection_status, close_serial
import os
import sys
import time
import queue
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ui_ready = False

initial_values = []


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
root.geometry("520x700")  # Set a specific window size
root.resizable(False, True)  # Allow resizing only in the Y direction


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
    selected_tab = notebook.index(notebook.select())
    if selected_tab == 0:
        send_manual_command()
    elif selected_tab == 1:
        send_RGB_wave_command()
    elif selected_tab == 2:
        send_audio_command()
    elif selected_tab == 3:
        send_RGB_retro_command()


menu_bar = Menu(root)  # Create menu bar
root.config(menu=menu_bar)
file_menu = Menu(menu_bar, tearoff=0)  # Add File menu
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Open Config", command=open_config)  # Add "Open Config" option
file_menu.add_command(label="Save Values", command=save_slider_values)

########################################################
########################Setup Tabs######################
########################################################

notebook = ttk.Notebook(root)  # Create the Notebook widget (tabs container)
notebook.bind("<<NotebookTabChanged>>", on_tab_selected)
notebook.pack(fill="both", expand=True)
tab_fonts = ("Arial", 10)


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


########################################################
#########################Tab1###########################
########################################################
tab1 = ttk.Frame(notebook)
notebook.add(tab1, text="Manual Color Mixer")  # Add this frame as a tab


##########Tabs 1 & 2 Resizeable Background###########
def resize_background(event):
    """Resize and update the canvas background image when the window is resized."""
    new_width, new_height = event.width, event.height
    resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    bg_image = ImageTk.PhotoImage(resized_image)
    canvas1.delete("bg_image")  # Remove previous background
    canvas1.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
    canvas1.bg_image = bg_image  # Keep reference to avoid garbage collection
    canvas2.delete("bg_image")  # Remove previous background
    canvas2.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
    canvas2.bg_image = bg_image  # Keep reference to avoid garbage collection
    canvas4.delete("bg_image")  # Remove previous background
    canvas4.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
    canvas4.bg_image = bg_image  # Keep reference to avoid garbage collection


image_path = os.path.join(BASE_DIR, "SMPTE_Color_Bars.png")  # Load and set up background image
original_image = Image.open(image_path)
canvas1 = tk.Canvas(tab1)
canvas1.pack(fill="both", expand=True)
resized_image = original_image.resize((800, 500), Image.Resampling.LANCZOS)  # Set an initial background image
bg_image = ImageTk.PhotoImage(resized_image)
canvas1.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
canvas1.bg_image = bg_image  # Keep reference


#####################Tab1 Sliders#######################
def resize_sliders(event):
    """Dynamically adjust slider positions based on canvas size."""
    canvas_width = canvas1.winfo_width()
    spacing = canvas_width / (len(slider_colors))  # Dynamic spacing

    for i, frame in enumerate(slider_frames):
        x_position = int(spacing * (i + 0.5))
        canvas1.coords(frame, x_position, 100)  # Update the window position


slider_colors = ["red", "yellow", "green", "blue", "purple", "white", "black"]
slider_backgrounds = ["#c0c0c0", "#c0c000", "#00c0c0", "#00c000", "#c000c0", "#c00000", "#0000c0"]
slider_names = ["Red \n(%)", "Amber \n(%)", "Green \n(%)", "Blue \n(%)", "Violet \n(%)", "White \n(%)",
                "PWM ƒ \n(x10kHz)"]
slider_texts = ["white", "#8B0000", "#E0FFFF", "#E0FFFF", "#FFD700", "black", "white"]
slider_labels = ["black", "#8B0000", "#8B0000", "#00008B", "#E0FFFF", "white", "#E0FFFF"]
sliders = []
slider_frames = []
for i in range(7):  # Place sliders dynamically for adc49 to adc55
    adc_name = f"adc{49 + i}"  # Naming sliders adc49 to adc55
    frame = tk.Frame(canvas1, bg=slider_backgrounds[i])
    label = tk.Label(frame, text=slider_names[i], fg=slider_labels[i], bg=slider_backgrounds[i])
    label.pack()

    # Set the 'to' value to 1 for adc55 (i == 6)
    to_value = 100 if i == 6 else 0  # Set 'to' as 1 for adc55 and 0 for others

    slider = tk.Scale(
        frame,
        from_=1000,
        to=to_value,  # Use the adjusted 'to' value
        resolution=1,
        orient="vertical",
        length=120,
        fg=slider_texts[i],
        bg=slider_colors[i],  # Ensure each slider has a unique color
        command=lambda value, name=adc_name: send_slider_value(name, value)
    )
    slider.pack()
    frame.pack(side="left", padx=10, pady=10)
    slider.pack()
    sliders.append(slider)
    slider_frames.append(canvas1.create_window(0, 100, window=frame))  # Placeholder position


#########################Resize Tab1###########################
def resize_all(event):
    """Handles resizing of the background, sliders, and button together."""
    resize_background(event)  # Resize and update background image
    resize_sliders(event)  # Reposition sliders dynamically


canvas1.bind("<Configure>", resize_all)


########################################################
#########################Tab2###########################
########################################################
tab2 = ttk.Frame(notebook)
notebook.add(tab2, text="Classic RGB")  # Add this frame as a tab
canvas2 = tk.Canvas(tab2)
canvas2.pack(fill="both", expand=True)
canvas2.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
canvas2.bg_image = bg_image  # Keep reference to avoid garbage collection


#####################Tab2 Sliders#######################
def resize_sliders2(event):
    """Dynamically adjust slider positions based on canvas size."""
    canvas_width = canvas2.winfo_width()
    # spacing = canvas_width / (len(slider2_colors))  # Dynamic spacing
    spacing = canvas_width / 3.5  # Dynamic spacing

    for i, frame in enumerate(slider2_frames):
        x_position = int(spacing * (i + 0.75))
        canvas2.coords(frame, x_position, 100)  # Update the window position


def resize_all2(event):
    """Handles resizing of the background, sliders, and button together."""
    resize_background(event)  # Resize and update background image
    resize_sliders2(event)  # Reposition sliders dynamically


slider2_colors = ["red", "green", "blue"]
slider2_backgrounds = ["#c0c000", "#00c000", "#c00000"]
slider2_names = ["Velocity", "Pastel", "Brightness"]
slider2_texts = ["white", "#E0FFFF", "#E0FFFF"]
slider2_labels = ["#8B0000", "#00008B", "white"]
sliders2 = []
slider2_frames = []
for i in range(3):  # Place sliders dynamically
    adc_name = f"adc{56 + i}"  # Naming sliders adc56 to adc58
    frame = tk.Frame(canvas2, bg=slider2_backgrounds[i])
    label = tk.Label(frame, text=slider2_names[i], fg=slider2_labels[i], bg=slider2_backgrounds[i])
    label.pack()
    slider2 = tk.Scale(
        frame,
        from_=1000,
        to=0,
        resolution=1,
        orient="vertical",
        length=120,
        fg=slider2_texts[i],
        bg=slider2_colors[i],
        command=lambda value, name=adc_name: send_slider_value(name, value)
    )
    slider2.pack()
    sliders2.append(slider2)
    slider2_frames.append(canvas2.create_window(0, 100, window=frame))  # Placeholder position

# Bind all resizing functions to the <Configure> event of the canvas
canvas2.bind("<Configure>", resize_all2)


# ########################################################
# #########################Tab3###########################
# ########################################################


tab3 = ttk.Frame(notebook)
notebook.add(tab3, text="Audio Effect")
notebook.pack(fill="both", expand=True)

# Scrollable Canvas in Tab3
frame_container = tk.Frame(tab3)
frame_container.pack(fill="both", expand=True)

canvas3 = tk.Canvas(frame_container)
scrollbar = tk.Scrollbar(frame_container, orient="vertical", command=canvas3.yview)
scrollbar.pack(side="right", fill="y")

canvas3.config(yscrollcommand=scrollbar.set)
canvas3.pack(side="left", fill="both", expand=True)

# Create an inner frame to hold all sliders and buttons
inner_frame = tk.Frame(canvas3)
canvas3.create_window((0, 0), window=inner_frame, anchor="nw")


# Scroll function for mouse wheel
def _on_mouse_wheel(event):
    canvas3.yview_scroll(-1 * (event.delta // 120), "units")


canvas3.bind_all("<MouseWheel>", _on_mouse_wheel)


def resize_all3(event):  # Resize function
    """Resize sliders, background, and button when canvas resizes."""
    inner_frame.update_idletasks()
    canvas3.config(scrollregion=canvas3.bbox("all"))
    # resize_background(event)  # Resize and update background image




row_colors = ["red", "yellow", "green", "blue", "purple", "white", "black"]
slider3_names = ["63Hz", "160Hz", "400Hz", "1kHz", "2.5kHz", "6.25kHz", "16kHz"]
sliders3 = []

for index in range(49):  # 7 rows * 7 columns
    row = index // 7
    col = index % 7
    adc_name = f"adc{index}"

    frame = tk.Frame(inner_frame, bg=row_colors[row])
    if row == 0:
        label = tk.Label(frame, text=slider3_names[col], fg="black")
        label.pack()

    foreground = "white" if row in (0, 3, 6) else "black"

    slider3 = tk.Scale(
        frame,
        from_=1000,
        to=0,
        resolution=1,
        orient="vertical",
        length=120,
        fg=foreground,
        bg=row_colors[row],
        command=lambda value, name=adc_name: send_slider_value(name, value)
    )

    slider3.set(0)  # Temporarily set to 0
    slider3.pack()
    sliders3.append(slider3)
    frame.grid(row=row, column=col, padx=10, pady=10)


# resize_all3(None)  # Ensure scroll region is set
canvas3.bind("<Configure>", resize_all3)



########################################################
#########################Tab4###########################
########################################################
tab4 = ttk.Frame(notebook)
notebook.add(tab4, text="Color Swells")  # Add this frame as a tab
canvas4 = tk.Canvas(tab4)
canvas4.pack(fill="both", expand=True)
canvas4.create_image(0, 0, image=bg_image, anchor="nw", tags="bg_image")
canvas4.bg_image = bg_image  # Keep reference to avoid garbage collection


#####################Tab4 Sliders#######################
def resize_sliders4(event):
    """Dynamically adjust slider positions based on canvas size."""
    canvas_width = canvas4.winfo_width()
    # spacing = canvas_width / (len(slider2_colors))  # Dynamic spacing
    spacing = canvas_width / 3.5  # Dynamic spacing

    for i, frame in enumerate(slider4_frames):
        x_position = int(spacing * (i + 0.75))
        canvas4.coords(frame, x_position, 100)  # Update the window position


def resize_all4(event):
    """Handles resizing of the background, sliders, and button together."""
    resize_background(event)  # Resize and update background image
    resize_sliders4(event)  # Reposition sliders dynamically


slider4_colors = ["red", "green", "blue"]
slider4_backgrounds = ["#c0c000", "#00c000", "#c00000"]
slider4_names = ["Velocity", "Pastel", "Brightness"]
slider4_texts = ["white", "#E0FFFF", "#E0FFFF"]
slider4_labels = ["#8B0000", "#00008B", "white"]
sliders4 = []
slider4_frames = []
for i in range(3):  # Place sliders dynamically
    adc_name = f"adc{56 + i}"  # Naming sliders adc56 to adc58
    frame = tk.Frame(canvas4, bg=slider4_backgrounds[i])
    label = tk.Label(frame, text=slider4_names[i], fg=slider4_labels[i], bg=slider4_backgrounds[i])
    label.pack()
    slider4 = tk.Scale(
        frame,
        from_=1000,
        to=0,
        resolution=1,
        orient="vertical",
        length=120,
        fg=slider4_texts[i],
        bg=slider4_colors[i],
        command=lambda value, name=adc_name: send_slider_value(name, value)
    )
    slider4.pack()
    sliders4.append(slider4)
    slider4_frames.append(canvas4.create_window(0, 100, window=frame))  # Placeholder position

# Bind all resizing functions to the <Configure> event of the canvas
canvas4.bind("<Configure>", resize_all4)




#######################################################
###################Serial Terminal#####################
#######################################################


################Serial Term Text Box###################

frame = tk.Frame(root)  # Create a Frame to hold the Text and Scrollbar
frame.pack(padx=10, pady=10)
scrollbar = tk.Scrollbar(frame)  # Create a Scrollbar
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_box = tk.Text(frame, height=10, width=150, yscrollcommand=scrollbar.set)  # Create a Text widget
text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=text_box.yview)  # Link the Scrollbar to the Text widget


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


entry_box = tk.Entry(root, width=140)
entry_box.pack(padx=10, pady=10)
entry_box.bind("<Return>", on_enter)  # Bind Enter key to on_enter function


################Serial Term Help Button################
def send_help():
    data_to_send = "help"
    response = send_data(data_to_send)
    text_box.insert(tk.END, f"{response}\n")
    text_box.yview(tk.END)  # Scroll to the bottom


help_button = tk.Button(root, text="Help", command=send_help)
help_button.pack(pady=5)


################Serial Term Status################
connection_status = tk.StringVar(root)  # Connection status
connection_status.set("Not connected")
status_label = tk.Label(root, text="Disconnected", fg="red")
status_label.pack(pady=5)


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
        status_label.config(text=f"Connected to {port}")
        start_serial_thread()
        read_initial_values()
        return True
    print("No device found.")
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

    status = get_connection_status()  # Update connection status
    status_label.config(text=f"Status: {status}", fg="green" if "Connected" in status else "red")

    root.after(16, check_for_data)


def on_quit():
    close_serial()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_quit)

ui_ready = True
if connect():
    populate_slider_values()

#######################################################
########################Main###########################
#######################################################


root.mainloop()  # Start the Tkinter event loop
