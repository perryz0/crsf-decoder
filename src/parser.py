import serial
import struct
import argparse

# TODO: Change default USB COM port (depends on the system), as needed
DEFAULT_SERIAL_PORT = "COM3"
DEFAULT_BAUD_RATE = 115200

# CRSF packet type mappings
CRSF_FRAMETYPE_LINK_STATISTICS = 0x14
CRSF_FRAMETYPE_BATTERY_SENSOR = 0x08
CRSF_FRAMETYPE_GPS = 0x02

def parse_crsf_packet(packet):
    """Parses a CRSF packet and extracts relevant telemetry data."""
    if len(packet) < 4:
        return None  # Invalid packet

    packet_type = packet[2]

    if packet_type == CRSF_FRAMETYPE_LINK_STATISTICS:
        rssi = packet[3]  # Extract RSSI value
        lq = packet[5]  # Extract Link Quality
        return {"RSSI": rssi, "LQ": lq}

    elif packet_type == CRSF_FRAMETYPE_BATTERY_SENSOR:
        voltage = struct.unpack(">H", packet[3:5])[0] / 10.0  # Convert mV to V
        return {"Battery Voltage": voltage}

    elif packet_type == CRSF_FRAMETYPE_GPS:
        lat = struct.unpack(">i", packet[3:7])[0] / 1e7
        lon = struct.unpack(">i", packet[7:11])[0] / 1e7
        return {"Latitude": lat, "Longitude": lon}

    return None  # Unknown packet type

def read_crsf_serial(port, baud_rate):
    """Reads CRSF packets from the specified serial port and parses telemetry data."""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud.")
            while True:
                packet = ser.read(64)  # Up to 64 bytes (max CRSF packet size)
                if len(packet) > 0:
                    parsed_data = parse_crsf_packet(packet)
                    if parsed_data:
                        print(parsed_data)
    except serial.SerialException as e:
        print(f"⚠️ Serial connection error: {e}")

if __name__ == "__main__":
    # Argparsing for custom port and baud rate
    parser = argparse.ArgumentParser(description="Parse CRSF telemetry from a serial port.")
    parser.add_argument("-p", "--port", default=DEFAULT_SERIAL_PORT, help="Serial port (default: COM3)")
    parser.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD_RATE, help="Baud rate (default: 115200)")

    args = parser.parse_args()
    
    # Start reading telem-mirror data binaries
    read_crsf_serial(args.port, args.baud)
