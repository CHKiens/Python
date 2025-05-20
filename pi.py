from gpiozero import OutputDevice
from gpiozero import LED
from time import sleep
from socket import *
import json
serverport = 11999
serversocket = socket(AF_INET, SOCK_DGRAM)

serveradress = ('', serverport)
serversocket.bind(serveradress)
#LED i GPIO port 17 og 18
red = LED(17)
green = LED(18)



current_position = "low"  # Default starting position



def save_position():
    global current_position
    with open("position.txt", "w") as f:
        f.write(current_position)

def load_position():
    global current_position
    try:
        with open("position.txt", "r") as f:
            current_position = f.read().strip()
    except FileNotFoundError:
        current_position = "low"  # Default starting position if file not found

def set_step_setting(setting):
    global current_position
    if setting != None:
        red.off()
        green.on()
    else:
        green.off()
        red.on()

    if setting == current_position:
        print(f"Already in {setting} position")
        return

    if setting == "low":
        print("Moving to low")
        if current_position == "medium":
            step_motor(steps_to_up, direction=-1)  # Move back 90 degrees
        elif current_position == "high":
            step_motor(steps_to_up + steps_to_down, direction=-1)  # Move back 180 degrees
        stop_motor()

    elif setting == "medium":
        print("Moving to medium")
        if current_position == "low":
            step_motor(steps_to_up, direction=1)  # Move forward 90 degrees
        elif current_position == "high":
            step_motor(steps_to_down, direction=-1)  # Move back 90 degrees

    elif setting == "high":
        print("Moving to high")
        if current_position == "low":
            step_motor(steps_to_up + steps_to_down, direction=1)  # Move forward 180 degrees
        elif current_position == "medium":
            step_motor(steps_to_down, direction=1)  # Move forward 90 degrees

    else:
        print("Invalid setting")
        green.off()
        red.on()
        return

    current_position = setting  # Update the current position

#GPIO-pins til ULN2003
IN1 = OutputDevice(6)
IN2 = OutputDevice(13)
IN3 = OutputDevice(19)
IN4 = OutputDevice(26)

#Stepsekvens til 28BYJ-48 (halv-step)
step_sequence = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
]

def set_step(step):
    IN1.value = step[0]
    IN2.value = step[1]
    IN3.value = step[2]
    IN4.value = step[3]

def step_motor(steps, delay=0.003, direction=1):
    for step in range(steps):
        for step in (step_sequence if direction == 1 else reversed(step_sequence)):
            set_step(step)
            sleep(delay)

def stop_motor():
    IN1.off()
    IN2.off()
    IN3.off()
    IN4.off()

#Positioner i antal steps (juster disse efter behov)
steps_to_middle = 0
steps_to_up = 130     # ca. 90 grader mod venstre
steps_to_down = 130   # ca. 90 grader mod højre

while True:

    message, clientadress = serversocket.recvfrom(1024)
    print("Modtaget besked fra klienten: ", message.decode())

    try:
        json_data = json.loads(message.decode().strip())
        setting = json_data

    except json.JSONDecodeError:
        print("Fejl i modtagelse af JSON data")
        setting = None
        green.off()
        red.on()

    if setting:
        load_position()
        set_step_setting(setting)
        save_position()