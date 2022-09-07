#Test

from ast import Subscript
from robot import Dolphin

dolphin = Dolphin()

token = dolphin.getToken()
#dolphin.subscribe("$aws/things/{}/shadow/get/accepted".format(dolphin.serial))
dolphin.subscribe("Maytronics/D2691ZNC/main".format(dolphin.serial))
print(login)

