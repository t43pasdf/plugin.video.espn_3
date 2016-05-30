#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import base64
import json
import re
import time
import urllib
import urlparse
from datetime import datetime, timedelta

import m3u8

import xbmcgui
import xbmcplugin

from resources.lib import util
from resources.lib import player_config
from resources.lib import adobe_activate_api
from resources.lib.globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL
from resources.lib.constants import *
from resources.lib.addon_util import *

from resources.lib import legacy

TAG = 'ESPN3: '

def get_url(url):
    tz = player_config.get_timezone()
    if '?' in url:
        sep = '&'
    else:
        sep = '?'
    return url + sep + 'tz=' + urllib.quote_plus(tz)

def CATEGORIES_ATV(refresh = False):
    if not adobe_activate_api.is_authenticated():
        addDir('[COLOR=FFFF0000]' + translation(30300) + '[/COLOR]',
               dict(MODE=AUTHENTICATE_MODE),
               defaultreplay)
    et = util.get_url_as_xml_soup_cache(get_url('http://espn.go.com/watchespn/appletv/featured'))
    for showcase in et.findall('.//showcase/items/showcasePoster'):
        name = showcase.get('accessibilityLabel')
        image = showcase.find('./image').get('src')
        url = util.parse_url_from_method(showcase.get('onPlay'))
        addDir(name,
               dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
               image, image)
    collections = et.findall('.//collectionDivider')
    shelfs = et.findall('.//shelf')
    for i in range(0, len(collections)):
        collection_divider = collections[i]
        shelf = shelfs[i]
        title = collection_divider.find('title').text
        name = shelf.get('id')
        addDir(title,
               dict(SHELF_ID=name, MODE=CATEGORY_SHELF_MODE),
               defaultlive)
    addDir(translation(30550),
           dict(MODE=CATEGORY_SPORTS_MODE),
           defaultlive)
    addDir(translation(30560),
           dict(MODE=CATEGORY_CHANNELS_MODE),
           defaultlive)
    if selfAddon.getSetting('ShowLegacyMenu') == 'true':
        addDir('[COLOR=FF0000FF]' + translation(30510) + '[/COLOR]',
               dict(MODE=OLD_LISTING_MODE),
               defaultfanart)
    if adobe_activate_api.is_authenticated():
        addDir('[COLOR=FF00FF00]' + translation(30380) + '[/COLOR]',
           dict(MODE=AUTHENTICATION_DETAILS_MODE),
           defaultfanart)
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=refresh)

def CATEGORY_SHELF(args):
    et = util.get_url_as_xml_soup_cache(get_url('http://espn.go.com/watchespn/appletv/featured'))
    for shelf in et.findall('.//shelf'):
        name = shelf.get('id')
        if name == args.get(SHELF_ID)[0]:
            process_item_list(shelf.findall('.//sixteenByNinePoster'))
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)

def CATEGORY_SPORTS(args):
    et = util.get_url_as_xml_soup_cache(get_url('http://espn.go.com/watchespn/appletv/sports'))
    images = et.findall('.//image')
    sports = et.findall('.//oneLineMenuItem')
    for i in range(0, min(len(images), len(sports))):
        sport = sports[i]
        image = images[i]
        name = sport.get('accessibilityLabel')
        image = image.text
        url = util.parse_url_from_method(sport.get('onSelect'))
        addDir(name,
               dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
               image, image)
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=False)

def CATEGORY_CHANNELS(args):
    et = util.get_url_as_xml_soup_cache(get_url('http://espn.go.com/watchespn/appletv/channels'))
    for channel in et.findall('.//oneLineMenuItem'):
        name = channel.get('accessibilityLabel')
        image = channel.find('.//image').text
        url = util.parse_url_from_method(channel.get('onSelect'))
        addDir(name,
               dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
               image, image)
    xbmcplugin.endOfDirectory(pluginhandle, updateListing=False)


def process_item_list(item_list):
    for item in item_list:
        stash_element = item.find('./stash/json')
        if item.get('id').startswith('loadMore'):
            method_info = util.parse_method_call(item.get('onSelect'))
            if method_info[0] == 'espn.page.loadMore':
                label = item.find('./label')
                label2 = item.find('./label2')
                menu_label = ''
                if label is not None:
                    menu_label = label.text
                if label2 is not None:
                    menu_label = menu_label + ' ' + label2.text
                if label is None and label2 is None:
                    menu_label = translation(30570)
                url = method_info[3]
                nav_id = method_info[2]
                url = url + '&navigationItemId=' + nav_id
                xbmc.log(TAG + 'Load more url %s' % url, LOG_LEVEL)
                addDir(menu_label,
                       dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
                       defaultimage)
        elif not item.get('id') == 'no-event':
            if stash_element is None:
                # Assume goes to another onPlay with a url
                name = item.get('accessibilityLabel')
                image = item.find('./image').get('src')
                url = util.parse_url_from_method(item.get('onPlay'))
                addDir(name,
                       dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
                       image, image)
            else:
                stash = stash_element.text.encode('utf-8')
                # Some of the json is baddly formatted
                stash = re.sub(r'\s+"', '"', stash)
                stash_json = json.loads(stash, 'utf-8')
                if stash_json['type'] == 'upcoming':
                    INDEX_TV_SHELF(stash_json, item, True)
                elif 'sessionUrl' in stash_json:
                    INDEX_TV_SHELF(stash_json, item, False)
                else:
                    INDEX_ITEM_SHELF(stash_json, item)


