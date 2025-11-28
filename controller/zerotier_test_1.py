import socket
import threading
import pygame
import time
import json

# --- Settings ---
LOCAL_PORT = 5004
OTHER_IP = "192.168.192.103"    # replace with peer's ZeroTier IP
OTHER_PORT = 5005
SEND_INTERVAL = 0.01     # seconds

# --- Shared state ---
current_key = None
current_event_type = None
running = True

# --- Setup UDP ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))
sock.setblocking(False)  # non-blocking recv

# --- Listener thread ---
def listen():
    global running
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            payload = json.loads(data.decode())
            print(f"Received from {addr}: {payload['type']} {payload['key']}")
        except BlockingIOError:
            pass
        except json.JSONDecodeError:
            print("Received invalid JSON")
        time.sleep(0.01)

# --- Sender thread ---
def send():
    global running
    while running:
        if current_key:
            msg = {
                "type": current_event_type,
                "key": current_key,
                "time": time.time()
            }
            sock.sendto(json.dumps(msg).encode(), (OTHER_IP, OTHER_PORT))
        time.sleep(SEND_INTERVAL)

# --- Start threads ---
threading.Thread(target=listen, daemon=True).start()
threading.Thread(target=send, daemon=True).start()

# --- Pygame setup ---
pygame.init()
screen = pygame.display.set_mode((200, 200))
pygame.display.set_caption("UDP 2-Way Comm")

# --- Main loop ---
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            current_key = pygame.key.name(event.key)
            current_event_type = "keydown"
            print(f"Key pressed: {current_key}")
        elif event.type == pygame.KEYUP:
            current_key = pygame.key.name(event.key)
            current_event_type = "keyup"
            print(f"Key released: {current_key}")
            current_key = None  # stop sending until next key press

    time.sleep(0.01)

pygame.quit()
running = False
sock.close()
