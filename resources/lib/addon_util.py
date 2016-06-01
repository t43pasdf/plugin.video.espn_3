import sys
import urllib
import base64
import m3u8

import xbmc
import xbmcgui
import xbmcplugin

import adobe_activate_api
import util
import player_config
from globals import defaultfanart, pluginhandle, selfAddon, translation, LOG_LEVEL
from constants import *

TAG = 'Addon_Util: '

def addLink(name, url, iconimage, fanart=None, infoLabels=None):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)

    if infoLabels is None:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    liz.setIconImage(iconimage)
    if fanart is None:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    video_streaminfo = dict()
    liz.addStreamInfo('video', video_streaminfo)
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)
    return ok


def addDir(name, url, iconimage, fanart=None, infoLabels=None):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if infoLabels is None:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if fanart is None:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)
    return ok

def check_error(session_json):
    status = session_json['status']
    if not status == 'success':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30500) % session_json['message'])
        return True
    return False

def does_requires_auth(network_name):
    requires_auth = not network_name == 'espn3'
    if network_name == 'espn3':
        free_content_check = player_config.can_access_free_content()
        if not free_content_check:
            xbmc.log('ESPN3: User needs login to ESPN3', LOG_LEVEL)
            requires_auth = True
    return requires_auth

def get_url(url):
    tz = player_config.get_timezone()
    if '?' in url:
        sep = '&'
    else:
        sep = '?'
    return url + sep + 'tz=' + urllib.quote_plus(tz)

# TODO: Unsure if cookie is needed
#ua UA_PC
#finalurl = finalurl + '|Connection=keep-alive&User-Agent=' + urllib.quote(ua) + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
def PLAY_TV(args):

    network_name = args.get(NETWORK_NAME)[0]
    event_name = args.get(EVENT_NAME)[0]
    event_guid = args.get(EVENT_GUID)[0]
    event_parental_rating = args.get(EVENT_PARENTAL_RATING)[0]
    resource = adobe_activate_api.get_resource(network_name, event_name, event_guid, event_parental_rating)

    requires_auth = does_requires_auth(network_name)

    if requires_auth:
        if not adobe_activate_api.is_authenticated():
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(30037), translation(30410))
            return
        media_token = adobe_activate_api.get_short_media_token(resource)
        token_type = 'ADOBEPASS'
    else:
        media_token = adobe_activate_api.get_device_id()
        token_type = 'DEVICE'


    # see http://api-app.espn.com/v1/watch/clients/watchespn-tvos for details
    # see http://espn.go.com/watchespn/appletv/featured for details
    start_session_url = args.get(SESSION_URL)[0]
    params = urllib.urlencode({'partner':'watchespn',
                               'playbackScenario':'HTTP_CLOUD_HIGH',
                               'platform':'tvos',
                               'token':media_token,
                               'tokenType':token_type,
                               'resource':base64.b64encode(resource),
                               'v': '2.0.0'
                               })
    start_session_url += '&' + params

    xbmc.log('ESPN3: start_session_url: ' + start_session_url, LOG_LEVEL)

    session_json = util.get_url_as_json(start_session_url)
    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    stream_quality = str(selfAddon.getSetting('StreamQuality'))
    bitrate_limit = int(selfAddon.getSetting('BitrateLimit'))
    xbmc.log(TAG + 'Stream Quality %s' % stream_quality, LOG_LEVEL)
    m3u8_obj = m3u8.load(playback_url)
    success = True
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
        if '0' == stream_quality: # Best
            stream_index = 0
            should_ask = False
            for playlist in m3u8_obj.data['playlists']:
                stream_info = playlist['stream_info']
                bandwidth = int(stream_info[bandwidth_key]) / 1024
                if bandwidth <= bitrate_limit:
                    break
                stream_index = stream_index + 1
        elif '2' == stream_quality: #Ask everytime
            should_ask = True
        if should_ask:
            for playlist in m3u8_obj.data['playlists']:
                stream_info = playlist['stream_info']
                resolution = stream_info['resolution']
                frame_rate = stream_info['frame_rate']
                bandwidth = int(stream_info[bandwidth_key]) / 1024
                if 'average_bandwidth' in stream_info:
                    xbmc.log(TAG + 'bandwidth: %s average bandwidth: %s' %
                             (stream_info['bandwidth'], stream_info['average_bandwidth']), LOG_LEVEL)
                stream_options.append(translation(30450) % (resolution,
                                                      frame_rate,
                                                      bandwidth))
            dialog = xbmcgui.Dialog()
            stream_index = dialog.select(translation(30440), stream_options)
            if stream_index < 0:
                success = False
            else:
                selfAddon.setSetting(id='StreamQualityIndex', value=str(stream_index))

        xbmc.log(TAG + 'Chose stream %d' % stream_index, LOG_LEVEL)
        item = xbmcgui.ListItem(path=m3u8_obj.playlists[stream_index].uri)
        return xbmcplugin.setResolvedUrl(pluginhandle, success, item)
    else:
        item = xbmcgui.ListItem(path=finalurl)
        return xbmcplugin.setResolvedUrl(pluginhandle, success, item)
