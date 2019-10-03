# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import json
import urllib2

import m3u8
from xbmcplugin import setResolvedUrl, endOfDirectory

import adobe_activate_api
import auth_routes
import espnplus
from globals import global_session
from plugin_routing import *
from resources.lib.addon_util import *
from resources.lib.globals import UA_PC
from resources.lib.kodiutils import set_setting, get_setting_as_int, get_setting


def get_token_type(auth_types):
    if requires_adobe_auth(auth_types):
        return 'ADOBEPASS'
    elif 'direct' in auth_types:
        return 'ESPN+'
    return 'DEVICE'

def check_auth_status(auth_types, resource, network_name):
    logging.debug('Checking auth of %s' % (auth_types))

    if requires_adobe_auth(auth_types):
        # Adobe auth
        if not adobe_activate_api.is_authenticated():
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(get_string(30038), get_string(30050),
                               yeslabel=get_string(30051),
                               nolabel=get_string(30360))
            if ret:
                authed = auth_routes.login_tv_provider()
                if not authed:
                    return None
            else:
                return None
        try:
            # testing code raise urllib2.HTTPError(url='test', code=403, msg='no', hdrs=dict(), fp=None)
            logging.debug('getting media token for resource %s' % resource)
            return adobe_activate_api.get_short_media_token(resource)
        except urllib2.HTTPError as http_exception:
            logging.debug('error getting media token %s' % http_exception)
            if http_exception.code == 410 or http_exception.code == 404 or http_exception.code == 401:
                dialog = xbmcgui.Dialog()
                dialog.ok(get_string(30037), get_string(30840))
                adobe_activate_api.deauthorize()
                return None
            elif http_exception.code == 403:
                # Check for blackout
                dialog = xbmcgui.Dialog()
                ok = dialog.yesno(get_string(30037), get_string(30900))
                if ok:
                    setting = get_setting_from_channel(network_name)
                    if setting is not None:
                        set_setting(setting, False)
                return None
            else:
                return None
        except adobe_activate_api.AuthorizationException as exception:
            logging.debug('Error authorizating media token %s' % exception)
            dialog = xbmcgui.Dialog()
            dialog.ok(get_string(30037), get_string(30840))
            adobe_activate_api.deauthorize()
            return None
    elif 'direct' in auth_types:
        # bam authentication
        if not espnplus.can_we_access_without_prompt():
            logging.debug('Invalid token')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno(get_string(30038), get_string(30060),
                               yeslabel=get_string(30061),
                               nolabel=get_string(30360))
            if ret:
                authed = auth_routes.login_espn_plus()
                if not authed:
                    return None
            else:
                return None
        espnplus.ensure_valid_access_token()

        return espnplus.get_bam_account_access_token()

    elif 'isp' in auth_types:
        return adobe_activate_api.get_device_id()
    logging.error('Unable to handle auth types')
    return None

