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
import os
from StringIO import StringIO

from globals import ADDON_PATH_PROFILE

SETTINGS_FILE = 'adobe.json'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

def save_settings(settings):
    settings_file = os.path.join(ADDON_PATH_PROFILE, SETTINGS_FILE)
    with open(settings_file, 'w') as fp:
        json.dump(settings, fp, sort_keys=True, indent=4)

def load_settings():
    settings_file = os.path.join(ADDON_PATH_PROFILE, SETTINGS_FILE)
    if not os.path.isfile(settings_file):
        save_settings(dict())
    with open(settings_file, 'r') as fp:
        return json.load(fp)

def get_device_id():
    settings = load_settings()
    if 'device_id' not in settings:
        settings['device_id'] = str(uuid.uuid1())
        save_settings(settings)
    return settings['device_id']

def get_regcode():
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

# TODO: Would need to store when reg code expires in case the user doesn't immediately
# activate the device
# called espn.regCode
resp = '{"id":"","code":"","requestor":"ESPN","generated":1463616806831,"expires":1463618606831,"info":{"deviceId":"","deviceType":"appletv","deviceUser":null,"appId":null,"appVersion":null,"registrationURL":null}}'
resp = json.loads(resp)
reg_code = resp['code']

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

content = '{"mvpd":"","requestor":"ESPN","userId":"","expires":"1466208969000"}'
# Called espn.authn
raw_input("Press Enter to continue...")

if False:
    # Get authn token (re-auth device after it expires), getAuthnToken
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


if False:
    # authorize
    nonce = str(uuid.uuid4())
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId' : device_id,
                               'resource' : 'TODO resource'})

    url = urlparse.urlunsplit(['https',
                                   'api.auth.adobe.com',
                                   'api/v1/authorize',
                                   params, ''])

    today = str(int(time.time() * 1000))
    key = 'gB8HYdEPyezeYbR1'
    message = 'GET requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/authorize'
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

content = '{"resource":"TODO resource","mvpd":"","requestor":"ESPN","expires":"1463621239000"}'

if True:
    # getShortMediaToken
    nonce = str(uuid.uuid4())
    params = urllib.urlencode({'requestor': 'ESPN',
                               'deviceId' : device_id,
                               'resource' : 'TODO resource'})

    url = urlparse.urlunsplit(['https',
                                   'api.auth.adobe.com',
                                   'api/v1/mediatoken',
                                   params, ''])

    today = str(int(time.time() * 1000))
    key = 'gB8HYdEPyezeYbR1'
    message = 'GET requestor_id=ESPN, nonce=' + nonce + ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=/mediatoken'
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

content = '{"mvpdId":"","expires":"1463618218000","serializedToken":"+++++++=","userId":"","requestor":"ESPN","resource":"TODO resource"}'

# serializedtoken = pkan