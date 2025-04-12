import serial
import argparse

def read_raw_serial(port, baud_rate):
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud.")
            while True:
                if ser.in_waiting:
                    data = ser.read(ser.in_waiting)
                    if data:
                        print("RAW:", data.hex(" "))
    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Raw Serial Dump")
    parser.add_argument("-p", "--port", default="COM3", help="Serial port (default: COM3)")
    parser.add_argument("-b", "--baud", type=int, default=416666, help="Baud rate (default: 416666)")
    args = parser.parse_args()

    read_raw_serial(args.port, args.baud)
