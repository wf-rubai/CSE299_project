# pi_robot.py
import socket, threading, time
import RPi.GPIO as GPIO
import smbus, math
from gpiozero import DistanceSensor

# ------------------------
# Laptop ZeroTier IP
# ------------------------
MAC_IP = "192.168.192.218"  
PI_PORT = 6000
MAC_PORT  = 6001

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PI_PORT))

# ---------------------------
# Setup motors and sensors
# ---------------------------
GPIO.setmode(GPIO.BCM)
motors = [17,27,22,10,12,13]
for p in motors: GPIO.setup(p, GPIO.OUT)

# ---------------
# PWM setup
# ---------------
PWM_freq = 10000
PWM_duty = 25

pwmA = GPIO.PWM(12, PWM_freq)  # PWM1A
pwmB = GPIO.PWM(13, PWM_freq)  # PWM1B

pwmA.start(PWM_duty)
pwmB.start(PWM_duty)

# ------------------------
# Sonar and MPU6050 setup
# ------------------------
ultra = DistanceSensor(echo=24, trigger=23)
bus = smbus.SMBus(1)
ADDR = 0x68
bus.write_byte_data(ADDR, 0x6B, 0)

ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

def read_word(reg):
    high = bus.read_byte_data(ADDR, reg)
    low = bus.read_byte_data(ADDR, reg + 1)
    val = (high << 8) | low
    if val > 32767:
        val -= 65536
    return val

# ------------------------
# MPU6050 Calibration
# ------------------------
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
az_off = (az_off / samples) - 16384   # remove gravity
gx_off /= samples
gy_off /= samples
gz_off /= samples

print("Calibration complete.")

pitch = 0.0
roll  = 0.0
yaw   = 0.0

x = 0.0
y = 0.0
vx = 0.0
vy = 0.0

last_t = time.time()

# ------------------------
# X, Y coordinates
# ------------------------
def get_xy():
    global pitch, roll, yaw
    global x, y, vx, vy
    global last_t

    # ---- time delta ----
    now = time.time()
    dt = now - last_t
    last_t = now

    # ---- read raw ----
    ax = read_word(ACCEL_XOUT_H)   - ax_off
    ay = read_word(ACCEL_XOUT_H+2) - ay_off
    az = read_word(ACCEL_XOUT_H+4) - az_off
    gx = read_word(GYRO_XOUT_H)    - gx_off
    gy = read_word(GYRO_XOUT_H+2)  - gy_off
    gz = read_word(GYRO_XOUT_H+4)  - gz_off

    # ---- convert units ----
    ax /= 16384.0
    ay /= 16384.0
    az /= 16384.0
    gx /= 131.0
    gy /= 131.0
    gz /= 131.0

    # ---- accel angles ----
    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
    accel_roll  = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))

    # ---- integrate gyro ----
    pitch += gx * dt
    roll  += gy * dt
    yaw   += gz * dt

    # ---- complementary filter ----
    alpha = 0.98
    pitch = alpha*pitch + (1-alpha)*accel_pitch
    roll  = alpha*roll  + (1-alpha)*accel_roll

    # ---- convert pitch/roll to radians ----
    pr = math.radians(pitch)
    rr = math.radians(roll)

    # ---- rotate local accel to world X/Y ----
    ax_world = ax * math.cos(pr) + az * math.sin(pr)
    ay_world = ay * math.cos(rr) + az * math.sin(rr)

    # convert g → m/s²
    ax_ms = ax_world * 9.81
    ay_ms = ay_world * 9.81

    # ---- integrate acceleration → velocity ----
    vx += ax_ms * dt
    vy += ay_ms * dt

    # ---- integrate velocity → position ----
    x += vx * dt
    y += vy * dt

    return x, y   # meters (approx!)

# -----------------------------
# Transmitter Loop
# -----------------------------
def telemetry_loop():
    while True:
        dist = ultra.distance * 100
        x, y = get_xy()
        msg = f"D={dist:.1f}cm AX={x:.2f} AY={y:.2f}"
        sock.sendto(msg.encode(), (MAC_IP, MAC_PORT))
        time.sleep(0.2)

# ---------------------
# Control Loop
# ---------------------
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
