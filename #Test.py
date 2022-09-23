#Test


from ast import Subscript
from encodings import utf_8
from robot import Dolphin
import json, pprint

#payload = "{\"TableName\":\"maytronics_iot_history\",\"Limit\":1,\"KeyConditionExpression\":\"musn = :val \",\"ScanIndexForward\":false,\"ExpressionAttributeValues\":{\":val\":{\"S\":\"blah\"}}}"
#test = json.loads(payload)
#pprint.pprint(test, indent=3)
#test = json.dumps(test)
#byte = b"'\000\024\n\002\030\002\n\002\020\000\n\002\b\002\n\002\030\002\n\002\b\005\b\003\030\0002\0020\001B\007\b\002\006\002\020\002R\033\020\003\032\0020\0048FX\002\006\f\n\004\b\007\020\b\032\004\b\005\020\006\006\t"
#byte2 = str("'\000\024\n\002\030\002\n\002\020\000\n\002\b\002\n\002\030\002\n\002\b\005\b\003\030\0002\0020\001B\007\b\002\006\002\020\002R\033\020\003\032\0020\0048FX\002\006\f\n\004\b\007\020\b\032\004\b\005\020\006\006\t")
#byte2 = bytearray(byte2, encoding="utf=8")
#print(byte2.decode(encoding="utf-8"))

dolphin = Dolphin()
login = dolphin.login('your@login.com','password')
token = dolphin.getToken()
#dolphin.subscribe("$aws/things/{}/shadow/get/accepted".format(dolphin.serial))
#dolphin.subscribe("$aws/things/{}/shadow/name/AwsShadowInterface/get/accepted".format(dolphin.serial))
#dolphin.subscribe("Maytronics/D2691ZNC/main".format(dolphin.serial))

#dolphin.subscribe("$aws/things/{}".format(dolphin.serial))
dolphin.subscribe([("$aws/things/{}/shadow/get/accepted".format(dolphin.serial)), ("$aws/things/{}/shadow/get".format(dolphin.serial)), ("$aws/things/{}/shadow/update/accepted".format(dolphin.serial)), ("$aws/things/{}/shadow/update/rejected".format(dolphin.serial)), ("$aws/things/{}/shadow/get/rejected".format(dolphin.serial)), ("$aws/things/{}/shadow/update/delta".format(dolphin.serial)), ("$aws/things/{}/shadow/update".format(dolphin.serial)), ("Maytronics/D2691ZNC/main".format(dolphin.serial))])
#dolphin.subscribe([("$aws/things/{}/shadow/get/accepted".format(dolphin.serial)), ("$aws/things/{}/shadow/get".format(dolphin.serial)), ("$aws/things/{}/shadow/update/accepted".format(dolphin.serial)), ("$aws/things/{}/shadow/update/rejected".format(dolphin.serial)), ("$aws/things/{}/shadow/get/rejected".format(dolphin.serial)), ("$aws/things/{}/shadow/update/delta".format(dolphin.serial)), ("$aws/things/{}/shadow/update".format(dolphin.serial))])

print(login)

