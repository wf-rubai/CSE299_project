import smbus
import time
import math

bus = smbus.SMBus(1)
ADDR = 0x68

bus.write_byte_data(ADDR, 0x6B, 0)   # wake sensor

ACCEL_XOUT_H = 0x3B
GYRO_XOUT_H  = 0x43

def read_word(reg):
    high = bus.read_byte_data(ADDR, reg)
    low = bus.read_byte_data(ADDR, reg + 1)
    val = (high << 8) | low
    if val > 32767:
        val -= 65536
    return val

# ------------------------------ CALIBRATION ------------------------------
print("Calibrating... Keep MPU6050 totally still!")
time.sleep(2)

ax_off = ay_off = az_off = 0
gx_off = gy_off = gz_off = 0
samples = 200

pitch = 0
roll = 0
yaw = 0

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

print("Calibration Done!")
print("Accel offsets:", ax_off, ay_off, az_off)
print("Gyro offsets : ", gx_off, gy_off, gz_off)
print("---------------------------------------")
# ------------------------------------------------------------------------

last_time = time.time()

while True:
    now = time.time()
    dt = now - last_time
    last_time = now
    
    # read raw
    ax = read_word(ACCEL_XOUT_H) - ax_off
    ay = read_word(ACCEL_XOUT_H+2) - ay_off
    az = read_word(ACCEL_XOUT_H+4) - az_off

    gx = read_word(GYRO_XOUT_H) - gx_off
    gy = read_word(GYRO_XOUT_H+2) - gy_off
    gz = read_word(GYRO_XOUT_H+4) - gz_off

    # convert to g?s and deg/sec
    ax /= 16384.0
    ay /= 16384.0
    az /= 16384.0

    gx /= 131.0
    gy /= 131.0
    gz /= 131.0

    # --- Accelerometer angle ---
    accel_pitch = math.degrees(math.atan2(ax, math.sqrt(ay**2 + az**2)))
    accel_roll  = math.degrees(math.atan2(ay, math.sqrt(ax**2 + az**2)))

    # --- Gyro integration ---
    pitch += gx * dt
    roll  += gy * dt
    yaw   += gz * dt     # yaw drift is normal (need magnetometer for accuracy)

    # --- Complementary filter ---
    alpha = 0.98
    pitch = alpha * pitch + (1-alpha) * accel_pitch
    roll  = alpha * roll  + (1-alpha) * accel_roll

    print(f"Pitch={pitch:.2f}  Roll={roll:.2f}  Yaw={yaw:.2f}")
    time.sleep(0.01)

