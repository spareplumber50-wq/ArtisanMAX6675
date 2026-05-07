#!/usr/bin/env python3
TEMP_FILE = "/home/pi/.var/app/org.artisan_scope.artisan/data/temps.txt"

try:
    with open(TEMP_FILE, "r") as f:
        print(f.read().strip())
except Exception:
    print("0.00,0.00")
