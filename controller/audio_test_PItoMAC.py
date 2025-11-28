import sounddevice as sd
import socket
import numpy as np
import queue
import threading

UDP_PORT = 7000
framesize = 1024
samplerate = 48000
device_index = 1  # Mac output device (usually your speakers)

audio_queue = queue.Queue()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))

def udp_listener():
    while True:
        data, _ = sock.recvfrom(framesize * 2)
        samples = np.frombuffer(data, dtype=np.int16)
        audio_queue.put(samples)

def audio_callback(outdata, frames, time, status):
    try:
        vol_mult = 4    # Amplify audio
        chunk = audio_queue.get_nowait()
        chunk = np.clip(chunk * vol_mult, -32768, 32767).astype(np.int16)
        stereo = np.column_stack([chunk, chunk]).astype(np.int16)
        outdata[:] = stereo
    except queue.Empty:
        outdata.fill(0)

threading.Thread(target=udp_listener, daemon=True).start()
print("🔊 Mac is ready to play audio...")

with sd.OutputStream(
    samplerate=samplerate,
    channels=2,
    dtype='int16',
    blocksize=framesize,
    device=device_index,
    callback=audio_callback
):
    while True:
        pass
