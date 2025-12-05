# laptop_controller_combined.py
import socket
import threading
import queue
import numpy as np
import pygame
import sounddevice as sd
import sys
import time

# -----------------------------
# Pi ZeroTier IP / Ports setup
# -----------------------------
PI_IP = "192.168.192.103"   # Pi ZeroTier IP
PI_PORT = 6000              # robot control port (send)
MAC_PORT  = 6001            # telemetry receive (bind)
INTERVAL = 0.05             # 50ms repeat

# Audio settings (kept original names where possible)
PEER_IP = PI_IP             # peer for audio is same Pi
UDP_PORT = 7000             # audio TX/RX port (bind + send)

# -----------------------------
# Audio config
# -----------------------------
FRAMESIZE = 1024
SAMPLERATE = 48000
GAIN = 4

INPUT_DEVICE = None   # default mic
OUTPUT_DEVICE = None  # default speaker

# -----------------------------
# Flags / state
# -----------------------------
mic_on = False
speaker_on = True

# last command / statuses for dashboard
last_movement_cmd = None
last_camera_cmd = None
last_telemetry = "No data yet"
joystick_present = False

# -----------------------------
# Socket setup
# -----------------------------
# Control socket used to send single-char commands to PI
control_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
control_sock.setblocking(False)

# Telemetry socket (bind to receive telemetry from PI)
telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telemetry_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
telemetry_sock.bind(("0.0.0.0", MAC_PORT))
telemetry_sock.setblocking(True)

# Audio socket (bind to receive audio frames)
audio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
audio_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)    # removable if needed
audio_sock.bind(("0.0.0.0", UDP_PORT))
audio_sock.setblocking(True)                                        # removable if needed

# -----------------------------
# Pygame / Joystick setup
# -----------------------------
pygame.init()
SCREEN_W, SCREEN_H = 400, 300
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Robot Controller Dashboard")
font = pygame.font.SysFont("monospace", 10)

pygame.joystick.init()
joystick_count = pygame.joystick.get_count()
joystick = None
if joystick_count != 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    joystick_present = True
    print(f"Detected joystick: {joystick.get_name()}")
    print(f"Number of axes: {joystick.get_numaxes()}")
    print(f"Number of buttons: {joystick.get_numbuttons()}")
    print(f"Number of hats: {joystick.get_numhats()}")
else:
    print("🚙 Use [W, A, S, D] keys to control the robot.")
    print("📷 Use Arrow keys to control the camera orientation.")
    print("🎧 Press 'M' to toggle Mic/Speaker on/off.")

# -----------------------------
# Audio queue and functions
# -----------------------------
audio_queue = queue.Queue()

def udp_receiver_audio():
    """Receive audio frames and push to queue"""
    while True:
        data, _ = audio_sock.recvfrom(FRAMESIZE * 2)
        samples = np.frombuffer(data, dtype=np.int16)
        audio_queue.put(samples)

audio_thread = threading.Thread(target=udp_receiver_audio, daemon=True)
audio_thread.start()

def playback_callback(outdata, frames, time_info, status):
    global speaker_on
    # outdata shape (frames, 2)
    if speaker_on:
        try:
            chunk = audio_queue.get_nowait()
            chunk = np.clip(chunk.astype(np.int32) * GAIN, -32768, 32767).astype(np.int16)  # remove the astype(np.int32) part if needed
            stereo = np.column_stack([chunk, chunk]).astype(np.int16)
            outdata[:] = stereo
        except queue.Empty:
            outdata.fill(0)
    else:
        # outdata.fill(0)
        try:
            chunk = audio_queue.get_nowait()
            chunk = np.clip(chunk * 0, -32768, 32767).astype(np.int16)
            stereo = np.column_stack([chunk, chunk]).astype(np.int16)
            outdata[:] = stereo
        except queue.Empty:
            outdata.fill(0)