def process_playback_url(playback_url, auth_string):
    logging.debug('Playback url %s' % playback_url)
    stream_quality =  str(get_setting('StreamQuality'))
    bitrate_limit = int(get_setting('BitrateLimit'))
    logging.debug('Stream Quality %s' % stream_quality)
    try:
        m3u8_obj = m3u8.load(playback_url)
    except Exception as e:
        logging.error('Unable to load m3u8 %s' % e)
        playback_url += '|' + auth_string
        item = xbmcgui.ListItem(path=playback_url)
        return setResolvedUrl(plugin.handle, True, item)

    success = True

    use_inputstream_addon = not get_setting_as_bool('DisableInputStream')

    if not use_inputstream_addon:
        if m3u8_obj.is_variant:
            stream_options = list()
            bandwidth_key = 'bandwidth'
            m3u8_obj.playlists.sort(key=lambda playlist: playlist.stream_info.bandwidth, reverse=True)
            m3u8_obj.data['playlists'].sort(key=lambda playlist: int(playlist['stream_info'][bandwidth_key]),
                                            reverse=True)
            stream_quality_index = str(get_setting('StreamQualityIndex'))
            stream_index = None
            should_ask = False
            try:
                stream_index = int(stream_quality_index)
                if stream_index < 0 or stream_index >= len(m3u8_obj.playlists):
                    should_ask = True
            except:
                should_ask = True
            if '0' == stream_quality:  # Best
                stream_index = 0
                should_ask = False
                for playlist in m3u8_obj.data['playlists']:
                    stream_info = playlist['stream_info']
                    bandwidth = int(stream_info[bandwidth_key]) / 1024
                    if bandwidth <= bitrate_limit:
                        break
                    stream_index += 1
            elif '2' == stream_quality:  # Ask everytime
                should_ask = True
            if should_ask:
                for playlist in m3u8_obj.data['playlists']:
                    stream_info = playlist['stream_info']
                    resolution = stream_info['resolution']
                    frame_rate = stream_info['frame_rate'] if 'frame_rate' in stream_info else 30.0
                    bandwidth = int(stream_info[bandwidth_key]) / 1024
                    if 'average_bandwidth' in stream_info:
                        logging.debug('bandwidth: %s average bandwidth: %s' %
                                      (stream_info['bandwidth'], stream_info['average_bandwidth']))
                    stream_options.append(get_string(30450) % (resolution, frame_rate, bandwidth))
                dialog = xbmcgui.Dialog()
                stream_index = dialog.select(get_string(30440), stream_options)
                if stream_index < 0:
                    success = False
                else:
                    set_setting('StreamQualityIndex', value=str(stream_index))

            uri = m3u8_obj.playlists[stream_index].uri
            logging.debug('Chose stream %d; %s' % (stream_index, uri))
            if 'http' not in uri[0:4]:
                index_of_last_slash = playback_url.rfind('/')
                uri = playback_url[0:index_of_last_slash] + '/' + uri
            item = xbmcgui.ListItem(path=uri + '|' + auth_string)
            setResolvedUrl(plugin.handle, success, item)
        else:
            item = xbmcgui.ListItem(path=playback_url)
            setResolvedUrl(plugin.handle, success, item)
    else:
        xbmc.log(TAG + 'Using inputstream.hls addon', xbmc.LOGDEBUG)
        item = xbmcgui.ListItem(path=playback_url)
        item.setProperty('inputstreamaddon', 'inputstream.hls')
        item.setProperty('inputstream.hls.manifest_type', 'hls')
        setResolvedUrl(plugin.handle, success, item)


def start_adobe_session(media_token, token_type, resource, start_session_url):
    params = urllib.urlencode({'partner': 'watchespn',
                               'playbackScenario': 'HTTP_CLOUD_HIGH',
                               'platform': 'chromecast_uplynk',
                               'token': media_token,
                               'tokenType': token_type,
                               'resource': base64.b64encode(resource),
                               'v': '2.0.0'
                               })
    authed_url = start_session_url + '&' + params

    xbmc.log('ESPN3: start_session_url: ' + authed_url, xbmc.LOGDEBUG)


    try:
        session_json = util.get_url_as_json(authed_url)
    except urllib2.HTTPError as exception:
        if exception.code == 403:
            session_json = json.load(exception)
            logging.debug('checking for errors in %s' % session_json)
        else:
            raise exception

    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    auth_string = 'Connection=keep-alive&User-Agent=' + urllib.quote(UA_PC) + '&Cookie=_mediaAuth=' + \
                        urllib.quote(session_json['session']['token'])
    process_playback_url(playback_url, auth_string=auth_string)

