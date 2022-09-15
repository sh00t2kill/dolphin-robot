import base64
import datetime
import hashlib
import hmac
import json
from multiprocessing.pool import RUN
import os
from smtpd import DebuggingServer
import sys
import time
import uuid
from wsgiref.headers import Headers

import AWSIoTPythonSDK
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import paho.mqtt.client as paho
import requests

"""
class Dolphin:
    LOGIN_URL = "https://mbapp18.maytronics.com/api/users/Login/"
    TOKEN_URL = "https://mbapp18.maytronics.com/api/IOT/getToken/"
    DYNAMODB_URL = "https://dynamodb.eu-west-1.amazonaws.com/"
    DYNAMODB_REGION = "eu-west-1"
    DYNAMODB_HOST = 'dynamodb.eu-west-1.amazonaws.com'
    IOT_URL = "a12rqfdx55bdbv-ats.iot.eu-west-1.amazonaws.com"
    LISTEN_TOPIC = "$aws/things/{}/shadow/get/accepted"
    DYNAMIC_TOPIC = "Maytronics/{}/main"
    Debug = 1
    Headers = {
        'appkey': '346BDE92-53D1-4829-8A2E-B496014B586C',
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
    }
    ca_file = "custom_components/mydolphin_plus/component/api/AmazonRootCA.pem"
    login_token = ''
    aws_token = ''
    serial = ''
    aws_token = ''
    aws_key = ''
    aws_secret = ''
    awsiot_id = ''
    awsiot_client = False

    LOCAL_STATE_TOPIC = 'robot/state'

    def __init__(self):
        # Nothing really to do here
        self.awsiot_id = str(uuid.uuid4())
        if (self.Debug):
            print("Maytonics Dolphin+ API via the Dark Arts")
            print("====================================")
            print("")

    def getSerial(self):
        return self.serial

    def setLocalBroker(self, broker, port, username=None, password=None):
        self.mqtt_client = paho.Client(self.awsiot_id)
        self.mqtt_client.connect(broker, port)

    def localPublish(self, message):
        print(f"local publish: {message}")
        self.mqtt_client.publish(self.LOCAL_STATE_TOPIC, message)

    def login(self, username, password):
        authreq = self.auth(username, password)
        if not authreq:
            print("ERROR!!!!!")
            raise RuntimeError('Unable to authenticate to service')

        tokenreq = self.getToken()
        if not tokenreq:
            print("ERROR!!!!!")
            raise RuntimeError('Unable to retrieve token from service')
            exit()

    def auth(self, username, password):
        # Create the payload
        payload = 'Email=' + username + '&Password=' + password
        response = requests.request("POST", self.LOGIN_URL, headers=self.Headers, data=payload)
        data = json.loads(response.text)

        print(response.text)

        try:
            serial = data['Data']['Sernum']
            token = data['Data']['token']
            actual_serial = serial[:-2]
        except TypeError:
            return False
        if (self.Debug):
            print("Found device:" + serial)
            print("Found token: " + token)

        self.serial = actual_serial
        self.login_token = token

        return True

    def getToken(self):
        self.Headers['token'] = self.login_token
        payload = 'Sernum=' + self.serial
        response = requests.request("POST", self.TOKEN_URL, headers=self.Headers, data=payload)
        data = json.loads(response.text)

        try:
            aws_token = data['Data']['Token']
            aws_key = data['Data']['AccessKeyId']
            aws_secret = data['Data']['SecretAccessKey']
        except:
            return False

        self.aws_token = aws_token
        self.aws_key = aws_key
        self.aws_secret = aws_secret

        if (self.Debug):
            print("AWS Key:" + aws_key)
            print("AWS Secret:" + aws_secret)
            print("Found aws signature token: " + data['Data']['Token'])

        return True

    def sign(self, key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    # This is pretty much straight out of AWS documentation RE creating a signature.
    # Im not convinced its doing anything but every time it gets touched, things break
    def getSignatureKey(self, key, date_stamp, regionName, serviceName):
        kDate = self.sign(('AWS4' + key).encode('utf-8'), date_stamp)
        kRegion = self.sign(kDate, regionName)
        kService = self.sign(kRegion, serviceName)
        kSigning = self.sign(kService, 'aws4_request')
        return kSigning

    def createAWSHeader(self, service, payload):
        content_type = 'application/x-amz-json-1.0'
        amz_target = 'DynamoDB_20120810.Query'
        method = 'POST'

        t = datetime.datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')

        canonical_uri = '/'
        canonical_querystring = ''

        canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + self.DYNAMODB_HOST + '\n' + 'x-amz-date:' + amz_date + '\n' + 'x-amz-target:' + amz_target + '\n'

        signed_headers = 'content-type;host;x-amz-date;x-amz-target'
        payload_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = date_stamp + '/' + self.DYNAMODB_REGION + '/' + service + '/' + 'aws4_request'
        string_to_sign = algorithm + '\n' + amz_date + '\n' + credential_scope + '\n' + hashlib.sha256(
            canonical_request.encode('utf-8')).hexdigest()
        signing_key = self.getSignatureKey(self.aws_secret, date_stamp, self.DYNAMODB_REGION, service)
        signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

        authorization_header = algorithm + ' ' + 'Credential=' + self.aws_key + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
        headers = {'Content-Type': content_type,
                   'X-Amz-Date': amz_date,
                   'X-Amz-Target': amz_target,
                   'Authorization': authorization_header,
                   'X-Amz-Security-Token': self.aws_token}

        return headers

    def Query(self):
        payload = "{\"TableName\":\"maytronics_iot_history\",\"Limit\":1,\"KeyConditionExpression\":\"musn = :val \",\"ScanIndexForward\":false,\"ExpressionAttributeValues\":{\":val\":{\"S\":\"" + self.serial + "\"}}}"
        service = 'dynamodb'
        headers = self.createAWSHeader(service, payload)
        request = requests.post(self.DYNAMODB_URL, data=payload, headers=headers)
        return request

    def mapQuery(self):
        resp = self.Query()
        data = resp.json()

        items = data['Items'][0]
        turn_on = items['rTurnOnCount']["N"]
        system_data = items['SystemData']['L']
        timestamp = items['SystemDataTimeStamp']["S"]
        count = 0
        if (self.Debug):
            for x in system_data:
                print(count, x)
                count = count + 1

        job_trigger = system_data[110]["S"]
        work_type = system_data[115]["S"]

        return_data = {
            "turn_on_count": turn_on,
            "job_trigger": job_trigger,
            "work_type": work_type,
            "timestamp": timestamp,
            "last_run_status": self.mapWorkType(work_type)
        }

        return return_data

    def mapWorkType(self, work_type):
        match work_type:
            case "cloud":
                return "cancelled"
            case _:
                return work_type

    def buildClient(self):
        script_dir = os.path.dirname(__file__)
        ca_file_path = os.path.join(script_dir, self.ca_file)
        myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.awsiot_id, useWebsocket=True)
        myAWSIoTMQTTClient.configureEndpoint(self.IOT_URL, 443)
        myAWSIoTMQTTClient.configureCredentials(ca_file_path)
        myAWSIoTMQTTClient.configureIAMCredentials(self.aws_key, self.aws_secret, self.aws_token)
        myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
        myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)
        myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)
        myAWSIoTMQTTClient.enableMetricsCollection()
        if (self.Debug):
            print("Connecting to " + self.IOT_URL)
        connected = myAWSIoTMQTTClient.connect()
        if (self.Debug):
            print("Connected!!!")
        if not connected:
            raise ConnectionError

        self.awsiot_client = myAWSIoTMQTTClient
        return True

    def subscribeAsync(self, topic):
        if not self.awsiot_client:
            self.buildClient()
        self.callbackmessage = None
        self.awsiot_client.subscribeAsync(topic, 0, None, self.customCallback)

    def listen(self):
        self.subscribe(self.LISTEN_TOPIC.format(self.getSerial()))
        # self.subscribe(self.DYNAMIC_TOPIC.format(self.getSerial()))

    def subscribe(self, topic):
        if not self.awsiot_client:
            self.buildClient()
        self.callbackmessage = None
        while True:
            self.awsiot_client.subscribe(topic, 0, self.customCallback)
            time.sleep(1)

    def publish(self, topic, message):
        if not self.awsiot_client:
            self.buildClient()

        self.awsiot_client.publish(topic, message, 1)

    def parseMsg(self, message):
        state = message['state']
        reported = state['reported']
        connected = reported['isConnected']['connected']
        system_state = reported['systemState']
        power_state = system_state['pwsState']
        return {"connected": connected, "state": power_state}

    def getPowerState(self, message):
        parsed = self.parseMsg(message)
        return parsed['state']

    def customCallback(self, client, userdata, message):
        jsonstr = str(message.payload.decode("utf-8"))
        callbackmessage = json.loads(jsonstr)
        try:
            parsed = self.parseMsg(callbackmessage)
            if (self.Debug):
                print(parsed)
            if (self.mqtt_client):
                self.localPublish(parsed)
        except KeyError:
            print(jsonstr)
        return callbackmessage
"""
