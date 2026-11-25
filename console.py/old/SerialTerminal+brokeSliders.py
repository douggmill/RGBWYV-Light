import pygame
import serial
import serial.tools.list_ports
import threading
import queue
import os

# Initialize Pygame and serial queue
pygame.init()
data_queue = queue.Queue()
ser = None

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
SLIDER_ROWS = 2
SLIDERS_PER_ROW = 28
SLIDER_COUNT = SLIDER_ROWS * SLIDERS_PER_ROW
SLIDER_HEIGHT = 200
SLIDER_WIDTH = 20
SLIDER_SPACING = 40
#SLIDER_X_OFFSET = SCREEN_WIDTH //3 # Adjusted slider X offset
MARGIN = 20


# Fonts and colors
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Background
bg_image_path = "bg.jpg"
background = pygame.image.load(bg_image_path)
background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT))

# # Sliders
# sliders = [50] * SLIDER_COUNT
# slider_positions = []
# slider_rects = []
#
#
# for row in range(SLIDER_ROWS):
#     for col in range(SLIDERS_PER_ROW):
#         x = SLIDER_X_OFFSET + col * SLIDER_SPACING
#         y = SCREEN_HEIGHT // 2 + row * (SLIDER_HEIGHT + 80) - (SLIDER_ROWS * SLIDER_HEIGHT // 2)
#         slider_positions.append((x, y))
#         slider_rects.append(pygame.Rect(x - SLIDER_WIDTH // 2, y - SLIDER_HEIGHT, SLIDER_WIDTH, SLIDER_HEIGHT))
#         labels.append(f"adc{row * SLIDERS_PER_ROW + col}")

# Sliders
sliders = [50] * SLIDER_COUNT
slider_positions = []
slider_rects = []
button_rects = []
rgb_indicators = []
labels = [] #### ADC labels
#default_slider_color = (128, 128, 128)


