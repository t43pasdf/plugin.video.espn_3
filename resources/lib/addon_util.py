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
