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


import time

try:
    import jwt
except ImportError:
    import pyjwt as jwt
import json
import logging
import uuid

try:
    import thread
except ImportError:
    import _thread as thread

from resources.lib.globals import global_session
from resources.lib.settings_file import SettingsFile
from resources.lib import util, websocket

# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

WEB_ID = 'ESPN-ONESITE.WEB-PROD'
ANDROID_ID = 'ESPN-OTT.GC.ANDTV-PROD'
DISNEY_ROOT_URL = 'https://registerdisney.go.com/jgc/v6/client'
API_KEY_URL = DISNEY_ROOT_URL + '/{id-provider}/api-key?langPref=en-US'
LOGIN_URL = DISNEY_ROOT_URL + '/{id-provider}/guest/login?langPref=en-US'
LICENSE_PLATE_URL = DISNEY_ROOT_URL + '/{id-provider}/license-plate'
REFRESH_AUTH_URL = DISNEY_ROOT_URL + '/{id-provider}/guest/refresh-auth?langPref=en-US'
BAM_API_KEY = 'ZXNwbiZicm93c2VyJjEuMC4w.ptUt7QxsteaRruuPmGZFaJByOoqKvDP2a5YkInHrc7c'
BAM_APP_CONFIG = 'https://bam-sdk-configs.bamgrid.com/bam-sdk/v2.0/espn-a9b93989/browser/v3.4/linux/chrome/prod.json'
GRACE_TIME_SECONDS = 10800  # 3 hour grace time for token expiration


logger = logging.getLogger(__name__)


def is_token_valid(encoded_token):
    token = jwt.decode(encoded_token, verify=False)
    return time.time() < token['exp']


def is_token_within_grace_period(encoded_token):
    token = jwt.decode(encoded_token, verify=False)
    return (time.time() + GRACE_TIME_SECONDS) < token['exp']


class TokenExchange(object):
    def __init__(self, token_dict):
        self.access_token = token_dict['access_token']
        self.refresh_token = token_dict['refresh_token']

    def is_access_token_valid(self):
        return is_token_valid(self.access_token)

    def is_access_token_within_grace_period(self):
        return is_token_within_grace_period(self.access_token)

    def is_refresh_token_valid(self):
        return is_token_valid(self.refresh_token)


class DisneyToken(object):
    def __init__(self, token_dict):
        self.grant_time_utc = token_dict['grant_time_utc']
        self.access_token = token_dict['access_token']
        self.access_token_ttl = token_dict['ttl']
        self.refresh_token = token_dict['refresh_token']
        self.refresh_token_ttl = token_dict['refresh_ttl']
        self.swid = token_dict['swid']
        self.id_token = token_dict['id_token']

    def is_refresh_token_valid(self):
        return time.time() < self.grant_time_utc + self.refresh_token_ttl


class Assertion(object):
    def __init__(self, grant_dict):
        self.assertion = grant_dict['assertion']

    def is_valid(self):
        return is_token_valid(self.assertion)


class Token(object):
    def __init__(self, token):
        self.token = token

    def is_valid(self):
        return is_token_valid(self.token)


class EspnPlusConfig(SettingsFile):
    def __init__(self):
        SettingsFile.__init__(self, 'espnplus.json')
        self.load_tokens()

    def load_tokens(self):
        self.account_token = None
        self.id_token_grant = None
        self.disney_id_token = None
        self.device_token_exchange = None
        self.device_refresh_token = None
        self.device_grant = None
        self.disney_token = None
        if 'accountToken' in self.settings:
            self.account_token = TokenExchange(self.settings['accountToken'])
        if 'idTokenGrant' in self.settings:
            self.id_token_grant = Assertion(self.settings['idTokenGrant'])
        if 'disneyIdToken' in self.settings:
            self.disney_id_token = Token(self.settings['disneyIdToken'])
        if 'deviceTokenExchange' in self.settings:
            self.device_token_exchange = TokenExchange(self.settings['deviceTokenExchange'])
        if 'deviceRefreshToken' in self.settings:
            self.device_refresh_token = TokenExchange(self.settings['deviceRefreshToken'])
        if 'deviceGrant' in self.settings:
            self.device_grant = Assertion(self.settings['deviceGrant'])
        if 'disneyToken' in self.settings:
            self.disney_token = DisneyToken(self.settings['disneyToken'])

    def get_subscriptions(self):
        if 'subscriptions' in self.settings:
            return self.settings['subscriptions']
        return None

    def set_subscriptions(self, subscriptions):
        self.settings['subscriptions'] = subscriptions

    def set_device_grant(self, device_grant):
        self.settings['deviceGrant'] = device_grant
        self.load_tokens()

    def set_device_token_exchange(self, token_exchange):
        self.settings['deviceTokenExchange'] = token_exchange
        self.load_tokens()

    def set_device_refresh_token(self, token_exchange):
        self.settings['deviceRefreshToken'] = token_exchange
        self.load_tokens()

    def set_disney_id_token(self, id_token):
        self.settings['disneyIdToken'] = id_token
        self.load_tokens()

    def set_disney_token(self, disney_token):
        disney_token['grant_time_utc'] = time.time()
        self.settings['disneyToken'] = disney_token
        self.load_tokens()

    def set_id_token_grant(self, grant_resp):
        self.settings['idTokenGrant'] = grant_resp
        self.load_tokens()

    def set_account_token(self, token_exchange):
        self.settings['accountToken'] = token_exchange
        self.load_tokens()


