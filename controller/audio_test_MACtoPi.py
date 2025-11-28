import sounddevice as sd
import socket
import numpy as np

PI_IP = "192.168.192.103"  # Pi IP
UDP_PORT = 7000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

samplerate = 48000
framesize = 1024

def callback(indata, frames, time, status):
    # if status:
    #     print(status)
    mono = indata[:, 0].astype(np.int16)
    sock.sendto(mono.tobytes(), (PI_IP, UDP_PORT))

with sd.InputStream(
    samplerate=samplerate,
    channels=1,
    dtype='int16',
    blocksize=framesize,
    callback=callback
):
    print("🎤 Sending mic audio to Pi...")
    input("Press Enter to stop.\n")
