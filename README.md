# dolphin-robot
A python reverse engineer attempt of the Maytronics Dolpin pool cleaner app

# example
robot = Dolphin()
robot.auth(<username>, <password>)
robot.getToken()

registers = robot.Query()
print(registers)