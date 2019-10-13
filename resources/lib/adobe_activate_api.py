# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


try:
    from urlparse import urlunsplit
except ImportError:
    from urllib.parse import urlunsplit

try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import uuid
import hashlib
import hmac
import base64
import time
import requests
import logging

from resources.lib.settings_file import SettingsFile

adobe_settings = SettingsFile('adobe.json')
settings = adobe_settings.settings
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

adobe_session = requests.Session()
adobe_session.headers.update({
    'Accept': 'application/json',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-us',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': UA_ATV
})


logger = logging.getLogger(__name__)


class AuthorizationException(Exception):
    def __init__(self, resp):
        self.resp = resp


def get_device_id():
    if 'device_id' not in settings:
        settings['device_id'] = str(uuid.uuid1())
    return settings['device_id']


def is_expired(expiration):
    return (time.time() * 1000) >= int(expiration)


def get_url_response(url, message, body=None, method=None):
    headers = {'Authorization': message}

    if method == 'DELETE':
        resp = requests.delete(url, headers=headers)
        return dict()
    elif method == 'POST':
        resp = adobe_session.post(url, json=body, headers=headers)
    else:
        resp = adobe_session.get(url, headers=headers)
    return resp.json()


def generate_message(method, path):
    nonce = str(uuid.uuid4())
    today = str(int(time.time() * 1000))
    key = b'gB8HYdEPyezeYbR1'
    message = method + ' requestor_id=ESPN, nonce=' + nonce + \
        ', signature_method=HMAC-SHA1, request_time=' + today + ', request_uri=' + path
    signature = hmac.new(key, message.encode('utf-8'), hashlib.sha1)
    signature = base64.b64encode(signature.digest()).decode('utf-8')
    message = message + ', public_key=yKpsHYd8TOITdTMJHmkJOVmgbb2DykNK, signature=' + signature
    return message


def is_reg_code_valid():
    if 'generateRegCode' not in settings:
        logger.debug('Unable to find reg code')
        return False
    # Check code isn't expired
    expiration = settings['generateRegCode']['expires']
    if is_expired(expiration):
        logger.debug('Reg code is expired at %s' % expiration)
        return False
    return True


# Gets called when the user wants to authorize this device, it returns a registration code to enter
# on the activation website page
# Sample : '{"id":"","code":"","requestor":"ESPN","generated":1463616806831,
# "expires":1463618606831,"info":{"deviceId":"","deviceType":"appletv","deviceUser":null,
# "appId":null,"appVersion":null,"registrationURL":null}}'
# (generateRegCode)
def get_regcode():
    params = urlencode(
        {'deviceId': get_device_id(),
         'deviceType': 'appletv',
         'ttl': '1800'})

    path = '/regcode'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'reggie/v1/ESPN' + path,
                      params, ''])

    message = generate_message('POST', path)

    resp = get_url_response(url, message, dict(), 'POST')

    settings['generateRegCode'] = resp
    return resp['code']


# Authenticates the user after they have been authenticated on the activation website (authenticateRegCode)
# Sample: '{"mvpd":"","requestor":"ESPN","userId":"","expires":"1466208969000"}'
def authenticate(regcode):
    params = urlencode({'requestor': 'ESPN'})

    path = '/authenticate/' + regcode
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)
    settings['authenticateRegCode'] = resp


# Get authn token (re-auth device after it expires), getAuthnToken
def re_authenticate():
    params = urlencode({'requestor': 'ESPN',
                        'deviceId': get_device_id()})

    path = '/tokens/authn'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('GET', path)

    logger.debug('Attempting to re-authenticate the device')
    resp = get_url_response(url, message)
    if 'status' in resp and resp['status'] == '410':
        raise AuthorizationException(resp)
    settings['authenticateRegCode'] = resp
    if 'authorize' in settings:
        del settings['authorize']
    logger.debug('Re-authenticated device')


def get_resource(channel, event_name, event_guid, event_parental_rating):
    return '<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title><![CDATA[' + \
           channel + ']]></title><item><title><![CDATA[' + event_name + "]]></title><guid><![CDATA[" + \
           event_guid + ']]></guid><media:rating scheme="urn:v-chip"><![CDATA[' + event_parental_rating + \
           "]]></media:rating></item></channel></rss> "


