# pi_controller_combined.py
import socket, threading, time
import RPi.GPIO as GPIO
import smbus, math
from gpiozero import DistanceSensor
from adafruit_servokit import ServoKit
import sounddevice as sd
import numpy as np
import queue


# -----------------------------
# Controll configaration
# -----------------------------
MAC_IP = "192.168.192.218"  
PI_PORT = 6000
MAC_PORT = 6001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PI_PORT))

# -------------------------
# Audio configaration
# -------------------------
PEER_IP = "192.168.192.218"
UDP_PORT = 7000

INPUT_DEVICE =  0   # Voice HAT mic index (check with sd.query_devices())
OUTPUT_DEVICE = 1   # USB PnP Sound Device index (check with sd.query_devices())

FRAMESIZE = 1024
SAMPLERATE = 48000
GAIN = 4

sock_audio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_audio.bind(("0.0.0.0", UDP_PORT))

audio_queue = queue.Queue()

# -----------------------------
# Setup motors
# -----------------------------
GPIO.setmode(GPIO.BCM)
motors = [22,10,27,17]
for p in motors: GPIO.setup(p, GPIO.OUT)
GPIO.output(motors, (0,0,0,0))


# -----------------------------
# PWM setup
# -----------------------------
GPIO.setup(12, GPIO.OUT) 
GPIO.setup(13, GPIO.OUT)

PWM_freq = 1000
angle_change = 5

pwmA = GPIO.PWM(12, PWM_freq)
pwmB = GPIO.PWM(13, PWM_freq)

rotation_duty = 80
linier_duty = 60

# -----------------------------
# Servo setup
# -----------------------------
kit = ServoKit(channels=16)
kit.frequency = 50

SERVO1 = 1
SERVO2 = 2

vartical_angle = 90
horizontal_angle = 90

kit.servo[SERVO1].angle = vartical_angle
kit.servo[SERVO2].angle = horizontal_angle


# -----------------------------
# Sonar & MPU6050 setup
# -----------------------------
ultra = DistanceSensor(echo=24, trigger=23)

bus = smbus.SMBus(1)
ADDR = 0x68
bus.write_byte_data(ADDR, 0x6B, 0)

ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

obj_ditect = False
max_dist = 90

def read_word(reg):
    high = bus.read_byte_data(ADDR, reg)
    low = bus.read_byte_data(ADDR, reg + 1)
    val = (high << 8) | low
    if val > 32767: val -= 65536
    return val

# -----------------------------
# MPU6050 Calibration
# -----------------------------
print("Calibrating MPU6050...")
time.sleep(2)

ax_off = ay_off = az_off = 0
gx_off = gy_off = gz_off = 0
samples = 200
for i in range(samples):
    ax_off += read_word(ACCEL_XOUT_H)
    ay_off += read_word(ACCEL_XOUT_H+2)
    az_off += read_word(ACCEL_XOUT_H+4)
    gx_off += read_word(GYRO_XOUT_H)
    gy_off += read_word(GYRO_XOUT_H+2)
    gz_off += read_word(GYRO_XOUT_H+4)
    time.sleep(0.005)

ax_off /= samples
ay_off /= samples
az_off = (az_off / samples) - 16384 # remove gravity
gx_off /= samples
gy_off /= samples
gz_off /= samples

print("Calibration complete.")

pitch = 0.0
roll  = 0.0
yaw   = 0.0

x = y = 0.0
vx = vy = 0.0
last_t = time.time()

# -----------------------------
# X, Y coordinates
# -----------------------------
def get_xy():
    global pitch, roll, yaw
    global x, y, vx, vy, last_t

    now = time.time()
    dt = now - last_t
    last_t = now

    ax = read_word(ACCEL_XOUT_H)   - ax_off
    ay = read_word(ACCEL_XOUT_H+2) - ay_off
    az = read_word(ACCEL_XOUT_H+4) - az_off
    gx = read_word(GYRO_XOUT_H)    - gx_off
    gy = read_word(GYRO_XOUT_H+2)  - gy_off
    gz = read_word(GYRO_XOUT_H+4)  - gz_off

    ax /= 16384.0; 
    ay /= 16384.0; 
    az /= 16384.0
    gx /= 131.0;   
    gy /= 131.0;   
    gz /= 131.0

    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
    accel_roll  = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))

    pitch += gx * dt
    roll  += gy * dt
    yaw   += gz * dt

    alpha = 0.98
    pitch = alpha*pitch + (1-alpha)*accel_pitch
    roll  = alpha*roll  + (1-alpha)*accel_roll

    pr = math.radians(pitch)
    rr = math.radians(roll)

    ax_world = ax * math.cos(pr) + az * math.sin(pr)
    ay_world = ay * math.cos(rr) + az * math.sin(rr)

    ax_ms = ax_world * 9.81
    ay_ms = ay_world * 9.81

    vx += ax_ms * dt
    vy += ay_ms * dt
    x += vx * dt
    y += vy * dt

    return x, y     # meters (approx!)

