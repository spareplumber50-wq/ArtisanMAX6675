#!/usr/bin/env python3
import smbus2

DAC_ADDRESS = 0x58
DAC_MAX = 0xFFF

def close_valve():
    dac_value = int((4.0 / 25.0) * DAC_MAX)
    high = (dac_value >> 8) & 0x0F
    low = dac_value & 0xFF
    for i in range(5):
        try:
            with smbus2.SMBus(1) as bus:
                bus.write_i2c_block_data(DAC_ADDRESS, high, [low])
            print("Valve closed")
            return
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")

close_valve()