config = EspnPlusConfig()

app_config = util.get_url_as_json_cache(BAM_APP_CONFIG, timeout=3600)


# disney

def url_for_provider(url, provider):
    return url.replace('{id-provider}', provider)


def get_api_key(provider):
    logger.debug('Getting API Key')
    resp = global_session.post(url_for_provider(API_KEY_URL, provider))
    return resp.headers.get('api-key')


def have_valid_login_id_token():
    return config.disney_id_token is not None and config.disney_id_token.is_valid()


def handle_license_plate_token(token):
    config.set_disney_token(token)
    config.set_disney_id_token(token['id_token'])


def get_login_id_token(username, password, provider):
    if config.disney_id_token is None or not config.disney_id_token.is_valid():
        logger.debug('Getting ID Token')
        resp = global_session.post(url_for_provider(LOGIN_URL, provider), headers={
            'Authorization': 'APIKEY %s' % get_api_key(provider)
        }, json={
            'loginValue': username,
            'password': password
        })
        config.set_disney_id_token(resp.json()['data']['token']['id_token'])
    return config.disney_id_token.token


def has_valid_login_id_token():
    return config.disney_id_token is not None and config.disney_id_token.is_valid()


def has_valid_disney_refresh_token():
    return config.disney_token is not None and config.disney_token.is_refresh_token_valid()


def get_license_plate(provider):
    logger.debug('Getting license plate')
    post_data = {
        'content': {
            'adId': uuid.uuid1().hex,
            'correlation-id': uuid.uuid1().hex,
            'deviceId': uuid.uuid1().hex,
            'deviceType': 'ANDTV',
            'entitlementPath': 'login',
            'entitlements': [],
        },
        'ttl': 0
    }
    resp = global_session.post(url_for_provider(LICENSE_PLATE_URL, provider), headers={
        'Authorization': 'APIKEY %s' % get_api_key(provider),
        'Content-Type': 'application/json',
    }, json=post_data)
    return post_data, resp.json()


def perform_license_plate_auth_flow(semaphore, result_queue):
    license_post_data, license_resp = get_license_plate(ANDROID_ID)
    pairing_code = license_resp['data']['pairingCode']
    logger.debug('Pairing code: %s' % pairing_code)

    fastcast_host = license_resp['data']['fastCastHost']
    fastcast_profile_id = license_resp['data']['fastCastProfileId']
    fastcast_topic = license_resp['data']['fastCastTopic']

    # Obtain websocket info from fastcast
    resp = global_session.get(fastcast_host + '/public/websockethost')
    websocket_info = resp.json()

    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp("wss://%s:%s/FastcastService/pubsub/profiles/%s?TrafficManager-Token=%s" %
                                (websocket_info['ip'], websocket_info['securePort'],
                                 fastcast_profile_id, websocket_info['token']),
                                on_message=create_on_message(fastcast_topic, result_queue),
                                on_error=on_error,
                                on_close=create_on_close(semaphore))
    ws.on_open = on_open

    return pairing_code, ws


def refresh_auth(provider):
    logger.debug('Refreshing auth')
    post_data = {
        'refreshToken': config.disney_token.refresh_token
    }
    resp = global_session.post(url_for_provider(REFRESH_AUTH_URL, provider), headers={
        'Content-Type': 'application/json',
    }, json=post_data)
    config.set_disney_id_token(resp.json()['data']['token']['id_token'])


def start_websocket_thread(ws):
    thread.start_new_thread(ws.run_forever, ())


# websocket
def create_on_message(fastcast_topic, result_queue):
    def on_message(ws, message):
        message_json = json.loads(message)
        if 'op' in message_json:
            op = message_json['op']
            if op == 'C':
                ret = {
                    'op': 'S',
                    'sid': message_json['sid'],
                    'tc': fastcast_topic,
                    'rc': 200
                }
                ws.send(json.dumps(ret))
            elif op == 'P':
                token = json.loads(message_json['pl'])
                result_queue.put(token)
                ws.close()

    return on_message


def on_error(ws, error):
    logger.debug(error)


def create_on_close(semaphore):
    def on_close(ws):
        logger.debug('Closed websocket')
        semaphore.release()

    return on_close


def on_open(ws):
    logger.debug('Opened websocket')
    ws.send(json.dumps({
        'op': 'C'
    }))


# bam

def fill_in_template(template, access_token):
    return template.replace('{apiKey}', BAM_API_KEY) \
        .replace('{accessToken}', access_token)


