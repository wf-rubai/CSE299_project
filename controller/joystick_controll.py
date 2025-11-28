import pygame

pygame.init()
pygame.joystick.init()

# Check for joysticks
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("No joystick detected.")
    exit()

# Get the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Detected joystick: {joystick.get_name()}")
print(f"Number of axes: {joystick.get_numaxes()}")
print(f"Number of buttons: {joystick.get_numbuttons()}")
print(f"Number of hats: {joystick.get_numhats()}")

done = False
while not done:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        
        # Joystick button events
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Button {event.button} pressed")
        # if event.type == pygame.JOYBUTTONUP:
        #     print(f"Button {event.button} released")

    # Get current state of joystick
    # A continuous loop is required to keep the event queue updated.
    pygame.event.pump() 
    
    # Get axis values (e.g., analog sticks)
    for i in range(joystick.get_numaxes()):
        axis = joystick.get_axis(i)
        if abs(axis) > 0.1: # Add a dead zone
            print(f"Axis {i} value: {axis:>6.3f}")

    # Get hat values (e.g., D-pad)
    for i in range(joystick.get_numhats()):
        hat = joystick.get_hat(i)
        if hat != (0, 0):
            print(f"Hat {i} value: {hat}")
            
    # Add a small delay to prevent excessive CPU usage
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