from multiprocessing.pool import RUN
from smtpd import DebuggingServer
from wsgiref.headers import Headers
import requests
import json
import sys, os, base64, datetime, hashlib, hmac
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import AWSIoTPythonSDK
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import uuid
import time

class Dolphin:

    LOGIN_URL       = "https://mbapp18.maytronics.com/api/users/Login/"
    TOKEN_URL       = "https://mbapp18.maytronics.com/api/IOT/getToken/"
    DYNAMODB_URL    = "https://dynamodb.eu-west-1.amazonaws.com/"
    DYNAMODB_REGION = "eu-west-1"
    DYNAMODB_HOST   = 'dynamodb.eu-west-1.amazonaws.com'
    IOT_URL         =  "a12rqfdx55bdbv-ats.iot.eu-west-1.amazonaws.com"
    Debug           = 1
    Headers         = {
                        'appkey': '346BDE92-53D1-4829-8A2E-B496014B586C',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
                      }

    login_token = ''
    aws_token   = ''
    serial      = ''
    aws_token   = ''
    aws_key     = ''
    aws_secret  = ''
    awsiot_id   = ''
    awsiot_client = False

    def __init__(self):
      #Nothing really to do here
        self.awsiot_id = str(uuid.uuid4())
        if (self.Debug):
            print("Maytonics Dolphin+ API via the Dark Arts")
            print("====================================")
            print("")  

    def login(self, username, password):
      authreq = self.auth(username, password)
      if not authreq:
        print ("ERROR!!!!!")
        raise RuntimeError('Unable to authenticate to service')
        
      tokenreq = self.getToken()
      if  not tokenreq:
        print ("ERROR!!!!!")
        raise RuntimeError('Unable to retrieve token from service')
        exit()

    def auth(self, username, password):
      # Create the payload
      payload='Email=' + username + '&Password=' + password
      response = requests.request("POST", self.LOGIN_URL, headers=self.Headers, data=payload)
      data = json.loads(response.text)

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
       payload='Sernum=' + self.serial
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
      string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
      signing_key = self.getSignatureKey(self.aws_secret, date_stamp, self.DYNAMODB_REGION, service)
      signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

      authorization_header = algorithm + ' ' + 'Credential=' + self.aws_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature
      headers = {'Content-Type':content_type,
           'X-Amz-Date':amz_date,
           'X-Amz-Target':amz_target,
           'Authorization':authorization_header,
           'X-Amz-Security-Token':self.aws_token}

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
          print (count, x)
          count = count + 1

      schedule_type = system_data[110]["S"]
      work_type = system_data[115]["S"]

      return_data = {
        "turn_on_count": turn_on,
        "schedule_type": schedule_type,
        "work_type": work_type,
        "timestamp": timestamp,
        "last_run_status": self.mapWorkType(work_type)
      }

      return return_data

    def mapWorkType(self, work_type):
      match work_type:
        case "cloud":
          return "Cancelled"
        case _:
          return work_type


    def buildClient(self):
      script_dir = os.path.dirname(__file__)
      ca_file = "AmazonRootCA1.pem"
      ca_file_path = os.path.join(script_dir, ca_file)
      myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(self.awsiot_id, useWebsocket=True)
      myAWSIoTMQTTClient.configureEndpoint(self.IOT_URL, 443)
      #print(ca_file_path)
      myAWSIoTMQTTClient.configureCredentials(ca_file_path)
      myAWSIoTMQTTClient.configureIAMCredentials(self.aws_key, self.aws_secret, self.aws_token)
      myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
      myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
      myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
      myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)
      myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)
      myAWSIoTMQTTClient.enableMetricsCollection()
      print("Our client is setup, lets try and connect")
      myAWSIoTMQTTClient.connect() 
      print("Connected!")
      self.awsiot_client = myAWSIoTMQTTClient

    def subscribe(self, topic):
      if not self.awsiot_client:
        self.buildClient()
      while True:
        self.awsiot_client.subscribe(topic, 1, self.customCallback)
        time.sleep(1)

    def publish(self, topic, message):
      if not self.awsiot_client:
        self.buildClient()
      
      self.awsiot_client.publish(topic, message)

    def customCallback(client, userdata, message):
      print(client)
      print (userdata)
      print(message)

