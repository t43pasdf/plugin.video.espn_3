import base64
import re
import sys
import time
import urllib

import xbmc
import xbmcgui
import xbmcplugin
from xbmcgui import ListItem

import player_config
import util
from constants import *
from globals import defaultfanart, selfAddon, translation
from resources.lib.kodiutils import get_setting_as_bool

TAG = 'Addon_Util: '


def addLink(name, url, iconimage="DefaultVideo.png", fanart=defaultfanart, infoLabels=None):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name)

    if infoLabels is None:
        infoLabels={'Title': name}

    liz.setInfo('video', infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    addon_art = {
        'fanart': fanart,
        'thumb': iconimage,
        'icon': iconimage
    }
    liz.setArt(addon_art)
    video_streaminfo = dict()
    liz.addStreamInfo('video', video_streaminfo)
    ok = xbmcplugin.addDirectoryItem(handle=plugin.handle, url=u, listitem=liz)
    return ok


def addDir(name, url, iconimage="DefaultFolder.png", fanart=defaultfanart, infoLabels=None):
    liz = xbmcgui.ListItem(name)
    if infoLabels is None:
        infoLabels={'Title': name}

    liz.setInfo('video', infoLabels=infoLabels)
    addon_art = {
        'fanart': fanart,
        'thumb': iconimage,
        'icon': iconimage
    }
    liz.setArt(addon_art)
    ok = xbmcplugin.addDirectoryItem(handle=plugin.handle, url=url, listitem=liz, isFolder=True)
    return ok

def check_error(session_json):
    status = session_json['status']
    if not status == 'success':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30500) % session_json['message'])
        return True
    return False

def does_requires_auth(network_name):
    xbmc.log(TAG + 'Checking auth of ' + network_name, xbmc.LOGDEBUG)
    requires_auth = not (network_name == 'espn3' or network_name == 'accextra' or network_name.find('free') >= 0 or network_name == '')
    if not requires_auth:
        free_content_check = player_config.can_access_free_content()
        if not free_content_check:
            xbmc.log('ESPN3: User needs login to ESPN3', xbmc.LOGDEBUG)
            requires_auth = True
    return requires_auth

def get_url(url):
    if 'listingsUrl' not in url and 'tz' not in url:
        tz = player_config.get_timezone()
        if '?' in url:
            sep = '&'
        else:
            sep = '?'
        return url + sep + 'tz=' + urllib.quote_plus(tz)
    return url

def get_setting_from_channel(channel):
    for setting in CHANNEL_SETTINGS:
        if CHANNEL_SETTINGS[setting] == channel:
            return setting
    return None

def include_item(networkId):
    for setting in CHANNEL_SETTINGS:
        channel = CHANNEL_SETTINGS[setting]
        if channel == networkId:
            return selfAddon.getSetting(setting) == 'true'
    return True


def get_league(listing):
    if 'categories' in listing:
        for category in listing['categories']:
            if 'type' in category and category['type'] == 'league':
                return category['description']
    return ''


def get_subcategory(listing):
    if 'subcategories' in listing:
        for subcategory in listing['subcategories']:
            return subcategory['name']
    return ''


def check_json_blackout(listing):
    blackout_dmas = list()
    for blackout in listing['blackouts']:
        if blackout['type'] == 'dma':
            for dma in blackout['detail']:
                blackout_dmas.append(dma)
    user_dma = player_config.get_dma()
    for blackout_dma in blackout_dmas:
        if blackout_dma == user_dma:
            return True
    return False

def check_event_blackout(event_id):
    xbmc.log(TAG + ' Checking blackout for ' + event_id, xbmc.LOGDEBUG)
    url = base64.b64decode(
        'aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi91dGlsL2lzVXNlckJsYWNrZWRPdXQ/ZXZlbnRJZD0=') + event_id
    xbmc.log(TAG + 'Blackout url %s' % url, xbmc.LOGDEBUG)
    blackout_data = util.get_url_as_json_cache(url)
    blackout = blackout_data['E3BlackOut']
    if not blackout == 'true':
        blackout = blackout_data['LinearBlackOut']
    return blackout == 'true'

def compare(lstart, lnetwork, lstatus, rstart, rnetwork, rstatus):
    xbmc.log(TAG + 'lstart %s lnetwork %s lstatus %s rstart %s rnetwork %s rstatus %s' %
             (lstart, lnetwork, lstatus, rstart, rnetwork, rstatus), xbmc.LOGDEBUG)
    if lnetwork != rnetwork:
        return 0
    if lstart is None and rstart is None:
        return 0
    if lstart is None:
        return 1
    if rstart is None:
        return -1
    ltime = int(time.mktime(lstart))
    rtime = int(time.mktime(rstart))
    if 'replay' in lstatus and 'replay' in rstatus:
        return int(rtime - ltime)
    if lstatus == rstatus:
        return int(ltime - rtime)
    elif lstatus == 'live':
        return -1
    elif rstatus == 'live':
        return 1
    return int(rtime - ltime)

def make_list_item(label, icon=None, infoLabels=None):
    if get_setting_as_bool('NoColors'):
        label = re.sub(r'\[COLOR=\w{8}\]', '', label)
        label = re.sub(r'\[/COLOR\]', '', label)
    listitem = ListItem(label, iconImage=icon)
    listitem.setInfo('video', infoLabels=infoLabels)
    listitem.setProperty('IsPlayable', 'true')
    return listitem
