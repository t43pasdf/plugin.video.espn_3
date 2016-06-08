import sys
import urllib
import base64
import m3u8
import time

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
    xbmc.log(TAG + 'Made url to %s' % u, LOG_LEVEL)
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
    if 'listingsUrl' not in url and 'tz' not in url:
        tz = player_config.get_timezone()
        if '?' in url:
            sep = '&'
        else:
            sep = '?'
        return url + sep + 'tz=' + urllib.quote_plus(tz)
    return url

def index_item(args):
    sport = args['sport']
    ename = args['eventName']
    sport2 = args['subcategory'] if 'subcategory' in args else sport
    if sport <> sport2:
        sport += ' (' + sport2 + ')'
    starttime = args['starttime'] if 'starttime' in args else None
    length = int(args['duration'])
    xbmc.log(TAG + 'startime %s' % starttime, LOG_LEVEL)

    if starttime is not None:
        now = time.time()
        etime = time.strftime("%I:%M %p", starttime)
        if args['type'] == 'replay':
            etime_local = starttime
            if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
                etime = time.strftime("%m/%d/%Y", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
        elif args['type'] == 'live':
            starttime_time = time.mktime(starttime)
            length  -= (time.time() - starttime_time)
            ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
        else:
            now_time = time.localtime(now)
            if now_time.tm_year == starttime.tm_year and \
                            now_time.tm_mon == starttime.tm_mon and \
                            now_time.tm_mday == starttime.tm_mday:
                etime = time.strftime("%I:%M %p", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
        aired = time.strftime("%Y-%m-%d", starttime)
    else:
        aired = 0

    network_id = args['networkId'] if 'networkId' in args else ''
    if network_id == 'longhorn':
        channel_color = 'BF5700'
    elif network_id == 'sec' or network_id == 'secplus':
        channel_color = '004C8D'
    else:
        channel_color = 'CC0000'
    if 'networkName' in args:
        network = args['networkName']
    else:
        network = network_id
        network = network.replace('espn', translation(30590))
        network = network.replace('sec', translation(30600))
        network = network.replace('longhorn', translation(30610))
    blackout = args['blackout'] if 'blackout' in args else False
    blackout_text = ''
    if blackout:
        blackout_text = translation(30580)
    ename = '[COLOR=FF%s]%s[/COLOR] %s %s' % (channel_color, network, blackout_text, ename)

    description = args['description']
    requires_auth = does_requires_auth(network_id)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = '*' + ename

    mpaa = args['parentalRating'] if 'parentRating' in args else 'U'
    infoLabels = {'title': ename,
                  'genre': sport,
                  'duration': length,
                  'studio': network,
                  'mpaa': mpaa,
                  'plot': description,
                  'aired': aired,
                  'premiered': aired}

    authurl = dict()
    if args['type'] == 'upcoming':
        authurl[MODE] = UPCOMING_MODE
    else:
        if 'adobeRSS' not in args and 'guid' not in args:
            authurl[PLAYBACK_URL] = args['sessionUrl']
            authurl[MODE] = PLAY_ITEM_MODE
        else:
            authurl[MODE] = PLAY_TV_MODE
            authurl[EVENT_ID] = args['eventId']
            authurl[SESSION_URL] = args['sessionUrl']
            authurl[NETWORK_NAME] = args['networkId']
            if 'adobeRSS' in args:
                authurl[ADOBE_RSS] = args['adobeRSS'].encode('iso-8859-1')
            else:
                authurl[EVENT_NAME] = args['eventName'].encode('iso-8859-1')
                authurl[EVENT_GUID] = args['guid'].encode('iso-8859-1')
                authurl[EVENT_PARENTAL_RATING] = mpaa
    fanart = args['imageHref']
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)