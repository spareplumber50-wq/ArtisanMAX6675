#!/usr/bin/env python3
'''
GP8302 Valve Driver
Based on DFRobot GP8302 library (MIT License)
Rewritten for ArtisanMAX6675 roaster control
Uses bit-banged I2C via RPi.GPIO to avoid hardware I2C bus conflicts
'''

import RPi.GPIO as GPIO
import time

# GP8302 Constants from DFRobot source
GP8302_ADDR          = 0x58
GP8302_CONFIG_REG    = 0x02
GP8302_RESOLUTION    = 0x0FFF
GP8302_MAX_MA        = 25.0
GP8302_STORE_HEAD    = 0x02
GP8302_STORE_ADDR    = 0x10
GP8302_STORE_CMD1    = 0x03
GP8302_STORE_CMD2    = 0x00
GP8302_STORE_DELAY   = 0.01

# I2C timing from DFRobot source
I2C_CYCLE_TOTAL      = 0.000005
I2C_CYCLE_BEFORE     = 0.000002
I2C_CYCLE_AFTER      = 0.000003

# GPIO pins (BCM)
SCL_PIN = 3
SDA_PIN = 2

# Calibration for 4-20mA (from DFRobot defaults)
DAC_4MA  = 655
DAC_20MA = 3277

def _setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(SCL_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(SDA_PIN, GPIO.OUT, initial=GPIO.HIGH)

def _start():
    GPIO.output(SCL_PIN, GPIO.HIGH)
    GPIO.output(SDA_PIN, GPIO.HIGH)
    time.sleep(I2C_CYCLE_BEFORE)
    GPIO.output(SDA_PIN, GPIO.LOW)
    time.sleep(I2C_CYCLE_AFTER)
    GPIO.output(SCL_PIN, GPIO.LOW)
    time.sleep(I2C_CYCLE_TOTAL)

def _stop():
    GPIO.output(SDA_PIN, GPIO.LOW)
    time.sleep(I2C_CYCLE_BEFORE)
    GPIO.output(SCL_PIN, GPIO.HIGH)
    time.sleep(I2C_CYCLE_TOTAL)
    GPIO.output(SDA_PIN, GPIO.HIGH)
    time.sleep(I2C_CYCLE_TOTAL)

def _recv_ack(ack=0):
    error_time = 0
    GPIO.setup(SDA_PIN, GPIO.IN)
    time.sleep(I2C_CYCLE_BEFORE)
    GPIO.output(SCL_PIN, GPIO.HIGH)
    time.sleep(I2C_CYCLE_AFTER)
    while GPIO.input(SDA_PIN) != ack:
        time.sleep(0.000001)
        error_time += 1
        if error_time > 250:
            break
    time.sleep(I2C_CYCLE_BEFORE)
    GPIO.output(SCL_PIN, GPIO.LOW)
    time.sleep(I2C_CYCLE_AFTER)
    GPIO.setup(SDA_PIN, GPIO.OUT)

def _send_byte(data, ack=0, bits=8, flag=True):
    data = data & 0xFF
    for i in range(bits - 1, -1, -1):
        if data & (1 << i):
            GPIO.output(SDA_PIN, GPIO.HIGH)
        else:
            GPIO.output(SDA_PIN, GPIO.LOW)
        time.sleep(I2C_CYCLE_BEFORE)
        GPIO.output(SCL_PIN, GPIO.HIGH)
        time.sleep(I2C_CYCLE_TOTAL)
        GPIO.output(SCL_PIN, GPIO.LOW)
        time.sleep(I2C_CYCLE_AFTER)
    if flag:
        _recv_ack(ack)

def _write_dac(dac):
    '''Write raw DAC value 0-0xFFF to GP8302.'''
    dac = dac & GP8302_RESOLUTION
    _start()
    _send_byte(GP8302_ADDR << 1)
    _send_byte(GP8302_CONFIG_REG)
    _send_byte((dac << 4) & 0xF0)
    _send_byte((dac >> 4) & 0xFF)
    _stop()

def set_ma(ma):
    '''Set output current in mA using 4-20mA calibrated range.'''
    ma = max(0.0, min(25.0, ma))
    _setup()
    if 4.0 <= ma <= 20.0:
        # Use calibrated 4-20mA range
        dac = int(DAC_4MA + ((ma - 4.0) * (DAC_20MA - DAC_4MA)) / 16.0)
    else:
        # Raw conversion for outside 4-20mA range
        dac = int((ma / GP8302_MAX_MA) * GP8302_RESOLUTION)
    _write_dac(dac)

def percent_to_ma(percent):
    '''Convert 0-100% to 4-20mA range. 0%=4mA(closed), 100%=20mA(open).'''
    percent = max(0.0, min(100.0, percent))
    return 4.0 + (percent / 100.0) * 16.0

def close_valve():
    '''Set valve to 4mA - fully closed.'''
    set_ma(4.0)

def open_valve(percent):
    '''Open valve to given percentage 0-100%.'''
    set_ma(percent_to_ma(percent))

def store():
    '''Save current config to survive power cycle.'''
    _setup()
    _start()
    _send_byte(GP8302_STORE_HEAD, 0, 3, False)
    _stop()
    _start()
    _send_byte(GP8302_STORE_ADDR)
    _send_byte(GP8302_STORE_CMD1)
    _stop()
    _start()
    _send_byte(GP8302_ADDR << 1, 1)
    for _ in range(8):
        _send_byte(GP8302_STORE_CMD2, 1)
    _stop()
    time.sleep(GP8302_STORE_DELAY)
    _start()
    _send_byte(GP8302_STORE_HEAD, 0, 3, False)
    _stop()
    _start()
    _send_byte(GP8302_STORE_ADDR)
    _send_byte(GP8302_STORE_CMD2)
    _stop()

if __name__ == "__main__":
    print("Testing valve driver...")
    close_valve()
    print("Valve closed (4mA)")
    time.sleep(2)
    open_valve(50)
    print("Valve 50% open (12mA)")
    time.sleep(2)
    close_valve()
    print("Valve closed (4mA)")
