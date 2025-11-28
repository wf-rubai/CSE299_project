import RPi.GPIO as GPIO # type: ignore
from time import sleep

# Pin setup
IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23

GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(IN3, GPIO.OUT)
GPIO.setup(IN4, GPIO.OUT)

# PWM setup (1000 Hz)
pwm1 = GPIO.PWM(IN1, 1000)
pwm2 = GPIO.PWM(IN2, 1000)
pwm3 = GPIO.PWM(IN3, 1000)
pwm4 = GPIO.PWM(IN4, 1000)

pwm1.start(0)
pwm2.start(0)
pwm3.start(0)
pwm4.start(0)

def motorA_forward(speed):
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(0)

def motorA_backward(speed):
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(speed)

def motorB_forward(speed):
    pwm3.ChangeDutyCycle(speed)
    pwm4.ChangeDutyCycle(0)

def motorB_backward(speed):
    pwm3.ChangeDutyCycle(0)
    pwm4.ChangeDutyCycle(speed)

def stop():
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
    pwm3.ChangeDutyCycle(0)
    pwm4.ChangeDutyCycle(0)

try:
    while True:
        print("Forward")
        motorA_forward(70)
        motorB_forward(70)
        sleep(2)

        print("Backward")
        motorA_backward(70)
        motorB_backward(70)
        sleep(2)

        print("Turn Right")
        motorA_forward(70)
        motorB_backward(70)
        sleep(1)

        print("Stop")
        stop()
        sleep(2)

except KeyboardInterrupt:
    pass

finally:
    pwm1.stop()
    pwm2.stop()
    pwm3.stop()
    pwm4.stop()
    GPIO.cleanup()