# -----------------------------
# Telemetry Thread
# -----------------------------
def telemetry_loop():
    global obj_ditect
    while True:
        dist = ultra.distance * 100
#        obj_ditect = True if dist < max_dist else False
        x_val, y_val = get_xy()
        msg = f"{dist:.1f} {x_val:.2f} {y_val:.2f}"     # distance(cm) x(m) y(m)
        sock.sendto(msg.encode(), (MAC_IP, MAC_PORT))
        time.sleep(0.2)
            
# -------------------------
# UDP receiver thread
# -------------------------
def udp_receiver():
    while True:
        data, _ = sock_audio.recvfrom(FRAMESIZE * 2)
        samples = np.frombuffer(data, dtype=np.int16)
        audio_queue.put(samples)

# -------------------------
# Playback callback
# -------------------------
def playback_callback(outdata, frames, time, status):
    try:
        chunk = audio_queue.get_nowait()
        chunk = np.clip(chunk * GAIN, -32768, 32767).astype(np.int16)
        stereo = np.column_stack([chunk, chunk]).astype(np.int16)
        outdata[:] = stereo
    except queue.Empty:
        outdata.fill(0)

# -------------------------
# Record callback
# -------------------------
def record_callback(indata, frames, time, status):
    mono = indata[:, 0].astype(np.int16)
    mono = np.clip(mono, -32768, 32767).astype(np.int16)
    sock_audio.sendto(mono.tobytes(), (PEER_IP, UDP_PORT))
    
# -------------------------
# Start full-duplex streams
# -------------------------
def audio_thread():
    with sd.InputStream(
        samplerate=SAMPLERATE,
        channels=1,     # Voice HAT is mono
        dtype='int16',
        blocksize=FRAMESIZE,
        device=INPUT_DEVICE,
        callback=record_callback
    ), sd.OutputStream(
        samplerate=SAMPLERATE,
        channels=2,     # USB DAC is stereo
        dtype='int16',
        blocksize=FRAMESIZE,
        device=OUTPUT_DEVICE,
        callback=playback_callback
    ):
        print("? FULL DUPLEX AUDIO ACTIVE")
        while True:
            time.sleep(1)

# -------------------------
# START EVERYTHING
# -------------------------
threading.Thread(target=udp_receiver, daemon=True).start()
threading.Thread(target=telemetry_loop, daemon=True).start()
threading.Thread(target=audio_thread, daemon=True).start()

# -----------------------------
# Robot Control Thread
# -----------------------------
def control_loop():
    global vartical_angle, horizontal_angle, obj_ditect
    while True:
        data, _ = sock.recvfrom(64)
        cmd = data.decode().lower()
        print("Command:", cmd)

        dist = ultra.distance * 100
        obj_ditect = True if dist < max_dist else False
        if cmd == 'w' and not obj_ditect:
            PWM_duty = linier_duty
            pwmA.start(PWM_duty)
            pwmB.start(PWM_duty)
            GPIO.output(motors, (1,0,1,0))
        elif cmd == 's':
            PWM_duty = linier_duty
            pwmA.start(PWM_duty)
            pwmB.start(PWM_duty)
            GPIO.output(motors, (0,1,0,1))
        elif cmd == 'a':
            PWM_duty = rotation_duty
            pwmA.start(PWM_duty)
            pwmB.start(PWM_duty)
            GPIO.output(motors, (0,1,1,0))
        elif cmd == 'd':
            PWM_duty = rotation_duty
            pwmA.start(PWM_duty)
            pwmB.start(PWM_duty)
            GPIO.output(motors, (1,0,0,1))
            
        if cmd == 'u':
            vartical_angle = min(170, vartical_angle + angle_change)
            kit.servo[SERVO1].angle = vartical_angle
        elif cmd == 'b':
            vartical_angle = max(10, vartical_angle - angle_change)
            kit.servo[SERVO1].angle = vartical_angle
        elif cmd == 'l':
            horizontal_angle = min(170, horizontal_angle + angle_change)
            kit.servo[SERVO2].angle = horizontal_angle
        elif cmd == 'r':
            horizontal_angle = max(10, horizontal_angle - angle_change)
            kit.servo[SERVO2].angle = horizontal_angle
        elif cmd == 'x':
            GPIO.output(motors, (0,0,0,0))
        
control_loop()  # main blocking loop
