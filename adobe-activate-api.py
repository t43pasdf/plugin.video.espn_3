#!/usr/bin/python2
import urlparse
import urllib
import uuid
import hashlib
import binascii
import base64
import urllib2
import random
import time
from datetime import datetime

# Get regcode test
device_id = ''.join([random.choice('0123456789abcdef') for x in range(16)])
nonce = str(uuid.uuid1())
params = urllib.urlencode(
    {'deviceId': device_id,
     'deviceType': 'appletv',
     'ttl': '1800'})

url = urlparse.urlunsplit(['https',
                               'api.auth.adobe.com',
                               'reggie/v1/ESPN/regcode',
                               params, ''])
# today = datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
today = str(int(time.time()))
salt = 'gB8HYdEPyezeYbR1'
d = 'POST requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/regcode'
h = hashlib.pbkdf2_hmac('sha1', d, salt, 100000)
h = binascii.hexlify(h)
h = base64.b64encode(h)
d = d + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + h

print d

body_contents = dict()
body_contents['requestor_id'] = 'ESPN'
body_contents['nonce'] = nonce
body_contents['signature_method'] = 'HMAC-SHA1'
body_contents['request_time'] = today
body_contents['request_uri'] = '/regcode'
body_contents['public_key'] = 'yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK'
body_contents['signature'] = h
body = urllib.urlencode(body_contents)

print body
print url

opener = urllib2.build_opener()
resp = opener.open(url, body)
print resp.read()

