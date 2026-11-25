# serial_module.py
import serial
import time
import queue
import threading
import serial.tools.list_ports
from ini import load_config


idn1 = load_config()  # Extract the IDN expected response
ser = None  # Initialize serial port and data queue
serial_lock = threading.Lock()
data_queue = queue.Queue()
connection_status = "Disconnected"  # Initial state
BAUD = 921600


def connect_serial(port, baudrate=BAUD):
    """Connect to the serial port."""
    global ser, connection_status
    if not port:
        connection_status = "Disconnected"
        return None
    try:
        with serial_lock:
            if ser and ser.is_open:
                ser.close()

            ser = serial.Serial(port, baudrate, timeout=0.1)
            connection_status = f"Connected to {port}"
        print(connection_status)
        return ser
    except serial.SerialException as e:
        with serial_lock:
            ser = None
            connection_status = "Disconnected"
        print(f"Error connecting to serial port {port}: {e}")
        return None


def send_idn_command(port):
    """Send '*idn' to the port and check if the response matches idn1."""
    try:
        with serial.Serial(port, BAUD, timeout=0.2) as test_ser:
            test_ser.reset_input_buffer()
            test_ser.write(b"*idn\n")
            time.sleep(0.15)
            response = test_ser.readline().decode("utf-8", errors="replace").strip()
            # The central may print a boot banner first; keep reading briefly.
            deadline = time.time() + 0.4
            while response != idn1 and time.time() < deadline:
                line = test_ser.readline().decode("utf-8", errors="replace").strip()
                if line:
                    response = line
            print(f"Checked {port}: Response = {response}")

            if response == idn1:
                print(f"Auto-connecting to {port}")
                return True
    except serial.SerialException as e:
        print(f"Serial error checking {port}: {e}")
    except UnicodeDecodeError:
        print(f"Received non-text response from {port}")
    return False


def _port_sort_key(port):
    """Prefer USB CDC ACM devices (XIAO), then typical USB serial names."""
    dev = port.device or ""
    if "ttyACM" in dev:
        return (0, dev)
    if "cu.usbmodem" in dev or "tty.usbmodem" in dev:
        return (1, dev)
    if dev.upper().startswith("COM"):
        return (2, dev)
    return (3, dev)


def auto_connect():
    """Scan serial ports (preferring /dev/ttyACM*), send '*idn', and connect to the central."""
    global ser, connection_status
    ports = sorted(serial.tools.list_ports.comports(), key=_port_sort_key)
    for port in ports:
        if send_idn_command(port.device):
            ser = connect_serial(port.device)
            return port.device
    connection_status = "Disconnected"
    print("No matching device found.")
    return None


def serial_thread():
    """Continuously read data from the serial port and store it in a queue. Auto-reconnect on disconnect."""
    global ser, connection_status
    while True:
        data = None
        need_reconnect = False
        with serial_lock:
            if ser and ser.is_open:
                try:
                    raw = ser.readline()
                    if raw:
                        data = raw.decode("utf-8", errors="replace").strip()
                except serial.SerialException:
                    connection_status = "Disconnected"
                    print("Connection lost! Attempting to reconnect...")
                    try:
                        ser.close()
                    except Exception:
                        pass
                    ser = None
                    need_reconnect = True
            else:
                need_reconnect = True

        if data:
            data_queue.put(data)

        if need_reconnect:
            time.sleep(0.5)
            print("Scanning for device...")
            auto_connect()
        else:
            time.sleep(0.01)


def send_data(data_to_send):
    """Send a message through the serial port. Adds a single trailing newline if missing."""
    global ser
    if data_to_send is None:
        return "Error: No data"
    payload = data_to_send
    if not payload.endswith("\n"):
        payload = payload + "\n"
    with serial_lock:
        if ser and ser.is_open:
            ser.write(payload.encode("utf-8"))
            return f"Sent: {payload.rstrip(chr(10) + chr(13))}"
    return "Error: No active serial connection"


def close_serial():
    """Close the serial port if it is open."""
    global ser, connection_status
    with serial_lock:
        if ser and ser.is_open:
            try:
                ser.close()
            except Exception:
                pass
        ser = None
        connection_status = "Disconnected"


def get_connection_status():
    """Return the current connection status."""
    return connection_status