for row in range(SLIDER_ROWS):
    for col in range(SLIDERS_PER_ROW):
        x = MARGIN + col * SLIDER_SPACING #+ (SCREEN_WIDTH // 4) #### move sliders x and y
        y = SCREEN_HEIGHT // 2 + row * (SLIDER_HEIGHT + 80) - (SLIDER_ROWS * SLIDER_HEIGHT // 2)
        slider_positions.append((x, y))
        slider_rects.append(pygame.Rect(x - SLIDER_WIDTH // 2, y - SLIDER_HEIGHT, SLIDER_WIDTH, SLIDER_HEIGHT))
        button_rects.append(pygame.Rect(x - SLIDER_WIDTH // 2, y + 20, SLIDER_WIDTH, 30))
        rgb_indicators.append(pygame.Rect(x - SLIDER_WIDTH // 2, y - SLIDER_HEIGHT - 40, SLIDER_WIDTH, 30))
        labels.append(f"adc{row * SLIDERS_PER_ROW + col}") # adc labels

# Console and dropdown
console_width = SCREEN_WIDTH // 4
console_height = SCREEN_HEIGHT // 2
console_rect = pygame.Rect(SCREEN_WIDTH - console_width - MARGIN, MARGIN, console_width, console_height)
text_input_rect = pygame.Rect(console_rect.left + 10, console_rect.bottom - 50, console_rect.width - 20, 40)
scrollback_rect = pygame.Rect(console_rect.left + 10, console_rect.top + 10, console_rect.width - 20, console_rect.height - 100)

# Dropdown menu
dropdown_rect = pygame.Rect(console_rect.left + 10, console_rect.bottom + 10, 150, 30)
show_ports = False
port_list = []

# Variables
connection_status = "Not connected"
selected_port = ""
scrollback_lines = []
text_input = ""
input_active = False

# Load last connected port
def load_last_connected_port():
    if os.path.exists("ini.txt"):
        with open("ini.txt", "r") as f:
            return f.read().strip()
    return None

def save_last_connected_port(port):
    with open("ini.txt", "w") as f:
        f.write(port)

# Serial functions
def connect_serial(port, baudrate=115200):
    global ser
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        save_last_connected_port(port)
        print(f"Connected to BLE Central HUB on {port}")
        return True
    except serial.SerialException:
       # print(f"Error connecting to serial port {port}: {e}")
        return False


def send_slider_value(slider_index, value):
    if ser and ser.is_open:
        normalized_value = round(value / 100.0, 2)
        command = f"adc{slider_index},{normalized_value}\n"
        ser.write(command.encode('utf-8'))
        print(f"Sent command: {command}")


def update_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

# Serial thread
def serial_thread():
    while True:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    data_queue.put(data)
            except serial.SerialException:
                break

def process_incoming_data():
    while not data_queue.empty():
        data = data_queue.get()
        scrollback_lines.append(data)


# def send_slider_value(slider_index, value):
#     if ser and ser.is_open:
#         normalized_value = round(value / 100.0, 2)
#         command = f"adc{slider_index},{normalized_value}\n"
#         ser.write(command.encode('utf-8'))
#         print(f"Sent command: {command}")


# Start serial thread
thread = threading.Thread(target=serial_thread, daemon=True)
thread.start()

# Initialize ports
last_port = load_last_connected_port()
if last_port:
    connected = connect_serial(last_port)
    if connected:
        connection_status = f"Connected to {last_port}"
        selected_port = last_port

# Main loop
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Lighting Console 003")
running = True
clock = pygame.time.Clock()

while running:
    screen.blit(background, (0, 0))

    # Draw sliders, buttons, and indicators
    for i, (x, y) in enumerate(slider_positions):
        pygame.draw.rect(screen, GRAY, slider_rects[i])
        handle_y = y - int(sliders[i] * 3)
        pygame.draw.rect(screen, WHITE, (x - 10, handle_y, 20, 10))
        slider_value_text = small_font.render(str(sliders[i]), True, WHITE)
        screen.blit(slider_value_text, (x - 15, y + 20))

    # Button
    pygame.draw.rect(screen, GRAY, button_rects[i])
    button_text = small_font.render(f"B{i + 1}", True, WHITE)
    screen.blit(button_text, (
    button_rects[i].centerx - button_text.get_width() // 2, button_rects[i].centery - button_text.get_height() // 2))

    # RGB Indicator
    color = RED if i % 3 == 0 else GREEN if i % 3 == 1 else BLUE
    pygame.draw.rect(screen, color, rgb_indicators[i])



    # Draw console panel
    pygame.draw.rect(screen, BLACK, console_rect)
    pygame.draw.rect(screen, WHITE, text_input_rect, 2)
    pygame.draw.rect(screen, WHITE, scrollback_rect, 2)

    # Render scrollback
    y_offset = scrollback_rect.top + 10
    for line in scrollback_lines[-10:]:
        text_surface = small_font.render(line, True, WHITE)
        screen.blit(text_surface, (scrollback_rect.left + 5, y_offset))
        y_offset += 20

    # Render text input
    input_surface = small_font.render(text_input, True, WHITE)
    screen.blit(input_surface, (text_input_rect.left + 5, text_input_rect.top + 10))

    # Dropdown menu
    pygame.draw.rect(screen, WHITE, dropdown_rect)
    dropdown_label = font.render("Ports", True, BLACK)
    screen.blit(dropdown_label, (dropdown_rect.left + 5, dropdown_rect.top + 5))

    if show_ports:
        for i, port in enumerate(port_list):
            port_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.bottom + (i * 30), 150, 30)
            pygame.draw.rect(screen, WHITE, port_rect)
            port_label = small_font.render(port, True, BLACK)
            screen.blit(port_label, (port_rect.left + 5, port_rect.top + 5))

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for i, rect in enumerate(slider_rects):
                if rect.collidepoint(event.pos):
                    sliders[i] = max(0, min(100, (slider_positions[i][1] - event.pos[1]) // 3))
                    send_slider_value(i, sliders[i])

            if text_input_rect.collidepoint(event.pos):
                input_active = True
            else:
                input_active = False

        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:


            for i, rect in enumerate(slider_rects):
                if rect.collidepoint(event.pos):
                    sliders[i] = max(0, min(100, (slider_positions[i][1] - event.pos[1]) * 100 // SLIDER_HEIGHT))
                    send_slider_value(i, sliders[i])


            if text_input_rect.collidepoint(event.pos):
                input_active = True ############################## sends adc values on slider mouse click
            else:
                input_active = False

            if dropdown_rect.collidepoint(event.pos):
                show_ports = not show_ports
                port_list = update_ports()

            if show_ports:
                for i, port in enumerate(port_list):
                    port_rect = pygame.Rect(dropdown_rect.left, dropdown_rect.bottom + (i * 30), 150, 30)
                    if port_rect.collidepoint(event.pos):
                        selected_port = port
                        connected = connect_serial(port)
                        if connected:
                            connection_status = f"Connected to {port}"
                        else:
                            connection_status = "Connection failed"
                        show_ports = False

            else:
                for i, rect in enumerate(slider_rects):
                    if rect.collidepoint(event.pos):
                        sliders[i] = max(0, min(100, (slider_positions[i][1] - event.pos[1]) * 100 / SLIDER_HEIGHT))
                        send_slider_value(i, sliders[i])

        elif event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:
                if ser and ser.is_open:
                    ser.write((text_input + "\n").encode('utf-8'))
                    scrollback_lines.append(f"> {text_input}")
                    text_input = ""
            elif event.key == pygame.K_BACKSPACE:
                text_input = text_input[:-1]
            else:
                text_input += event.unicode

    # Update display
    process_incoming_data()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
