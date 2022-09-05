from robot import Dolphin
# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK
Robot = Dolphin()
DolphinLogin = Robot.login(username="jasondanieladams@gmail.com", password="Bonzai1957!")

import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT

# Create an AWS IoT MQTT Client using TLSv1.2 Mutual Authentication
myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("testIoTPySDK")
# Create an AWS IoT MQTT Client using Websocket SigV4
myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient("testIoTPySDK", useWebsocket=True)
myAWSIoTMQTTClient.configureEndpoint("iot.us-east-2.amazonaws.com", 8883)
myAWSIoTMQTTClient.configureIAMCredentials(Robot.aws_key, Robot.aws_secret, Robot.aws_token)

myAWSIoTMQTTClient.connect()

#AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.configureEndpoint("a12rqfdx55bdbv-ats.iot.eu-west-1.amazonaws.com", 8883)
# AWS IoT MQTT Client
#AWSIoTPythonSDK.configureIAMCredentials(Robot.aws_key, Robot.aws_secret, Robot.aws_token)
# AWS IoT MQTT Shadow Client
#AWSIoTPythonSDK.MQTTLib.AWSIoTMQTTShadowClient.configureIAMCredentials(Robot.aws_key, Robot.aws_secret, Robot.aws_token)
pass
#DolpinAuth = Robot.auth(username="jasondanieladams@gmail.com",password="Bonzai1957!")