def CATEGORIES_SHOWCASE(args):
    url = args.get(SHOWCASE_URL)[0]
    selected_nav_id = args.get(SHOWCASE_NAV_ID, None)
    et = util.get_url_as_xml_soup_cache(get_url(url))
    navigation_items = et.findall('.//navigation/navigationItem')
    xbmc.log('ESPN3 Found %s items' % len(navigation_items), LOG_LEVEL)
    if selected_nav_id is None and len(navigation_items) > 0:
        for navigation_item in navigation_items:
            name = navigation_item.find('./title').text
            nav_id = navigation_item.get('id')
            menu_item = navigation_item.find('.//twoLineMenuItem')
            if menu_item is None:
                menu_item = navigation_item.find('.//twoLineEnhancedMenuItem')
            if menu_item is not None and not menu_item.get('id') == 'no-event':
                addDir(name,
                       dict(SHOWCASE_URL=url, SHOWCASE_NAV_ID=nav_id, MODE=CATEGORY_SHOWCASE_MODE), defaultfanart)
    elif len(navigation_items) > 0:
        for navigation_item in navigation_items:
            if navigation_item.get('id') == selected_nav_id[0]:
                xbmc.log('ESPN3 Found nav item %s' % selected_nav_id[0], LOG_LEVEL)
                process_item_list(navigation_item.findall('.//twoLineMenuItem'))
                process_item_list(navigation_item.findall('.//twoLineEnhancedMenuItem'))
                xbmcplugin.setContent(pluginhandle, 'episodes')
    else: # If there are no navigation items then just dump all of the menu entries
        xbmc.log('ESPN3: Dumping all menu items', LOG_LEVEL)
        process_item_list(et.findall('.//twoLineMenuItem'))
        process_item_list(et.findall('.//twoLineEnhancedMenuItem'))
        xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(pluginhandle)

def get_metadata(item):
    metadataKeysElement = item.find('.//metadataKeys')
    metadataValuesElement = item.find('.//metadataValues')
    description = ''
    if metadataKeysElement is not None and metadataValuesElement is not None:
        keyLabels = metadataKeysElement.findall('.//label')
        valueLabels = metadataValuesElement.findall('.//label')
        for i in range(0, min(len(keyLabels), len(valueLabels))):
            if valueLabels[i].text is not None:
                description = description + '%s: %s\n' % (keyLabels[i].text, valueLabels[i].text)
    return description

# Items can play as is and do not need authentication
def INDEX_ITEM_SHELF(stash_json, item):
    sport = stash_json['sportName']
    ename = stash_json['name']
    fanart = stash_json['imageHref']
    length = int(stash_json['duration'])
    description = stash_json['description']
    description = description + '\n\n' + get_metadata(item)

    infoLabels = {'title': ename,
                  'genre':sport,
                  'duration':length,
                  'plot':description}

    authurl = dict()
    authurl[MODE] = PLAY_ITEM_MODE
    authurl[PLAYBACK_URL] = stash_json['playbackUrl']
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)