def execute_method(endpoint, access_token='', json_body=None, data=None):
    logger.debug('Executing endpoint %s' % endpoint['href'])
    http_headers = {}
    for i, (header, value) in enumerate(endpoint['headers'].items()):
        http_headers[header] = fill_in_template(value, access_token)
    resp = None
    if endpoint['method'] == 'POST':
        resp = global_session.post(endpoint['href'], headers=http_headers, json=json_body, data=data)
    elif endpoint['method'] == 'GET':
        resp = global_session.get(endpoint['href'], headers=http_headers)
    return resp


def create_device_grant():
    endpoint = app_config['services']['device']['client']['endpoints']['createDeviceGrant']
    resp = execute_method(endpoint, json_body={
        'deviceFamily': 'browser',
        'applicationRuntime': 'chrome',
        'deviceProfile': 'linux',
        'attributes': {}
    })
    if resp is not None:
        config.set_device_grant(resp.json())


def get_device_assertion():
    if config.device_grant is None or not config.device_grant.is_valid():
        create_device_grant()
    return config.device_grant.assertion


def exchange_token(data):
    endpoint = app_config['services']['token']['client']['endpoints']['exchange']
    resp = execute_method(endpoint, data=data)
    return resp.json()


def create_account_grant(access_token, json_body):
    endpoint = app_config['services']['account']['client']['endpoints']['createAccountGrant']
    resp = execute_method(endpoint, access_token=access_token, json_body=json_body)
    return resp.json()


def get_subscriptions(access_token):
    endpoint = app_config['services']['subscription']['client']['endpoints']['getSubscriptions']
    resp = execute_method(endpoint, access_token=access_token)
    return resp.json()


def get_account_details(access_token):
    endpoint = app_config['services']['account']['client']['endpoints']['getCurrentAccount']
    resp = execute_method(endpoint, access_token=access_token)
    return resp.json()


def get_device_token_exchange():
    if config.device_token_exchange is None or not config.device_token_exchange.is_refresh_token_valid():
        logger.debug('Getting Device Token Exchange')
        device_assertion = get_device_assertion()
        token_exchange = exchange_token(data={
            'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
            'latitude': 0,
            'longitude': 0,
            'platform': 'browser',
            'setCookie': False,
            'subject_token': device_assertion,
            'subject_token_type': 'urn:bamtech:params:oauth:token-type:device'
        })
        config.set_device_token_exchange(token_exchange)
    return config.device_token_exchange.refresh_token


def get_device_refresh_token():
    if config.device_refresh_token is None or not config.device_refresh_token.is_access_token_valid():
        logger.debug('Getting Device Refresh Token')
        device_token_exchange_refresh = get_device_token_exchange()
        token_exchange = exchange_token(data={
            'grant_type': 'refresh_token',
            'latitude': 0,
            'longitude': 0,
            'platform': 'browser',
            'setCookie': False,
            'refresh_token': device_token_exchange_refresh,
        })
        config.set_device_refresh_token(token_exchange)
    return config.device_refresh_token.access_token


def request_bam_account_access_token():
    if config.id_token_grant is None or not config.id_token_grant.is_valid():
        logger.debug('Getting Token Grant')
        device_token = get_device_refresh_token()
        grant_resp = create_account_grant(access_token=device_token, json_body={
            'id_token': config.disney_id_token.token
        })
        config.set_id_token_grant(grant_resp)

    account_token = exchange_token(data={
        'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
        'latitude': 0,
        'longitude': 0,
        'platform': 'browser',
        'setCookie': False,
        'subject_token': config.id_token_grant.assertion,
        'subject_token_type': 'urn:bamtech:params:oauth:token-type:account'
    })
    config.set_account_token(account_token)
    config.set_subscriptions(get_bam_sub_details())


def has_valid_bam_account_access_token():
    return config.account_token is not None and config.account_token.is_access_token_within_grace_period()


def get_bam_account_access_token():
    return config.account_token.access_token


def get_bam_sub_details():
    if config.get_subscriptions() is None:
        if not has_valid_bam_account_access_token() and has_valid_login_id_token():
            request_bam_account_access_token()
        elif not has_valid_bam_account_access_token():
            return []
        config.set_subscriptions(get_subscriptions(config.account_token.access_token))
    return config.get_subscriptions()


def get_bam_account_details():
    return get_account_details(config.account_token.access_token)


def get_entitlements():
    sub_details = get_bam_sub_details()
    entitlements = []
    for sub in sub_details:
        if sub['isActive']:
            for product in sub['products']:
                for entitlement in product['productEntitlements']:
                    entitlements.append(entitlement['name'])
    return entitlements


def can_we_access_without_prompt():
    if has_valid_bam_account_access_token():
        return True
    if has_valid_login_id_token():
        return True
    if has_valid_disney_refresh_token():
        return True
    return False


def ensure_valid_access_token():
    if has_valid_bam_account_access_token():
        return
    if has_valid_login_id_token():
        request_bam_account_access_token()
        return
    if has_valid_disney_refresh_token():
        refresh_auth(ANDROID_ID)
        request_bam_account_access_token()