def record_callback(indata, frames, time_info, status):
    global mic_on
    # indata shape (frames, channels)
    if mic_on:
        mono = indata[:, 0].astype(np.int16)
        mono = np.clip(mono.astype(np.int32) * GAIN, -32768, 32767).astype(np.int16)    # remove the astype(np.int32) part if needed
        try:
            audio_sock.sendto(mono.tobytes(), (PEER_IP, UDP_PORT))
        except Exception as e:
            # network issue shouldn't crash callback
            pass

# Start audio streams (safe try/except)
input_stream = None
output_stream = None
try:
    input_stream = sd.InputStream(
        samplerate=SAMPLERATE,
        channels=1,
        dtype='int16',
        blocksize=FRAMESIZE,
        device=INPUT_DEVICE,
        callback=record_callback
    )
    output_stream = sd.OutputStream(
        samplerate=SAMPLERATE,
        channels=2,
        dtype='int16',
        blocksize=FRAMESIZE,
        device=OUTPUT_DEVICE,
        callback=playback_callback
    )
    input_stream.start()
    output_stream.start()
except Exception as e:
    print("Failed to start audio streams:", e)
    # continue; user can still use joystick/telemetry

# -----------------------------
# Telemetry receiver thread
# -----------------------------
def recv_telemetry():
    global last_telemetry
    while True:
        data, _ = telemetry_sock.recvfrom(1024)
        text = data.decode(errors='ignore')
        last_telemetry = text
        # also print to console
        print("Telemetry:", text)

telemetry_thread = threading.Thread(target=recv_telemetry, daemon=True)
telemetry_thread.start()

# -----------------------------
# Helper: send control command
# -----------------------------
def send_control(cmd_char):
    global last_movement_cmd, last_camera_cmd
    if cmd_char is None:
        return
    try:
        control_sock.sendto(cmd_char.encode(), (PI_IP, PI_PORT))
    except Exception as e:
        # ignore send errors
        pass

    # Update last command display
    if cmd_char in ['w','a','s','d']:
        last_movement_cmd = cmd_char
    elif cmd_char in ['U','D','L','R']:
        last_camera_cmd = cmd_char

# -----------------------------
# Main loop
# -----------------------------
running = True
clock = pygame.time.Clock()
current_key = None

