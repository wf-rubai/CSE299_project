import sounddevice as sd
import socket
import threading
import numpy as np
import queue

# -------------------------
# CONFIGURATION
# -------------------------
PEER_IP = "192.168.192.218"  # replace with other device IP
UDP_PORT = 7000

INPUT_DEVICE = 0   # Voice HAT mic index (check with sd.query_devices())
OUTPUT_DEVICE = 1  # USB PnP Sound Device index (check with sd.query_devices())

FRAMESIZE = 1024
SAMPLERATE = 48000
GAIN = 4
# -------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

audio_queue = queue.Queue()

# -------------------------
# UDP receiver thread
# -------------------------
def udp_receiver():
    while True:
        data, _ = sock.recvfrom(FRAMESIZE * 2)
        samples = np.frombuffer(data, dtype=np.int16)
        audio_queue.put(samples)

threading.Thread(target=udp_receiver, daemon=True).start()

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
    sock.sendto(mono.tobytes(), (PEER_IP, UDP_PORT))

# -------------------------
# Start full-duplex streams
# -------------------------
with sd.InputStream(
    samplerate=SAMPLERATE,
    channels=1,  # Voice HAT is mono
    dtype='int16',
    blocksize=FRAMESIZE,
    device=INPUT_DEVICE,
    callback=record_callback
), sd.OutputStream(
    samplerate=SAMPLERATE,
    channels=2,  # USB DAC is stereo
    dtype='int16',
    blocksize=FRAMESIZE,
    device=OUTPUT_DEVICE,
    callback=playback_callback
):
    print("? FULL DUPLEX AUDIO ACTIVE")
    print(f"? Sending to {PEER_IP}:{UDP_PORT}, receiving on {UDP_PORT}")
    print("Press Ctrl+C to stop.")
    while True:
        pass
