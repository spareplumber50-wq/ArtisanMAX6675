#!/usr/bin/env python3
import sys

CONTROL_FILE = "/home/pi/.var/app/org.artisan_scope.artisan/data/control.txt"

try:
    ET, BT, ETB, BTB = sys.argv[1:]
    with open(CONTROL_FILE, "w") as f:
        f.write(f"{ET},{BT},{ETB},{BTB}")
except Exception as e:
    with open("/tmp/artisan_output.log", "a") as f:
        f.write(f"ERROR: {str(e)}\n")
