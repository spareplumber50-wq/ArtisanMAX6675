#!/usr/bin/env python3
import smbus2
import time
import os
import signal
import sys

CONTROL_FILE = "/home/pi/.var/app/org.artisan_scope.artisan/data/control.txt"
LOCK_FILE = "/tmp/i2c.lock"
DAC_ADDRESS = 0x58
DAC_MAX = 0xFFF
DELAY = 3

last_modified = 0
last_update = 0

def write_ma(ma):
    """Write mA to DAC with bus locking and retry."""
    while os.path.exists(LOCK_FILE):
        time.sleep(0.1)
    open(LOCK_FILE, 'w').close()
    try:
        ma = max(4.0, min(20.0, ma))
        dac_value = int((ma / 25.0) * DAC_MAX)
        high = (dac_value >> 8) & 0x0F
        low = dac_value & 0xFF
        with smbus2.SMBus(1) as bus:
            bus.write_i2c_block_data(DAC_ADDRESS, high, [low])
    except Exception as e:
        with open("/tmp/dac_error.log", "a") as f:
            f.write(f"ERROR write_ma: {str(e)}\n")
    finally:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

def percent_to_ma(percent):
    return 4.0 + (percent / 100.0) * 16.0

def shutdown(signum, frame):
    """Close valve on shutdown."""
    print("Shutdown signal received, closing valve...")
    # Retry closing valve up to 5 times
    for i in range(5):
        try:
            write_ma(4.0)
            print("Valve closed")
            break
        except Exception as e:
            print(f"Retry {i+1}: {e}")
            time.sleep(1)
    sys.exit(0)

# Register shutdown handlers
signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

# Wait for I2C bus and 24V supply to be ready
time.sleep(5)

# Close valve on start with retries
print("DAC server started, closing valve...")
for i in range(10):
    try:
        write_ma(4.0)
        print("Valve closed successfully")
        break
    except Exception as e:
        print(f"Valve close attempt {i+1} failed: {e}")
        time.sleep(2)

while True:
    try:
        # Only act if Artisan is actively monitoring
        # Check control file was modified recently (within 30 seconds)
        if os.path.exists(CONTROL_FILE):
            modified = os.path.getmtime(CONTROL_FILE)
            now = time.time()
            age = now - modified

            # If control file is older than 30 seconds Artisan is not monitoring
            # Close the valve for safety
            if age > 30:
                if last_modified != 0:
                    print("Artisan not monitoring, closing valve")
                    write_ma(4.0)
                    last_modified = 0
            
            elif modified != last_modified and (now - last_update) >= DELAY:
                with open(CONTROL_FILE, "r") as f:
                    parts = f.read().strip().split(",")
                    ET = float(parts[0])
                    BT = float(parts[1])

                # Only throttle if temps are valid
                if ET > 0 and BT > 0:
                    if BT < 100:
                        percent = 100.0
                    elif BT > 200:
                        percent = 0.0
                    else:
                        percent = 100.0 - ((BT - 100) / 100.0) * 100.0

                    ma = percent_to_ma(percent)
                    write_ma(ma)
                    print(f"ET={ET:.2f} BT={BT:.2f} -> {percent:.1f}% = {ma:.2f}mA")

                    last_modified = modified
                    last_update = now

    except FileNotFoundError:
        pass
    except Exception as e:
        with open("/tmp/dac_error.log", "a") as f:
            f.write(f"ERROR: {str(e)}\n")

    time.sleep(1)
