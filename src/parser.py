import serial
import struct
import argparse
import time
from enum import IntEnum

# CRSF Constants
CRSF_SYNC = 0xC8
CRSF_MAX_PACKET_SIZE = 64

# Default Serial Port Settings
DEFAULT_SERIAL_PORT = "COM3"
DEFAULT_BAUD_RATE = 115200

class CRSFPacketTypes(IntEnum):
    """CRSF Packet Type Definitions"""
    GPS = 0x02
    VARIO = 0x07
    BATTERY_SENSOR = 0x08
    BARO_ALT = 0x09
    HEARTBEAT = 0x0B
    VIDEO_TRANSMITTER = 0x0F
    LINK_STATISTICS = 0x14
    RC_CHANNELS_PACKED = 0x16
    ATTITUDE = 0x1E
    FLIGHT_MODE = 0x21
    DEVICE_INFO = 0x29
    CONFIG_READ = 0x2C
    CONFIG_WRITE = 0x2D
    RADIO_ID = 0x3A

def crc8_dvb_s2(crc, byte):
    """Compute CRC-8 (DVB-S2)"""
    crc ^= byte
    for _ in range(8):
        if crc & 0x80:
            crc = (crc << 1) ^ 0xD5
        else:
            crc = crc << 1
    return crc & 0xFF

def crc8_check(packet):
    """Validate CRSF Packet CRC"""
    return crc8_dvb_s2(0, packet[2:-1]) == packet[-1]

def parse_crsf_packet(packet):
    """Parses CRSF telemetry data and prints human-readable output"""
    if len(packet) < 4:
        print(f"⚠️ Skipping invalid packet: {packet.hex()}")
        return None  

    if packet[0] != CRSF_SYNC:
        print(f"⚠️ Skipping non-CRSF packet: {packet.hex()}")
        return None  

    if not crc8_check(packet):
        print(f"❌ CRC Mismatch: {packet.hex()}")
        return None

    packet_type = packet[2]

    if packet_type == CRSFPacketTypes.LINK_STATISTICS:
        rssi1 = packet[3]
        rssi2 = packet[4]
        lq = packet[5]
        snr = struct.unpack("b", bytes([packet[6]]))[0]  # Signed int
        print(f"📶 RSSI: {rssi1}/{rssi2}, LQ: {lq}, SNR: {snr}")

    elif packet_type == CRSFPacketTypes.BATTERY_SENSOR:
        voltage = struct.unpack(">H", packet[3:5])[0] / 10.0
        print(f"🔋 Battery: {voltage:.1f}V")

    elif packet_type == CRSFPacketTypes.GPS:
        lat = struct.unpack(">i", packet[3:7])[0] / 1e7
        lon = struct.unpack(">i", packet[7:11])[0] / 1e7
        speed = struct.unpack(">H", packet[11:13])[0] / 36.0
        altitude = struct.unpack(">H", packet[15:17])[0] - 1000
        sats = packet[17]
        print(f"📡 GPS: {lat:.6f}, {lon:.6f} | Alt: {altitude}m | Speed: {speed:.1f}m/s | Sats: {sats}")

    elif packet_type == CRSFPacketTypes.ATTITUDE:
        pitch = struct.unpack(">h", packet[3:5])[0] / 10000.0
        roll = struct.unpack(">h", packet[5:7])[0] / 10000.0
        yaw = struct.unpack(">h", packet[7:9])[0] / 10000.0
        print(f"🎛️ Attitude: Pitch={pitch:.2f} Roll={roll:.2f} Yaw={yaw:.2f}")

    elif packet_type == CRSFPacketTypes.FLIGHT_MODE:
        mode = ''.join(map(chr, packet[3:-2]))
        print(f"✈️ Flight Mode: {mode}")

    else:
        print(f"🛑 Unknown Packet Type: 0x{packet_type:02X} | Data: {packet.hex()}")

def read_crsf_serial(port, baud_rate):
    """Reads CRSF packets from a serial port and decodes telemetry"""
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"✅ Connected to {port} at {baud_rate} baud.")
            buffer = bytearray()

            while True:
                if ser.in_waiting > 0:
                    buffer.extend(ser.read(ser.in_waiting))

                while len(buffer) >= 4:
                    expected_len = buffer[1] + 2
                    if expected_len > CRSF_MAX_PACKET_SIZE or expected_len < 4:
                        print(f"⚠️ Bad packet length: {expected_len}. Resetting buffer.")
                        buffer.clear()
                        break

                    if len(buffer) >= expected_len:
                        packet = buffer[:expected_len]
                        buffer = buffer[expected_len:]  # Remove parsed data
                        parse_crsf_packet(packet)  # Process CRSF packet
                    else:
                        break

    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse CRSF telemetry from a serial port.")
    parser.add_argument("-p", "--port", default=DEFAULT_SERIAL_PORT, help="Serial port (default: COM3)")
    parser.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD_RATE, help="Baud rate (default: 115200)")

    args = parser.parse_args()
    
    read_crsf_serial(args.port, args.baud)
