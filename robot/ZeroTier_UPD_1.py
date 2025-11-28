# pi_robot.py
import socket, threading, time
import RPi.GPIO as GPIO
import smbus2, math
from gpiozero import DistanceSensor

MAC_IP = "192.168.192.218"  # Laptop ZeroTier IP
PI_PORT = 6000
MAC_PORT  = 6001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PI_PORT))

# Setup motors and sensors
GPIO.setmode(GPIO.BCM)
motors = [17,27,22,10]
for p in motors: GPIO.setup(p, GPIO.OUT)
ultra = DistanceSensor(echo=24, trigger=23)
bus = smbus2.SMBus(1)
MPU_ADDR = 0x68
bus.write_byte_data(MPU_ADDR, 0x6B, 0)

def read_mpu():
    # Simple accel example
    def read_word(reg):
        h = bus.read_byte_data(MPU_ADDR, reg)
        l = bus.read_byte_data(MPU_ADDR, reg+1)
        val = (h << 8) + l
        if val >= 0x8000: val = -((65535 - val) + 1)
        return val
    ax = read_word(0x3B)/16384.0
    ay = read_word(0x3D)/16384.0
    az = read_word(0x3F)/16384.0
    return (ax, ay, az)

def telemetry_loop():
    while True:
        dist = ultra.distance * 100
        ax, ay, az = read_mpu()
        msg = f"D={dist:.1f}cm AX={ax:.2f} AY={ay:.2f} AZ={az:.2f}"
        sock.sendto(msg.encode(), (MAC_IP, MAC_PORT))
        time.sleep(0.2)

def control_loop():
    while True:
        data, _ = sock.recvfrom(64)
        cmd = data.decode().lower()
        print("Command:", cmd)
        # example simple motor logic
        if cmd == 'w':
            GPIO.output(motors, (1,0,1,0))
        elif cmd == 's':
            GPIO.output(motors, (0,1,0,1))
        elif cmd == 'a':
            GPIO.output(motors, (0,1,1,0))
        elif cmd == 'd':
            GPIO.output(motors, (1,0,0,1))
        else:
            GPIO.output(motors, (0,0,0,0))

threading.Thread(target=telemetry_loop, daemon=True).start()
control_loop()