def start_espn_plus_session(start_session_url):
    espnplus_url = start_session_url.replace('{scenario}', 'browser~ssai')

    xbmc.log('ESPN+ URL %s' % espnplus_url, xbmc.LOGDEBUG)

    try:
        session_json = global_session.get(espnplus_url, headers={
            'Authorization': espnplus.get_bam_account_access_token(),
            'Accept': 'application/vnd.media-service+json; version=2'
        }).json()
    except urllib2.HTTPError as exception:
        logging.debug('Unable to get session %s' % exception)
        if exception.code == 403:
            session_json = json.load(exception)
            xbmc.log(TAG + 'checking for errors in %s' % session_json)
        else:
            raise exception

    logging.debug('Session JSON %s' % session_json)
    if check_espn_plus_error(session_json):
        return
    if 'slide' in session_json['stream']:
        playback_url = session_json['stream']['slide']
    else:
        playback_url = session_json['stream']['complete']

    auth_string = 'Authorization=' + espnplus.get_bam_account_access_token()
    process_playback_url(playback_url, auth_string=auth_string)

def start_session(media_token, token_type, resource, start_session_url):
    if token_type == 'ADOBEPASS' or token_type == 'DEVICE':
        start_adobe_session(media_token, token_type, resource, start_session_url)
    else:
        start_espn_plus_session(start_session_url)

@plugin.route('/play-item/<event_id>')
def play_item(event_id):
    url = arg_as_string('url')
    item = xbmcgui.ListItem(path=url)
    return setResolvedUrl(plugin.handle, True, item)

@plugin.route('/play-vod/<event_id>')
def play_vod(event_id):
    url = arg_as_string('url')
    session_json = util.get_url_as_json(url)
    playback_url = session_json['playbackState']['videoHref']

    process_playback_url(playback_url, '')

# Used for V3 Page api play requests
@plugin.route('/play-event/<event_id>')
def play_event(event_id):
    event_url = arg_as_string('event_url')
    auth_types = arg_as_list('auth_types')

    session_json = util.get_url_as_json(event_url)
    resource = session_json['adobeRSS']
    network_name = session_json['tracking']['network']

    logging.debug('Checking current auth of %s' % auth_types)
    media_token = check_auth_status(auth_types, resource, network_name)
    token_type = get_token_type(auth_types)

    if token_type is None or media_token is None:
        endOfDirectory(plugin.handle, succeeded=False, updateListing=True)
    else:
        start_session_url = session_json['playbackState']['videoHref']
        start_session(media_token, token_type, resource, start_session_url)


# Cookie is only needed when authenticating with espn broadband as opposed to uplynk
#ua UA_PC
#finalurl = finalurl + '|Connection=keep-alive&User-Agent=' + urllib.quote(ua) + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
# Legacy uses this to play items
@plugin.route('/play-tv/<event_id>')
def play_tv(event_id):
    resource = arg_as_string('resource')
    network_name = arg_as_string('network_name')

    auth_types = get_auth_types_from_network(network_name)
    media_token = check_auth_status(auth_types, resource, network_name)
    if media_token is None:
        return
    token_type = get_token_type(auth_types)

    # see aHR0cDovL2FwaS1hcHAuZXNwbi5jb20vdjEvd2F0Y2gvY2xpZW50cy93YXRjaGVzcG4tdHZvcw== for details
    # see aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2ZlYXR1cmVk for details
    start_session_url = arg_as_string('session_url')

    start_session(media_token, token_type, resource, start_session_url)

@plugin.route('/upcoming-event/<event_id>')
def upcoming_event(event_id):
    starttime = arg_as_string('starttime')
    event_name = urllib.unquote_plus(arg_as_string('event_name'))
    packages = arg_as_list('packages')
    entitlements = espnplus.get_entitlements()
    logging.debug('Upcoming event chosen for %s, %s, %s' % (starttime, packages, entitlements))
    has_entitlement = is_entitled(packages, entitlements)
    logging.debug('Entitled for content? %s' % has_entitlement)
    extra = ''
    if not has_entitlement:
        extra = get_string(40270) % (', '.join(packages))
    dialog = xbmcgui.Dialog()
    dialog.ok(get_string(30035), get_string(30036) % (event_name, starttime, extra))
    endOfDirectory(plugin.handle, succeeded=False, updateListing=True)