def INDEX_TV_SHELF(stash_json, item, upcoming):
    sport = stash_json['categoryName']
    ename = stash_json['name']
    sport2 = stash_json['subcategoryName']
    if sport <> sport2:
        sport += ' ('+sport2+')'
    fanart = stash_json['imageHref']
    mpaa = stash_json['parentalRating']
    starttime = int(stash_json['startTime'])/1000
    now = time.time()
    etime = time.strftime("%I:%M %p",time.localtime(float(starttime)))
    length = int(stash_json['duration'])
    if stash_json['type'] == 'replay':
        etime_local = time.localtime(starttime)
        if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
            etime = time.strftime("%m/%d/%Y",time.localtime(starttime))
        else:
            etime = time.strftime("%m/%d %I:%M %p",time.localtime(starttime))
        ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
    elif now > starttime:
        length = length - (now - starttime)
        xbmc.log(TAG + ' Setting length to %s' % length, LOG_LEVEL)
        ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
    else:
        now_time = time.localtime(now)
        start_time = time.localtime(starttime)
        if now_time.tm_year == start_time.tm_year and \
            now_time.tm_mon == start_time.tm_mon and \
                now_time.tm_mday == start_time.tm_mday:
            etime = time.strftime("%I:%M %p", time.localtime(starttime))
        else:
            etime = time.strftime("%m/%d %I:%M %p", time.localtime(starttime))
        ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
    aired = time.strftime("%Y-%m-%d",time.localtime(starttime))

    network = stash_json['network']
    if network == 'longhorn':
        channel_color = 'BF5700'
    elif network == 'sec' or network == 'secplus':
        channel_color = '004C8D'
    else:
        channel_color = 'CC0000'
    network = network.replace('espn', translation(30590))
    network = network.replace('sec', translation(30600))
    network = network.replace('longhorn', translation(30610))
    blackout = check_blackout(item)
    blackout_text = ''
    if blackout:
        blackout_text = translation(30580)
    ename = '[COLOR=FF%s]%s[/COLOR] %s %s' % (channel_color, network, blackout_text, ename)

    if 'description' in stash_json:
        description = stash_json['description']
    else:
        description = ''
    description = description + '\n\n' + get_metadata(item)

    requires_auth = does_requires_auth(stash_json['network'])
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = '*' + ename

    infoLabels = {'title': ename,
                  'genre':sport,
                  'duration':length,
                  'studio': stash_json['network'],
                  'mpaa':mpaa,
                  'plot':description,
                  'aired':aired,
                  'premiered':aired}

    authurl = dict()
    if upcoming:
        authurl[MODE] = UPCOMING_MODE
    else:
        authurl[EVENT_ID] = stash_json['eventId']
        authurl[SESSION_URL] = stash_json['sessionUrl']
        authurl[MODE] = PLAY_TV_MODE
        authurl[NETWORK_NAME] = stash_json['network']
        authurl[EVENT_NAME] = stash_json['name'].encode('iso-8859-1')
        authurl[EVENT_GUID] = stash_json['guid'].encode('iso-8859-1')
        authurl[EVENT_PARENTAL_RATING] = mpaa
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)

def check_blackout(item):
    blackouts = item.findall('.//blackouts/blackoutsItem/detail/detailItem')
    blackout_type = item.find('.//blackouts/blackoutsItem/type')
    if blackout_type is not None and not blackout_type.text == 'dma':
        return False
    user_dma = player_config.get_dma()
    if blackouts is not None:
        for blackout in blackouts:
            if blackout.text == user_dma:
                return True
    return False

def PLAY_ITEM(args):
    url = args.get(PLAYBACK_URL)[0]
    item = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

base_url = sys.argv[0]
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get(MODE, None)

xbmc.log('ESPN3: args %s' % args, LOG_LEVEL)

refresh = False
if mode is not None and mode[0] == AUTHENTICATE_MODE:
    xbmc.log('Authenticate Device', LOG_LEVEL)
    regcode = adobe_activate_api.get_regcode()
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30310),
                   translation(30320),
                   translation(30330) % regcode,
                   translation(30340),
                   translation(30360),
                   translation(30350))
    if ok:
        try:
            adobe_activate_api.authenticate()
            dialog.ok(translation(30310), translation(30370))
        except urllib2.HTTPError as e:
            dialog.ok(translation(30037), translation(30420) % e)
    mode = None
    refresh = True
elif mode is not None and mode[0] == AUTHENTICATION_DETAILS_MODE:
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30380),
                      translation(30390) % adobe_activate_api.get_authentication_expires(),
                      nolabel = translation(30360),
                      yeslabel = translation(30430))
    if ok:
        adobe_activate_api.deauthorize()
    mode = None
    refresh = True

if mode == None:
    adobe_activate_api.clean_up_authorization_tokens()
    xbmc.log("Generate Main Menu", LOG_LEVEL)
    CATEGORIES_ATV(refresh)
elif mode[0] == CATEGORY_SHOWCASE_MODE:
    CATEGORIES_SHOWCASE(args)
elif mode[0] == LIVE_EVENTS_MODE:
    xbmc.log("Indexing Videos", LOG_LEVEL)
    legacy.INDEX(args)
elif mode[0] == LIST_SPORTS_MODE:
    xbmc.log("List sports", LOG_LEVEL)
    legacy.LISTSPORTS(args)
elif mode[0] == INDEX_SPORTS_MODE:
    xbmc.log("Index by sport", LOG_LEVEL)
    legacy.INDEX(args)
elif mode[0] == PLAY_MODE:
    legacy.PLAY_LEGACY_TV(args)
elif mode[0] == PLAY_ITEM_MODE:
    PLAY_ITEM(args)
elif mode[0] == PLAY_TV_MODE:
    PLAY_TV(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming", LOG_LEVEL)
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=False,updateListing=True)
elif mode[0] == CATEGORY_SHELF_MODE:
    CATEGORY_SHELF(args)
elif mode[0] == OLD_LISTING_MODE:
    xbmc.log("Old listing mode", LOG_LEVEL)
    legacy.CATEGORIES()
elif mode[0] == CATEGORY_SPORTS_MODE:
    CATEGORY_SPORTS(args)
elif mode[0] == CATEGORY_CHANNELS_MODE:
    CATEGORY_CHANNELS(args)
