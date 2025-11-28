# laptop_controller.py
import socket, pygame, threading

PI_IP = "192.168.192.103"   # Pi ZeroTier IP
PI_PORT = 6000
MAC_PORT  = 6001      # to receive sensor data
INTERVAL = 0.05       # 50ms repeat

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", MAC_PORT))

pygame.init()
screen = pygame.display.set_mode((200,200))
current_key = None

def recv_telemetry():
    while True:
        data, _ = sock.recvfrom(1024)
        print("Telemetry:", data.decode())

threading.Thread(target=recv_telemetry, daemon=True).start()

while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            current_key = event.unicode
        elif event.type == pygame.KEYUP:
            current_key = None
    if current_key:
        sock.sendto(current_key.encode(), (PI_IP, PI_PORT))
    pygame.time.wait(INTERVAL)
