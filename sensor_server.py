#!/usr/bin/env python3
import time
import os

TEMP_FILE = "/home/pi/.var/app/org.artisan_scope.artisan/data/temps.txt"
LOCK_FILE = "/tmp/i2c.lock"

time.sleep(10)
print("Sensor server starting...")

while True:
    try:
        # Wait for bus to be free
        while os.path.exists(LOCK_FILE):
            time.sleep(0.1)

        # Lock the bus
        open(LOCK_FILE, 'w').close()

        import board
        import busio
        import adafruit_mcp9600

        i2c = busio.I2C(board.SCL, board.SDA)
        mcp_ET = adafruit_mcp9600.MCP9600(i2c, address=0x60)
        mcp_BT = adafruit_mcp9600.MCP9600(i2c, address=0x67)

        ET = mcp_ET.temperature
        BT = mcp_BT.temperature

        i2c.deinit()
        del i2c, mcp_ET, mcp_BT

        with open(TEMP_FILE, "w") as f:
            f.write(f"{ET:.2f},{BT:.2f}")

        print(f"ET={ET:.2f} BT={BT:.2f}")

    except OSError as e:
        # I2C busy or device error - just retry
        with open("/tmp/sensor_error.log", "a") as f:
            f.write(f"RETRY: {str(e)}\n")

    except Exception as e:
        with open("/tmp/sensor_error.log", "a") as f:
            f.write(f"ERROR: {str(e)}\n")

    finally:
        # Always release lock
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    time.sleep(2)
