import pygame
import serial
import serial.tools.list_ports
import threading
import queue
import os

data_queue = queue.Queue()
ser = None

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # Full HD resolution
SLIDER_ROWS = 2
SLIDERS_PER_ROW = 28
SLIDER_COUNT = SLIDER_ROWS * SLIDERS_PER_ROW
SLIDER_HEIGHT = 200
SLIDER_WIDTH = 20
SLIDER_SPACING = 40
MARGIN = 20

# Initialize Pygame
pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Lighting Console 001")

# Fonts and colors
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

default_slider_color = (128, 128, 128)

# Background
bg_color = BLACK

# Sliders
sliders = [50] * SLIDER_COUNT
slider_positions = []
slider_rects = []
button_rects = []
rgb_indicators = []

for row in range(SLIDER_ROWS):
    for col in range(SLIDERS_PER_ROW):
        x = MARGIN + col * SLIDER_SPACING + (SCREEN_WIDTH // 4)
        y = SCREEN_HEIGHT // 2 + row * (SLIDER_HEIGHT + 80) - (SLIDER_ROWS * SLIDER_HEIGHT // 2)
        slider_positions.append((x, y))
        slider_rects.append(pygame.Rect(x - SLIDER_WIDTH // 2, y - SLIDER_HEIGHT, SLIDER_WIDTH, SLIDER_HEIGHT))
        button_rects.append(pygame.Rect(x - SLIDER_WIDTH // 2, y + 20, SLIDER_WIDTH, 30))
        rgb_indicators.append(pygame.Rect(x - SLIDER_WIDTH // 2, y - SLIDER_HEIGHT - 40, SLIDER_WIDTH, 30))

# Text console and connection panel
console_width = SCREEN_WIDTH // 4
console_rect = pygame.Rect(MARGIN, MARGIN, console_width - 2 * MARGIN, SCREEN_HEIGHT - 2 * MARGIN)
text_input_rect = pygame.Rect(console_rect.left + 10, console_rect.bottom - 60, console_rect.width - 20, 40)
scrollback_rect = pygame.Rect(console_rect.left + 10, console_rect.top + 50, console_rect.width - 20, console_rect.height - 120)

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
        print(f"Connected to Arduino on {port}")
        save_last_connected_port(port)
        return ser
    except serial.SerialException as e:
        print(f"Error connecting to serial port {port}: {e}")
        return None

def send_slider_value(slider_index, value):
    if ser and ser.is_open:
        normalized_value = round(value / 100.0, 2)
        command = f"adc{slider_index},{normalized_value}\n"
        ser.write(command.encode('utf-8'))
        print(f"Sent command: {command}")

def send_text_input():
    global text_input
    if ser and ser.is_open and text_input:
        command = text_input + "\n"
        ser.write(command.encode('utf-8'))
        scrollback_lines.append(f"> {text_input}")
        text_input = ""

def update_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]

def serial_thread():
    while True:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    data_queue.put(data)
            except serial.SerialException as e:
                print(f"Serial error: {e}")
                break

def process_incoming_data():
    while not data_queue.empty():
        data = data_queue.get()
        print(f"Received: {data}")
        scrollback_lines.append(data)

# Start the serial thread
thread = threading.Thread(target=serial_thread, daemon=True)
thread.start()

# Main loop
running = True
clock = pygame.time.Clock()
last_port = load_last_connected_port()
if last_port:
    ser = connect_serial(last_port)
    selected_port = last_port

while running:
    screen.fill(bg_color)

    # Draw console panel
    pygame.draw.rect(screen, GRAY, console_rect)
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

    # Draw sliders, buttons, and indicators
    for i in range(SLIDER_COUNT):
        # Slider
        pygame.draw.rect(screen, default_slider_color, slider_rects[i])
        handle_y = slider_positions[i][1] - int(sliders[i] * SLIDER_HEIGHT / 100)
        pygame.draw.rect(screen, WHITE, (slider_positions[i][0] - SLIDER_WIDTH // 2, handle_y, SLIDER_WIDTH, 10))

        # Button
        pygame.draw.rect(screen, GRAY, button_rects[i])
        button_text = small_font.render(f"B{i+1}", True, WHITE)
        screen.blit(button_text, (button_rects[i].centerx - button_text.get_width() // 2, button_rects[i].centery - button_text.get_height() // 2))

        # RGB Indicator
        color = RED if i % 3 == 0 else GREEN if i % 3 == 1 else BLUE
        pygame.draw.rect(screen, color, rgb_indicators[i])

    # Draw connection status
    status_text = font.render(f"Connection: {connection_status}", True, WHITE)
    screen.blit(status_text, (MARGIN, MARGIN))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if text_input_rect.collidepoint(event.pos):
                input_active = True
            else:
                input_active = False

            for i, rect in enumerate(slider_rects):
                if rect.collidepoint(event.pos):
                    sliders[i] = max(0, min(100, (slider_positions[i][1] - event.pos[1]) * 100 // SLIDER_HEIGHT))
                    send_slider_value(i, sliders[i])

        elif event.type == pygame.KEYDOWN and input_active:
            if event.key == pygame.K_RETURN:
                send_text_input()
            elif event.key == pygame.K_BACKSPACE:
                text_input = text_input[:-1]
            else:
                text_input += event.unicode

    # Update display
    process_incoming_data()
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
