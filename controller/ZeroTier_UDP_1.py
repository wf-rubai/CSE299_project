# laptop_controller.py
import socket, pygame, threading

# -----------------------------
# Pi ZeroTier IP setup
# -----------------------------
PI_IP = "192.168.192.103"   # Pi ZeroTier IP
PI_PORT = 6000
MAC_PORT  = 6001      # to receive sensor data
INTERVAL = 0.05       # 50ms repeat

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", MAC_PORT))

# -----------------------------
# Pygame setup
# -----------------------------
pygame.init()
screen = pygame.display.set_mode((200,200))

pygame.joystick.init()
joystick_count = pygame.joystick.get_count()
if joystick_count != 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Detected joystick: {joystick.get_name()}")
    print(f"Number of axes: {joystick.get_numaxes()}")
    print(f"Number of buttons: {joystick.get_numbuttons()}")
    print(f"Number of hats: {joystick.get_numhats()}")
else:
    print("🚙 Use [W, A, S, D] keys to control the robot.")
    print("📷 Use Arrow keys to control the camera orientation.")

stick_key = None
stick_value = 0
current_key = None

# -----------------------------
# Receive telemetry thread
# -----------------------------
def recv_telemetry():
    while True:
        data, _ = sock.recvfrom(1024)
        print("Telemetry:", data.decode())

threading.Thread(target=recv_telemetry, daemon=True).start()

# -----------------------------
# Main loop
# -----------------------------
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            current_key = event.unicode
            if event.key == pygame.K_UP:
                current_key = 'U'
            elif event.key == pygame.K_DOWN:
                current_key = 'D'
            elif event.key == pygame.K_LEFT:
                current_key = 'L'
            elif event.key == pygame.K_RIGHT:
                current_key = 'R'   
                
            if current_key not in ['w','a','s','d','U','D','L','R']:
                current_key = None
        elif event.type == pygame.KEYUP:
            current_key = None
            
    if joystick_count != 0:
        pygame.event.pump() 
        # Read joystick axes
        axis_0 = joystick.get_axis(0)  # Left stick horizontal
        axis_1 = joystick.get_axis(1)  # Left stick vertical
        axis_2 = joystick.get_axis(2)  # Right stick horizontal
        axis_3 = joystick.get_axis(3)  # Right stick vertical
        
        # Determine key based on joystick position
        if abs(axis_0) > 0.1:
            current_key = 'L' if axis_0 < 0 else 'R'    # Cam Left/Right
        elif abs(axis_1) > 0.1:
            current_key = 'U' if axis_1 < 0 else 'D'    # Cam Up/Down
        elif abs(axis_2) > 0.1:
            current_key = 'd' if axis_3 < 0 else 'a'    # Bot Left/Right
        elif abs(axis_3) > 0.1:
            current_key = 's' if axis_2 < 0 else 'w'    # Bot Forward/Backward
        else:
            current_key = None
            
    if current_key:
        sock.sendto(current_key.encode(), (PI_IP, PI_PORT))
    pygame.time.delay(50)

pygame.quit()


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