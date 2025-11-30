import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

pins = [23, 26]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)

pwmA = GPIO.PWM(23, 10000)  # PWM1A
pwmB = GPIO.PWM(26, 10000)  # PWM1B

pwmA.start(0)
pwmB.start(0)

try:
    while True:
        pwmA.ChangeDutyCycle(25)
        pwmB.ChangeDutyCycle(75)
        time.sleep(1)

        pwmA.ChangeDutyCycle(75)
        pwmB.ChangeDutyCycle(25)
        time.sleep(1)

except KeyboardInterrupt:
    pwmA.stop()
    pwmB.stop()
    GPIO.cleanup()
