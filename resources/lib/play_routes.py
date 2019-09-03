import json
import logging
import urllib2

import m3u8
from xbmcplugin import setResolvedUrl

from plugin_routing import *
from resources.lib.addon_util import *
from resources.lib.globals import UA_PC
import adobe_activate_api

@plugin.route('/play-item')
def PLAY_ITEM(args):
    url = args.get(PLAYBACK_URL)[0]
    item = xbmcgui.ListItem(path=url)
    return setResolvedUrl(plugin.handle, True, item)

# Cookie is only needed when authenticating with espn broadband as opposed to uplynk
#ua UA_PC
#finalurl = finalurl + '|Connection=keep-alive&User-Agent=' + urllib.quote(ua) + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
@plugin.route('/play-tv/<event_id>')
def PLAY_TV(event_id):
    resource = arg_as_string('resource')
    network_name = arg_as_string('network_name')

    requires_auth = does_requires_auth(network_name)
    if not requires_auth:
        logging.debug(TAG + ' Forcing auth')
        requires_auth = adobe_activate_api.is_authenticated()

    if requires_auth:
        if not adobe_activate_api.is_authenticated():
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30037), translation(30410))
            return
        try:
            # testing code raise urllib2.HTTPError(url='test', code=403, msg='no', hdrs=dict(), fp=None)
            xbmc.log(TAG + ' getting media token for resource %s' % resource, xbmc.LOGDEBUG)
            media_token = adobe_activate_api.get_short_media_token(resource)
        except urllib2.HTTPError as http_exception:
            xbmc.log(TAG + ' error getting media token %s' % http_exception, xbmc.LOGDEBUG)
            if http_exception.code == 410 or http_exception.code == 404 or http_exception.code == 401:
                dialog = xbmcgui.Dialog()
                dialog.ok(translation(30037), translation(30840))
                adobe_activate_api.deauthorize()
                xbmcplugin.endOfDirectory(plugin.handle, succeeded=False, updateListing=True)
                return
            elif http_exception.code == 403:
                # Check for blackout
                dialog = xbmcgui.Dialog()
                ok = dialog.yesno(translation(30037), translation(30900))
                if ok:
                    setting = get_setting_from_channel(network_name)
                    if setting is not None:
                        selfAddon.setSetting(setting, 'false')
                return
            else:
                raise http_exception
        except adobe_activate_api.AuthorizationException as exception:
            xbmc.log(TAG + ' Error authorizating media token %s' % exception, xbmc.LOGDEBUG)
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30037), translation(30840))
            adobe_activate_api.deauthorize()
            xbmcplugin.endOfDirectory(plugin.handle, succeeded=False, updateListing=True)
            return

        token_type = 'ADOBEPASS'
    else:
        media_token = adobe_activate_api.get_device_id()
        token_type = 'DEVICE'


    # see aHR0cDovL2FwaS1hcHAuZXNwbi5jb20vdjEvd2F0Y2gvY2xpZW50cy93YXRjaGVzcG4tdHZvcw== for details
    # see aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2ZlYXR1cmVk for details
    start_session_url = arg_as_string('session_url')
    params = urllib.urlencode({'partner':'watchespn',
                               'playbackScenario':'HTTP_CLOUD_HIGH',
                               'platform':'chromecast_uplynk',
                               'token':media_token,
                               'tokenType':token_type,
                               'resource':base64.b64encode(resource),
                               'v': '2.0.0'
                               })
    start_session_url += '&' + params

    xbmc.log('ESPN3: start_session_url: ' + start_session_url, xbmc.LOGDEBUG)

    try:
        session_json = util.get_url_as_json(start_session_url)
    except urllib2.HTTPError as exception:
        if exception.code == 403:
            session_json = json.load(exception)
            xbmc.log(TAG + 'checking for errors in %s' % session_json)
        else:
            raise exception

    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    logging.debug('Playback url %s' % playback_url)
    stream_quality = str(selfAddon.getSetting('StreamQuality'))
    bitrate_limit = int(selfAddon.getSetting('BitrateLimit'))
    logging.debug('Stream Quality %s' % stream_quality)
    try:
        m3u8_obj = m3u8.load(playback_url)
    except:
        playback_url += '|Connection=keep-alive&User-Agent=' + urllib.quote(UA_PC) + '&Cookie=_mediaAuth=' +\
                        urllib.quote(session_json['session']['token'])
        item = xbmcgui.ListItem(path=playback_url)
        return xbmcplugin.setResolvedUrl(plugin.handle, True, item)

    success = True

    use_inputstream_addon = selfAddon.getSetting('DisableInputStream') == 'false'

    if not use_inputstream_addon:
        if m3u8_obj.is_variant:
            stream_options = list()
            bandwidth_key = 'bandwidth'
            m3u8_obj.playlists.sort(key=lambda playlist: playlist.stream_info.bandwidth, reverse=True)
            m3u8_obj.data['playlists'].sort(key=lambda playlist: int(playlist['stream_info'][bandwidth_key]), reverse=True)
            stream_quality_index = str(selfAddon.getSetting('StreamQualityIndex'))
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
            elif '2' == stream_quality: #Ask everytime
                should_ask = True
            if should_ask:
                for playlist in m3u8_obj.data['playlists']:
                    stream_info = playlist['stream_info']
                    resolution = stream_info['resolution']
                    frame_rate = stream_info['frame_rate']
                    bandwidth = int(stream_info[bandwidth_key]) / 1024
                    if 'average_bandwidth' in stream_info:
                        logging.debug('bandwidth: %s average bandwidth: %s' %
                                 (stream_info['bandwidth'], stream_info['average_bandwidth']))
                    stream_options.append(translation(30450) % (resolution, frame_rate, bandwidth))
                dialog = xbmcgui.Dialog()
                stream_index = dialog.select(translation(30440), stream_options)
                if stream_index < 0:
                    success = False
                else:
                    selfAddon.setSetting(id='StreamQualityIndex', value=str(stream_index))

            logging.debug('Chose stream %d' % stream_index)
            item = xbmcgui.ListItem(path=m3u8_obj.playlists[stream_index].uri)
            xbmcplugin.setResolvedUrl(plugin.handle, success, item)
        else:
            item = xbmcgui.ListItem(path=playback_url)
            xbmcplugin.setResolvedUrl(plugin.handle, success, item)
    else:
        xbmc.log(TAG + 'Using inputstream.hls addon', xbmc.LOGDEBUG)
        item = xbmcgui.ListItem(path=playback_url)
        item.setProperty('inputstreamaddon', 'inputstream.hls')
        item.setProperty('inputstream.hls.manifest_type', 'hls')
        xbmcplugin.setResolvedUrl(plugin.handle, success, item)
