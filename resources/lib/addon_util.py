# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import base64
import re
import time
import urllib

import xbmc
import xbmcgui
from xbmcgui import ListItem

import player_config
import util
from constants import *
from resources.lib.kodiutils import get_setting_as_bool, get_string
import logging

TAG = 'Addon_Util: '

def check_error(session_json):
    status = session_json['status']
    if not status == 'success':
        dialog = xbmcgui.Dialog()
        dialog.ok(get_string(30037), get_string(30500) % session_json['message'])
        return True
    return False

def check_espn_plus_error(session_json):
    if 'errors' in session_json:
        error_msg = ''
        for error in session_json['errors']:
            error_msg = error_msg + error['description'] + ' '
        dialog = xbmcgui.Dialog()
        dialog.ok(get_string(30037), get_string(30500) % error_msg)
        return True

def is_entitled(packages, entitlements):
    has_entitlement = packages is None or len(packages) == 0
    if packages is not None:
        for entitlement in entitlements:
            logging.debug('%s in %s ? %s' % (entitlement, packages, entitlement in packages))
            has_entitlement = has_entitlement or (entitlement in packages)
    return has_entitlement

def get_auth_types_from_network(network_name):
    logging.debug('Checking auth of ' + network_name)
    requires_auth = not (network_name == 'espn3' or network_name == 'accextra' or network_name.find('free') >= 0 or network_name == '')
    if requires_auth:
        return ['mvpd']
    return ['isp']

def requires_adobe_auth(auth_types):
    if 'mvpd' in auth_types:
        return True
    if 'isp' in auth_types:
        return player_config.can_access_free_content()
    return False

def check_auth_types(auth_types):
    if 'mvpd' in auth_types or 'direct' in auth_types:
        return True
    if 'isp' in auth_types:
        return player_config.can_access_free_content()
    return False


def get_url(url):
    if 'listingsUrl' not in url and 'tz' not in url:
        tz = player_config.get_timezone()
        if tz is None or tz == '':
            tz = 'America/New_York'
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
            return get_setting_as_bool(setting)
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
    logging.debug(' Checking blackout for ' + event_id)
    url = 'http://broadband.espn.go.com/espn3/auth/watchespn/util/isUserBlackedOut?eventId=%s' % event_id
    logging.debug('Blackout url %s' % url)
    blackout_data = util.get_url_as_json_cache(url)
    blackout = blackout_data['E3BlackOut']
    if not blackout == 'true':
        blackout = blackout_data['LinearBlackOut']
    return blackout == 'true'

def compare(lstart, lnetwork, lstatus, rstart, rnetwork, rstatus):
    # xbmc.log(TAG + 'lstart %s lnetwork %s lstatus %s rstart %s rnetwork %s rstatus %s' %
    #          (lstart, lnetwork, lstatus, rstart, rnetwork, rstatus), xbmc.LOGDEBUG)
    # Prefer live content
    #  sorted by network
    # Prefer upcoming content
    # sorted by time
    if lstatus == 'live' and rstatus != 'live':
        return -1
    if rstatus == 'live' and lstatus != 'live':
        return 1
    if lstatus == 'live' and rstatus == 'live':
        if lnetwork < rnetwork:
            return -1
        if rnetwork < lnetwork:
            return 1
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
