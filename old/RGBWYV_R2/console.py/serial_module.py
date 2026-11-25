# serial_module.py
import serial
import time
import queue
import serial.tools.list_ports
from ini import load_config


idn1 = load_config()  # Extract the IDN expected response
ser = None  # Initialize serial port and data queue
data_queue = queue.Queue()
connection_status = "Disconnected"  # Initial state


def connect_serial(port, baudrate=921600):
    """Connect to the serial port."""
    global ser, connection_status
    try:
        if ser and ser.is_open:
            ser.close()  # Ensure any existing connection is closed

        ser = serial.Serial(port, baudrate, timeout=0.1)
        connection_status = f"Connected to {port}"  # Update status
        print(connection_status)
        return ser
    except serial.SerialException as e:
        connection_status = "Disconnected"
        print(f"Error connecting to serial port {port}: {e}")
        return None


def send_idn_command(port):
    """Send '*idn' to the port and check if the response matches idn1."""
    try:
        with serial.Serial(port, 115200, timeout=0.1) as test_ser:
            test_ser.write(b"*idn\n")
            time.sleep(0.1)
            response = test_ser.readline().decode('utf-8').strip()
            print(f"Checked {port}: Response = {response}")  # Debugging output

            if response == idn1:
                print(f"Auto-connecting to {port}")
                return True
    except serial.SerialException as e:
        print(f"Serial error checking {port}: {e}")
    except UnicodeDecodeError:
        print(f"Received non-text response from {port}")
    return False


def auto_connect():
    """Scan all COM ports, send '*idn', and connect to the correct one."""
    global ser, connection_status
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if send_idn_command(port.device):  # If the response matches idn1
            ser = connect_serial(port.device)
            return port.device  # Return the connected port
    connection_status = "Disconnected"
    print("No matching device found.")
    return None


def serial_thread():
    """Continuously read data from the serial port and store it in a queue. Auto-reconnect on disconnect."""
    global ser, connection_status
    while True:
        if ser and ser.is_open:
            try:
                data = ser.readline().decode('utf-8').strip()
                if data:
                    data_queue.put(data)
            except serial.SerialException:
                connection_status = "Disconnected"
                print("Connection lost! Attempting to reconnect...")
                ser = None  # Mark connection as lost

        if ser is None or not ser.is_open:
            time.sleep(0.1)  # Wait before reconnecting
            print("Scanning for device...")
            auto_connect()

        time.sleep(0.1)


def send_data(data_to_send):
    """Send a message through the serial port."""
    global ser
    if ser and ser.is_open:
        ser.write(data_to_send.encode('utf-8') + b'\n')
        return f"Sent: {data_to_send}"
    return "Error: No active serial connection"


def get_connection_status():
    """Return the current connection status."""
    return connection_status