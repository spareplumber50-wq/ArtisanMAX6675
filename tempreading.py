import spidev
import time

def open_sensor(ce):
    """Open a MAX6675 on SPI bus 0, chip enable ce (0 or 1)"""
    spi = spidev.SpiDev()
    spi.open(0, ce)
    spi.max_speed_hz = 4000000
    spi.mode = 0b00
    return spi

sensor_0 = open_sensor(0)
sensor_1 = open_sensor(1)

def read_temp(spi, label="Sensor"):
    raw = spi.readbytes(2)
    value = (raw[0] << 8) | raw[1]

    # Bit 2 = open thermocouple fault flag
    if value & 0x04:
        raise RuntimeError(f"{label}: Thermocouple fault — check connection!")

    # Bits 14:3 = 12-bit temp, LSB = 0.25°C
    temp_c = (value >> 3) * 0.25
    temp_f = (temp_c * 9/5) + 32
    return temp_c, temp_f

try:
    print("Reading MAX6675 sensors on TouchBerry Pi — Ctrl+C to stop\n")
    while True:
        c0, f0 = read_temp(sensor_0, "CE0")
        c1, f1 = read_temp(sensor_1, "CE1")

        print(f"CE0 (Sensor 1): {c0:.2f}°C  /  {f0:.2f}°F")
        print(f"CE1 (Sensor 2): {c1:.2f}°C  /  {f1:.2f}°F")
        print("-" * 40)

        time.sleep(1)

except RuntimeError as e:
    print(f"Sensor error: {e}")

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    sensor_0.close()
    sensor_1.close()
