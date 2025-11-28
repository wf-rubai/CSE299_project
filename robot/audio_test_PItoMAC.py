import sounddevice as sd
import socket
import numpy as np

UDP_IP = "192.168.192.103"  # <-- Mac's IP
UDP_PORT = 7000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

samplerate = 48000
framesize = 1024
device_index = 1  # Check with `arecord -l` or `sd.query_devices()`

def callback(indata, frames, time, status):
    # if status:
    #     print(status)
    mono = indata[:, 0].astype(np.int16)
    sock.sendto(mono.tobytes(), (UDP_IP, UDP_PORT))

with sd.InputStream(
    samplerate=samplerate,
    channels=1,       # mono
    dtype='int16',
    blocksize=framesize,
    device=device_index,
    callback=callback
):
    print("🎤 Sending Pi mic audio to Mac...")
    input("Press Enter to stop.\n")
