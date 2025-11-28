import sounddevice as sd
import socket
import threading
import numpy as np
import queue
import pygame

# -------------------------
# CONFIGURATION
# -------------------------
PEER_IP = "192.168.192.103"  # Pi IP
UDP_PORT = 7000

INPUT_DEVICE = None   # default mic
OUTPUT_DEVICE = None  # default speaker

FRAMESIZE = 1024
SAMPLERATE = 48000
GAIN = 4

# -------------------------
# Flags
# -------------------------
mic_on = False
speaker_on = True

# -------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

audio_queue = queue.Queue()

# -------------------------
# UDP Receiver Thread
# -------------------------
def udp_receiver():
    while True:
        # if speaker_on:
        data, _ = sock.recvfrom(FRAMESIZE * 2)
        samples = np.frombuffer(data, dtype=np.int16)
        audio_queue.put(samples)

threading.Thread(target=udp_receiver, daemon=True).start()

# -------------------------
# Playback Callback
# -------------------------
def playback_callback(outdata, frames, time, status):
    if speaker_on:
        try:
            chunk = audio_queue.get_nowait()
            chunk = np.clip(chunk * GAIN, -32768, 32767).astype(np.int16)
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

# -------------------------
# Record Callback
# -------------------------
def record_callback(indata, frames, time, status):
    if mic_on:
        mono = indata[:, 0].astype(np.int16)
        mono = np.clip(mono * GAIN, -32768, 32767).astype(np.int16)
        sock.sendto(mono.tobytes(), (PEER_IP, UDP_PORT))

# -------------------------
# Initialize pygame for key press
# -------------------------
pygame.init()
screen = pygame.display.set_mode((200, 100))
pygame.display.set_caption("Mic/Speaker Toggle")

# -------------------------
# Start audio streams
# -------------------------
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

print("🎧 Full duplex audio started!")
print("Press 'M' to toggle Mic/Speaker on/off.")

# -------------------------
# Main loop for keypress
# -------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                mic_on = not mic_on
                speaker_on = not speaker_on
                print(f"Mic {'ON' if mic_on else 'OFF'} | Speaker {'ON' if speaker_on else 'OFF'}")

# -------------------------
# Stop streams
# -------------------------
input_stream.stop()
output_stream.stop()
pygame.quit()
