#!/usr/bin/env python3
import sys
import time
import os
import signal

sys.path.insert(0, '/home/pi/(YOUR_Directory)')
from valve_driver import close_valve, open_valve, percent_to_ma

CONTROL_FILE = "/home/pi/.var/app/org.artisan_scope.artisan/data/control.txt"
DELAY = 3

last_modified = 0
last_update = 0

def shutdown(signum, frame):
    print("Shutdown - closing valve")
    for i in range(5):
        try:
            close_valve()
            print("Valve closed")
            break
        except Exception as e:
            print(f"Retry {i+1}: {e}")
            time.sleep(1)
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)

time.sleep(3)
print("DAC server started")

# Close valve on start with retries
for i in range(10):
    try:
        close_valve()
        print("Valve closed on startup")
        break
    except Exception as e:
        print(f"Startup attempt {i+1} failed: {e}")
        time.sleep(2)

while True:
    try:
        if os.path.exists(CONTROL_FILE):
            modified = os.path.getmtime(CONTROL_FILE)
            now = time.time()
            age = now - modified

            # Close valve if Artisan not actively monitoring
            if age > 30:
                if last_modified != 0:
                    print("Artisan inactive - closing valve")
                    close_valve()
                    last_modified = 0

            elif modified != last_modified and (now - last_update) >= DELAY:
                with open(CONTROL_FILE, "r") as f:
                    parts = f.read().strip().split(",")
                    ET = float(parts[0])
                    BT = float(parts[1])

                if ET > 0 and BT > 0:
                    if BT < 100:
                        percent = 100.0
                    elif BT > 200:
                        percent = 0.0
                    else:
                        percent = 100.0 - ((BT - 100) / 100.0) * 100.0

                    open_valve(percent)
                    print(f"ET={ET:.2f} BT={BT:.2f} -> {percent:.1f}% = {percent_to_ma(percent):.2f}mA")

                    last_modified = modified
                    last_update = now

    except FileNotFoundError:
        pass
    except Exception as e:
        with open("/tmp/dac_error.log", "a") as f:
            f.write(f"ERROR: {str(e)}\n")

    time.sleep(1)