while running:
    # --- handle events ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Mic toggle key 'M'
            if event.key == pygame.K_m:
                mic_on = not mic_on
                speaker_on = not speaker_on
            # Arrow keys map to camera
            elif event.key == pygame.K_UP:
                current_key = 'U'
            elif event.key == pygame.K_DOWN:
                current_key = 'D'
            elif event.key == pygame.K_LEFT:
                current_key = 'L'
            elif event.key == pygame.K_RIGHT:
                current_key = 'R'
            # WASD movement
            elif event.key in (pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d):
                current_key = event.unicode  # 'w','a','s','d'
            else:
                current_key = None
        elif event.type == pygame.KEYUP:
            current_key = None

    # --- joystick handling (if present) ---
    if joystick is not None:
        pygame.event.pump()
        # Safe get axes with try/except (some joysticks have fewer axes)
        try:
            axis_0 = joystick.get_axis(0)  # left stick horiz
            axis_1 = joystick.get_axis(1)  # left stick vert
            axis_2 = joystick.get_axis(2)  # right stick horiz
            axis_3 = joystick.get_axis(3)  # right stick vert
        except Exception:
            axis_0 = axis_1 = axis_2 = axis_3 = 0.0

        # Map joystick to commands:
        # Left stick controls robot movement: up -> w, down -> s, left -> a, right -> d
        if abs(axis_1) > 0.3:
            current_key = 'w' if axis_1 < 0 else 's'
        elif abs(axis_0) > 0.3:
            current_key = 'a' if axis_0 < 0 else 'd'
        # Right stick controls camera: up/down/left/right -> U/D/L/R
        elif abs(axis_3) > 0.3:
            current_key = 'D' if axis_3 < 0 else 'U'
        elif abs(axis_2) > 0.3:
            current_key = 'R' if axis_2 < 0 else 'L'
        else:
            # no stick displacement
            current_key = None

    # --- send command if present ---
    if current_key:
        send_control(current_key)

    # --- draw dashboard ---
    screen.fill((45, 45, 45))  # beige-like background

    # Titles and instructions
    screen.blit(font.render("Robot Controller Dashboard", True, (255, 255, 255)), (12, 8))
    screen.blit(font.render("Keys: WASD - Move | Arrows - Camera | M - Toggle Mic/Speaker", True, (255, 255, 255)), (12, 32))

    # Status boxes
    def draw_box(x, y, w, h, label, value):
        pygame.draw.rect(screen, (55,55,55), (x, y, w, h))
        # pygame.draw.rect(screen, (0,0,0), (x, y, w, h), 1)
        screen.blit(font.render(label, True, (255, 255, 255)), (x+6, y+4))
        screen.blit(font.render(value, True, (255, 255, 255)), (x+6, y+24))

    draw_box(12, 60, 180, 60, "Audio", f"Mic: {'ON' if mic_on else 'OFF'} | Speaker: {'ON' if speaker_on else 'OFF'}")
    draw_box(208, 60, 180, 60, "Joystick", f"Present: {joystick_present}")

    draw_box(12, 132, 180, 60, "Last Movement", f"{last_movement_cmd if last_movement_cmd else '—'}")
    draw_box(208, 132, 180, 60, "Last Camera", f"{last_camera_cmd if last_camera_cmd else '—'}")

    # Telemetry area (multi-line)
    pygame.draw.rect(screen, (55,55,55), (12, 204, SCREEN_W-24, 84))
    # pygame.draw.rect(screen, (0,0,0), (12, 204, SCREEN_W-24, 84), 1)
    screen.blit(font.render("Telemetry (latest):", True, (255, 255, 255)), (18, 208))
    # wrap telemetry text if long
    telemetry_lines = []
    telemetry_text = last_telemetry if last_telemetry else ""
    # split into chunks of ~50 chars
    while telemetry_text:
        telemetry_lines.append(telemetry_text[:50])
        telemetry_text = telemetry_text[50:]
    for i, line in enumerate(telemetry_lines[:3]):
        screen.blit(font.render(line, True, (255, 255, 255)), (18, 232 + i*16))

    pygame.display.flip()

    # cap the loop
    clock.tick(20)

# -----------------------------
# Shutdown
# -----------------------------
try:
    if input_stream is not None:
        input_stream.stop()
        input_stream.close()
    if output_stream is not None:
        output_stream.stop()
        output_stream.close()
except Exception as e:
    pass

try:
    telemetry_sock.close()
    audio_sock.close()
    control_sock.close()
except Exception:
    pass

pygame.quit()
print("Exited cleanly.")



############################################################
# joystick controlls readings
# ----------------------------------------------------------
#   BUTTON                  |  ACTION
# ----------------------------------------------------------
# button right Y            | 0
# button right B            | 1
# button right A            | 2
# button right X            | 3
# ----------------------------------------------------------
# upper left front          | 4
# upper right front         | 5
# upper left back           | 6
# upper right back          | 7
# ----------------------------------------------------------
# select button             | 8
# start button              | 9
# left stick button         | 10
# right stick button        | 11
# guide button              | 12
# ----------------------------------------------------------
# hat-button left up        | ( 0,  1)
# hat-button left down      | ( 0, -1)
# hat-button left left      | (-1,  0)
# hat-button left right     | ( 1,  0)
# not used                  | (0,  0)
# ----------------------------------------------------------
# 
# 
# 
# ----------------------------------------------------------
#   STICKS          |  AXIS             |  ACTION
# ----------------------------------------------------------
# right stick up    | 3                 | [0, -1]
# right stick down  | 3                 | [1,  0]
# right stick left  | 2                 | [0, -1]
# right stick right | 2                 | [1,  0]
# ----------------------------------------------------------
# left stick up     | 1                 | [0, -1]
# left stick down   | 1                 | [1,  0]
# left stick left   | 0                 | [0, -1]
# left stick right  | 0                 | [1,  0]
# ----------------------------------------------------------
############################################################