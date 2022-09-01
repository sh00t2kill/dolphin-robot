from smtpd import DebuggingServer
from wsgiref.headers import Headers
import requests
import json
import sys, os, base64, datetime, hashlib, hmac

class Dolphin:

    LOGIN_URL       = "https://mbapp18.maytronics.com/api/users/Login/"
    TOKEN_URL       = "https://mbapp18.maytronics.com/api/IOT/getToken/"
    DYNAMODB_URL    = "https://dynamodb.eu-west-1.amazonaws.com/"
    DYNAMODB_REGION = "eu-west-1"
    DYNAMODB_HOST   = 'dynamodb.eu-west-1.amazonaws.com'
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

    def __init__(self):
      #Nothing really to do here
        if (self.Debug):
            print("Petoneer Python API via the Dark Arts")
            print("====================================")
            print("")  

    def login(self, username, password):
      self.auth(username, password)
      self.getToken()

    def auth(self, username, password):
      # Create the payload
      payload='Email=' + username + '&Password=' + password
      response = requests.request("POST", self.LOGIN_URL, headers=self.Headers, data=payload)
      data = json.loads(response.text)
      serial = data['Data']['Sernum']
      token = data['Data']['token']
      actual_serial = serial[:-2]

      self.serial = actual_serial
      self.login_token = token

      return True


    def getToken(self):
       self.Headers['token'] = self.login_token
       payload='Sernum=' + self.serial
       response = requests.request("POST", self.TOKEN_URL, headers=self.Headers, data=payload)
       data = json.loads(response.text)
       aws_token = data['Data']['Token']
       aws_key = data['Data']['AccessKeyId']
       aws_secret = data['Data']['SecretAccessKey']  

       self.aws_token = aws_token
       self.aws_key = aws_key
       self.aws_secret = aws_secret

       return True

    def sign(self, key, msg):
       return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def getSignatureKey(self, key, date_stamp, regionName, serviceName):
       kDate = self.sign(('AWS4' + key).encode('utf-8'), date_stamp)
       kRegion = self.sign(kDate, regionName)
       kService = self.sign(kRegion, serviceName)
       kSigning = self.sign(kService, 'aws4_request')
       return kSigning

    def Query(self):
      content_type = 'application/x-amz-json-1.0'
      amz_target = 'DynamoDB_20120810.Query'
      method = 'POST'
      service = 'dynamodb'

      payload = "{\"TableName\":\"maytronics_iot_history\",\"Limit\":40,\"KeyConditionExpression\":\"musn = :val \",\"ScanIndexForward\":false,\"ExpressionAttributeValues\":{\":val\":{\"S\":\"D2382TQM\"}}}"


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

      request = requests.post(self.DYNAMODB_URL, data=payload, headers=headers)
      return request.text



