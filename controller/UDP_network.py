import socket
import threading
import pygame
import time

# ======== CONFIGURATION =========
MY_IP = "0.0.0.0"           # Listen on all interfaces
MY_PORT = 5010              # Port to receive messages
OTHER_IP = "172.20.10.3"   # IP of the other device
OTHER_PORT = 5009           # Port to send messages
SEND_INTERVAL = 0.05        # 20 messages per second
# ================================

pygame.init()
screen = pygame.display.set_mode((200, 200))
pygame.display.set_caption("UDP 2-Way Comm")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind((MY_IP, MY_PORT))
sock.setblocking(False)

current_key = None
running = True

def listen():
    """Thread: Listen for incoming messages"""
    global running
    while running:
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received from {addr}: {data.decode()}")
        except BlockingIOError:
            pass
        time.sleep(0.01)

def send():
    """Thread: Continuously send current key"""
    global running
    while running:
        if current_key:
            sock.sendto(current_key.encode(), (OTHER_IP, OTHER_PORT))
        time.sleep(SEND_INTERVAL)

# Start threads
listener = threading.Thread(target=listen, daemon=True)
sender = threading.Thread(target=send, daemon=True)
listener.start()
sender.start()

# Main Pygame loop
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            current_key = pygame.key.name(event.key)
            print(f"Key pressed: {current_key}")

pygame.quit()
running = False
sock.close()
