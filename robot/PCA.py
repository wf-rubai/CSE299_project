# sudo apt update
# sudo apt install python3-pip python3-smbus i2c-tools
# pip3 install adafruit-circuitpython-servokit

from adafruit_servokit import ServoKit
import time

# PCA9685 has 16 channels
kit = ServoKit(channels=16)

# Optional: set frequency to 50Hz (standard for servos)
kit.frequency = 50

# Servo channels you want to use
SERVO1 = 0      # PCA9685 channel 0
SERVO2 = 1      # PCA9685 channel 1

# Move servo test
while True:
    print("0°")
    kit.servo[SERVO1].angle = 0
    kit.servo[SERVO2].angle = 0
    time.sleep(1)

    print("90°")
    kit.servo[SERVO1].angle = 90
    kit.servo[SERVO2].angle = 90
    time.sleep(1)

    print("180°")
    kit.servo[SERVO1].angle = 180
    kit.servo[SERVO2].angle = 180
    time.sleep(1)