def get_resource_key(resource):
    return str(resource.encode('utf-8'))


# Sample '{"resource":"resource","mvpd":"","requestor":"ESPN","expires":"1463621239000"}'
def authorize(resource):
    if is_authorized(resource):
        logger.debug('already authorized')
        return
    params = urlencode({'requestor': 'ESPN',
                        'deviceId': get_device_id(),
                        'resource': resource})

    path = '/authorize'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('GET', path)

    resp = get_url_response(url, message)

    if 'authorize' not in settings:
        settings['authorize'] = dict()
    logger.debug('resource %s resp %s' % (resource, resp))
    if 'status' in resp and resp['status'] == 403:
        raise AuthorizationException(resp)
    settings['authorize'][get_resource_key(resource)] = resp


def deauthorize():
    params = urlencode({'deviceId': get_device_id()})

    path = '/logout'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('DELETE', path)

    try:
        get_url_response(url, message, body=None, method='DELETE')
    except HTTPError:
        logger.debug('De-authorize failed')
    if 'authorize' in settings:
        del settings['authorize']
    if 'authenticateRegCode' in settings:
        del settings['authenticateRegCode']


# getShortMediaToken
# Sample '{"mvpdId":"","expires":"1463618218000","serializedToken":"+++++++=","userId":"",
# "requestor":"ESPN","resource":" resource"}'
def get_short_media_token(resource):
    if has_to_reauthenticate():
        logger.debug('re-authenticating device')
        re_authenticate()

    params = urlencode({'requestor': 'ESPN',
                        'deviceId': get_device_id(),
                        'resource': resource})

    path = '/mediatoken'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('GET', path)

    try:
        authorize(resource)
        resp = get_url_response(url, message)
        if 'status' in resp and resp['status'] == 403:
            raise AuthorizationException(resp)
    except HTTPError as exception:
        if exception.code == 401:
            logger.debug('Unauthorized exception, trying again')
            re_authenticate()
            authorize(resource)
            resp = get_url_response(url, message)
        else:
            logger.debug('Rethrowing exception %s' % exception)
            raise exception
    except AuthorizationException as exception:
        logger.debug('Authorization exception, trying again %s' % exception)
        re_authenticate()
        authorize(resource)
        resp = get_url_response(url, message)
        if 'status' in resp and resp['status'] == 403:
            raise AuthorizationException(resp)
    logger.debug('Resp %s' % resp)
    settings['getShortMediaToken'] = resp
    return resp['serializedToken']


def is_authenticated():
    return 'authenticateRegCode' in settings


def has_to_reauthenticate():
    if 'authenticateRegCode' in settings and 'expires' in settings['authenticateRegCode']:
        return is_expired(settings['authenticateRegCode']['expires'])
    return True


def is_authorized(resource):
    if 'authorize' in settings and get_resource_key(resource) in settings['authorize']:
        return not is_expired(settings['authorize'][get_resource_key(resource)]['expires'])


def get_expires_time(key):
    expires = settings[key]['expires']
    expires_time = time.localtime(int(expires) / 1000)
    return time.strftime('%Y-%m-%d %H:%M', expires_time)


def get_authentication_expires():
    return get_expires_time('authenticateRegCode')


def get_authorization_expires():
    return get_expires_time('authorize')


def clean_up_authorization_tokens():
    keys_to_delete = list()
    if 'authorize' in settings:
        for key in settings['authorize']:
            if 'expires' in settings['authorize'][key]:
                if is_expired(settings['authorize'][key]['expires']):
                    keys_to_delete.append(key)
            else:
                keys_to_delete.append(key)
    for key in keys_to_delete:
        del settings['authorize'][key]


def get_user_metadata():
    params = urlencode({'requestor': 'ESPN',
                        'deviceId': get_device_id()})

    path = '/tokens/usermetadata'
    url = urlunsplit(['https', 'api.auth.adobe.com',
                      'api/v1' + path,
                      params, ''])

    message = generate_message('GET', path)

    get_url_response(url, message)
