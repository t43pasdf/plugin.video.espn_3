#!/usr/bin/python2
import urlparse
import urllib
import uuid
import hashlib
import hmac
import base64
import urllib2
import random
import time
import json
import gzip
from StringIO import StringIO
from datetime import datetime

UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'
device_id = str(uuid.uuid1())

# Get regcode test generateRegCode
if False:
    nonce = str(uuid.uuid4())
    params = urllib.urlencode(
        {'deviceId': device_id,
         'deviceType': 'appletv',
         'ttl': '1800'})

    url = urlparse.urlunsplit(['https',
                                   'api.auth.adobe.com',
                                   'reggie/v1/ESPN/regcode',
                                   params, ''])

    today = str(int(time.time() * 1000))
    key = 'gB8HYdEPyezeYbR1'
    message = 'POST requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/regcode'
    signature = hmac.new(key, message, hashlib.sha1)
    signature = base64.b64encode(signature.digest())
    message = message + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + signature

    opener = urllib2.build_opener()
    opener.addheaders = [ ("Accept", "application/json"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                            ("Connection", "close"),
                            ("User-Agent", UA_ATV),
                            ("Authorization", message)]
    resp = opener.open(url, urllib.urlencode(dict()))
    resp = resp.read()
    print resp
    resp = json.loads(resp)
    reg_code = resp['code']

# TODO: Would need to store when reg code expires incase the user doesn't immediately
# activate the device
# called espn.regCode

raw_input("Press Enter to continue...")

if False:
    # Authenticate code test authenticateRegCode
    nonce = str(uuid.uuid4())
    params = urllib.urlencode({'requestor': 'ESPN'})

    url = urlparse.urlunsplit(['https',
                                   'api.auth.adobe.com',
                                   'api/v1/authenticate/' + reg_code,
                                   params, ''])

    today = str(int(time.time() * 1000))
    key = 'gB8HYdEPyezeYbR1'
    message = 'GET requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/authenticate/' + reg_code
    signature = hmac.new(key, message, hashlib.sha1)
    signature = base64.b64encode(signature.digest())
    message = message + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + signature

    opener = urllib2.build_opener()
    opener.addheaders = [ ("Accept", "application/json"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                            ("Connection", "close"),
                            ("User-Agent", UA_ATV),
                            ("Authorization", message)]
    resp = opener.open(url)
    if resp.info().get('Content-Encoding') == 'gzip':
        buf = StringIO(resp.read())
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()
    else:
        content = resp.read()

    print content

# Called espn.authn


# Get authn token
nonce = str(uuid.uuid4())
params = urllib.urlencode({'requestor': 'ESPN',
                           'deviceId' : device_id})

url = urlparse.urlunsplit(['https',
                               'api.auth.adobe.com',
                               'api/v1/tokens/authn',
                               params, ''])

today = str(int(time.time() * 1000))
key = 'gB8HYdEPyezeYbR1'
message = 'GET requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/tokens/authn'
signature = hmac.new(key, message, hashlib.sha1)
signature = base64.b64encode(signature.digest())
message = message + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + signature

opener = urllib2.build_opener()
opener.addheaders = [ ("Accept", "application/json"),
                        ("Accept-Encoding", "gzip, deflate"),
                        ("Accept-Language", "en-us"),
                        ("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8"),
                        ("Connection", "close"),
                        ("User-Agent", UA_ATV),
                        ("Authorization", message)]
resp = opener.open(url)
if resp.info().get('Content-Encoding') == 'gzip':
    buf = StringIO(resp.read())
    f = gzip.GzipFile(fileobj=buf)
    content = f.read()
else:
    content = resp.read()

print content

