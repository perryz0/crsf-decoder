import serial
import struct
import argparse

CRSF_SYNC = 0xC8
CRSF_MAX_PACKET_SIZE = 64
CRSF_MIN_PACKET_SIZE = 4

def crc8_dvb_s2(crc, byte):
    crc ^= byte
    for _ in range(8):
        if crc & 0x80:
            crc = (crc << 1) ^ 0xD5
        else:
            crc = crc << 1
    return crc & 0xFF

def crc8_check(packet):
    crc = 0
    for byte in packet[2:-1]:  # skip sync and length
        crc = crc8_dvb_s2(crc, byte)
    return crc == packet[-1]

def parse_crsf_packet(packet):
    is_valid = crc8_check(packet)
    print(f"\nRaw Packet: {packet.hex(' ')} | CRC: {'OK' if is_valid else 'FAIL'}")

    if not is_valid or len(packet) < 4:
        return

    packet_type = packet[2]
    payload = packet[3:-1]

    if packet_type == 0x14:  # LINK_STATISTICS
        if len(payload) >= 4:
            rssi1, rssi2, lq = payload[0], payload[1], payload[2]
            snr = struct.unpack("b", bytes([payload[3]]))[0]
            print(f"Link Stats - RSSI: {rssi1}/{rssi2}, LQ: {lq}, SNR: {snr}")
    elif packet_type == 0x08:  # BATTERY_SENSOR
        if len(payload) >= 2:
            voltage = struct.unpack(">H", payload[0:2])[0] / 10.0
            print(f"Battery Voltage: {voltage:.1f}V")
    elif packet_type == 0x02:  # GPS
        if len(payload) >= 15:
            lat = struct.unpack(">i", payload[0:4])[0] / 1e7
            lon = struct.unpack(">i", payload[4:8])[0] / 1e7
            speed = struct.unpack(">H", payload[8:10])[0] / 36.0
            alt = struct.unpack(">H", payload[12:14])[0] - 1000
            sats = payload[14]
            print(f"GPS: {lat:.6f}, {lon:.6f}, Alt: {alt}m, Speed: {speed:.1f}m/s, Sats: {sats}")
    else:
        print(f"Unknown Packet Type: 0x{packet_type:02X} | Payload: {payload.hex()}")

def read_crsf_serial(port, baud_rate):
    try:
        with serial.Serial(port, baud_rate, timeout=1) as ser:
            print(f"Connected to {port} at {baud_rate} baud.")
            buffer = bytearray()

            while True:
                if ser.in_waiting:
                    buffer.extend(ser.read(ser.in_waiting))

                # Resync on valid CRSF packets
                while len(buffer) >= 2:
                    sync_index = buffer.find(CRSF_SYNC)
                    if sync_index == -1:
                        buffer.clear()
                        break
                    if sync_index > 0:
                        buffer = buffer[sync_index:]

                    if len(buffer) < 2:
                        break

                    length = buffer[1]
                    expected_len = length + 2  # sync + len + payload + crc

                    if length < 2 or expected_len > CRSF_MAX_PACKET_SIZE:
                        buffer.pop(0)
                        continue

                    if len(buffer) < expected_len:
                        break  # wait for more bytes

                    packet = buffer[:expected_len]
                    buffer = buffer[expected_len:]
                    parse_crsf_packet(packet)

    except serial.SerialException as e:
        print(f"Serial connection error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CRSF Telemetry Parser")
    parser.add_argument("-p", "--port", default="COM3", help="Serial port (default: COM3)")
    parser.add_argument("-b", "--baud", type=int, default=420000, help="Baud rate (default: 420000)")
    args = parser.parse_args()

    read_crsf_serial(args.port, args.baud)
