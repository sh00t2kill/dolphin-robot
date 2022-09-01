# dolphin-robot
A python reverse engineer attempt of the Maytronics Dolpin pool cleaner app

# example
from robot import Dolphin

robot = Dolphin()

robot.login(username, password)

registers = robot.Query()

print(registers)

# TODO
Need to work out what the hell each of the values returned from DynamoDB mean!