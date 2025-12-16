### ⚙️ System Overview

```
   Laptop (control + monitor)
   ├── Keyboard input → UDP → Pi Zero (real time)
   ├── Mic → UDP (audio) → Pi Zero
   ├── UDP (audio) ← Pi Zero (INMP441 mic)
   ├── UDP (text telemetry) ← Pi Zero (sensor readings)
   └── MJPEG video ← ESP32-CAM HTTP stream

   Pi Zero (robot brain)
   ├── Motor driver (PWM outputs)
   ├── Ultrasonic sensor (distance)
   ├── MPU-6050 (I²C accel/gyro)
   ├── INMP441 (I²S mic)
   ├── Audio amp + 3 W speaker (PWM audio out)
   └── ZeroTier + UDP + ffmpeg
```

### Pin connection

Perfect — that’s exactly the right step before wiring your robot.
Here’s a **clean, ready-to-build pin planning table** for your **Raspberry Pi Zero** robot setup.
It includes **each component**, **its pin name**, **which Pi GPIO pin it connects to**, and **the voltage** required.

---

## ⚙️ Raspberry Pi Zero Pin Connection Table

| **Component**                           | **Component Pin Name**                 | **Connect to Raspberry Pi Pin (BCM No. / Physical Pin)**      | **Voltage / Notes**                                                       |
| --------------------------------------- | -------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **INMP441 Microphone (I²S)**            | VDD                                    | 3.3 V (Physical Pin 1 or 17)                                  | **3.3 V only** (5 V will damage it)                                       |
|                                         | GND                                    | GND (Physical Pin 6, 9, 14, 20, 25, 30, 34, 39)               | Common ground                                                             |
|                                         | **BCLK (SCK)**                         | GPIO 18 / Physical Pin 12                                     | I²S Bit Clock                                                             |
|                                         | **LRCL (WS)**                          | GPIO 19 / Physical Pin 35                                     | I²S Left/Right Clock                                                      |
|                                         | **DOUT**                               | GPIO 20 / Physical Pin 38                                     | I²S Data Input to Pi                                                      |
|                                         | **L/R Select**                         | Connect to GND                                                | Select left channel                                                       |

| **3 W Audio Amplifier (e.g. PAM8403)**  | **VIN / VCC**                          | 5 V (Physical Pin 2 or 4)                                     | Requires **5 V**                                                          |
|                                         | **GND**                                | Any GND pin                                                   | Common ground                                                             |
|                                         | **L-IN**                               | GPIO 13 / Physical Pin 33                                     | PWM Audio output from Pi                                                  |
|                                         | **L-OUT / R-OUT**                      | Connect to 3 W speakers                                       | Output to speakers                                                        |

| **HC-SR04 Ultrasonic Sensor**           | **VCC**                                | 5 V (Physical Pin 2 or 4)                                     | Needs **5 V**                                                             |
|                                         | **GND**                                | Any GND pin                                                   | Common ground                                                             |
|                                         | **Trig**                               | GPIO 23 / Physical Pin 16                                     | Output from Pi                                                            |
|                                         | **Echo**                               | GPIO 24 / Physical Pin 18 (via voltage divider 1 kΩ + 2 kΩ)** | Echo pin is 5 V → must step down to 3.3 V for Pi input                    |

| **MPU6050 (Accelerometer + Gyroscope)** | **VCC**                                | 3.3 V (Physical Pin 1 or 17)                                  | Use **3.3 V** (5 V also works on some modules but 3.3 V is safer)         |
|                                         | **GND**                                | Any GND pin                                                   | Common ground                                                             |
|                                         | **SDA**                                | GPIO 2 / Physical Pin 3                                       | I²C Data                                                                  |
|                                         | **SCL**                                | GPIO 3 / Physical Pin 5                                       | I²C Clock                                                                 |

| **Motor Driver (L293D / L298N)**        | **VCC1 (logic)**                       | 5 V (Physical Pin 2 or 4)                                     | Logic voltage                                                             |
|                                         | **VCC2 (motor power)**                 | 5 V–9 V (from external battery)                               | Depends on motor voltage                                                  |
|                                         | **GND**                                | Pi GND (shared)                                               | Common ground                                                             |
|                                         | **IN1**                                | GPIO 17 / Physical Pin 11                                     | Motor A control                                                           |
|                                         | **IN2**                                | GPIO 27 / Physical Pin 13                                     | Motor A control                                                           |
|                                         | **IN3**                                | GPIO 22 / Physical Pin 15                                     | Motor B control                                                           |
|                                         | **IN4**                                | GPIO 10 / Physical Pin 19                                     | Motor B control                                                           |
|                                         | **ENA / ENB**                          | 5 V or PWM GPIOs                                              | Use 5 V if always enabled, or connect to PWM pins for speed control       |

| **ESP32-CAM**                           | Connect separately to 5 V power source (e.g., USB or 5 V pin on Pi with ample current) | —                                                             | **5 V** required; Pi Zero’s 5 V pin can supply small current (~1 A total) |

---

## ⚡ Voltage summary

| **Device**                | **Power Voltage** | **Current Draw (approx.)**                     |
| ------------------------- | ----------------- | ---------------------------------------------- |
| Raspberry Pi Zero         | 5 V               | 150–250 mA                                     |
| INMP441 Mic               | 3.3 V             | 3.0 mA                                         |
| PAM8403 Amp + 3 W speaker | 5 V               | 300–500 mA (depending on volume)               |
| HC-SR04                   | 5 V               | 15 mA                                          |
| MPU6050                   | 3.3 V             | 5 mA                                           |
| L293D motor driver        | 5–9 V             | Depends on motors (typically 300 mA per motor) |
| ESP32-CAM                 | 5 V               | 200–300 mA (peaks up to 500 mA when streaming) |

---

### 🛜 Server informations

Network ID: 68BEA79ACF6E42FA
Check IP: zerotier-cli listnetworks

Devices check:

python3 - << EOF
import sounddevice as sd
print(sd.query_devices())
EOF

---
---

* need to use local ip on:
   ├── ino code: ws_server_host 
   └──  port: 8000

* in 3 terminals run these three lines:

```bash

daphne server.asgi.application -b 192.168.68.101 -p 8000

python manage.py runserver 192.168.68.101:8100

ngrok http 192.168.68.101:8000

```

* need to change the puiblic ip of ngrok in the webPage file without the http part

---

