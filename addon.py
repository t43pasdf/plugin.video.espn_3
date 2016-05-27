#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import urllib, xbmcplugin, xbmcaddon, xbmcgui
import time
from datetime import datetime, timedelta
import base64
import urlparse

from globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle
import player_config
import events
import util
import urlparse
import m3u8
import re
import json

import adobe_activate_api

OLD_LISTING_MODE = 'OLD_LISTING_MODE'
LIVE_EVENTS_MODE = 'LIVE_EVENTS'
PLAY_MODE = 'PLAY'
PLAY_ITEM_MODE = 'PLAY_ITEM'
PLAY_TV_MODE = 'PLAY_TV'
LIST_SPORTS_MODE = 'LIST_SPORTS'
INDEX_SPORTS_MODE = 'INDEX_SPORTS'
UPCOMING_MODE = 'UPCOMING'
AUTHENTICATE_MODE = 'AUTHENTICATE'
AUTHENTICATION_DETAILS_MODE = 'AUTHENTICATION_DETAILS'
CATEGORY_SHELF_MODE = 'CATEGORY_SHELF'
CATEGORY_SHOWCASE_MODE = 'CATEGORY_SHOWCASE'
CATEGORY_SPORTS_MODE = 'CATEGORY_SPORTS'
CATEGORY_CHANNELS_MODE = 'CATEGORY_CHANNELS'
NETWORK_ID = 'NETWORK_ID'
EVENT_ID = 'EVENT_ID'
SIMULCAST_AIRING_ID = 'SIMULCAST_AIRING_ID'
SESSION_URL = 'SESSION_URL'
DESKTOP_STREAM_SOURCE = 'DESKTOP_STREAM_SOURCE'
NETWORK_NAME = 'NETWORK_NAME'
EVENT_NAME = 'EVENT_NAME'
EVENT_GUID = 'EVENT_GUID'
EVENT_PARENTAL_RATING = 'EVENT_PARENTAL_RATING'
SHELF_ID = 'SHELF_ID'
SHOWCASE_URL = 'SHOWCASE_URL'
SHOWCASE_NAV_ID = 'SHOWCASE_NAV_ID'
PLAYBACK_URL = 'PLAYBACK_URL'

ESPN_URL = 'ESPN_URL'
MODE = 'MODE'
SPORT = 'SPORT'

BAM_NS = '{http://services.bamnetworks.com/media/types/2.1}'

# Taken from https://espn.go.com/watchespn/player/config
ESPN3_ID = 'n360'
SECPLUS_ID = 'n323'

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
    xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=refresh)

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
    xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=False)

def CATEGORY_CHANNELS(args):
    et = util.get_url_as_xml_soup_cache(get_url('http://espn.go.com/watchespn/appletv/channels'))
    for channel in et.findall('.//oneLineMenuItem'):
        name = channel.get('accessibilityLabel')
        image = channel.find('.//image').text
        url = util.parse_url_from_method(channel.get('onSelect'))
        addDir(name,
               dict(SHOWCASE_URL=url, MODE=CATEGORY_SHOWCASE_MODE),
               image, image)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=False)


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
                xbmc.log(TAG + 'Load more url %s' % url)
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
                    INDEX_ITEM_UPCOMING(stash_json, item)
                elif 'sessionUrl' in stash_json:
                    INDEX_TV_SHELF(stash_json, item)
                else:
                    INDEX_ITEM_SHELF(stash_json, item)


def CATEGORIES_SHOWCASE(args):
    url = args.get(SHOWCASE_URL)[0]
    selected_nav_id = args.get(SHOWCASE_NAV_ID, None)
    et = util.get_url_as_xml_soup_cache(get_url(url))
    navigation_items = et.findall('.//navigation/navigationItem')
    xbmc.log('ESPN3 Found %s items' % len(navigation_items))
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
                xbmc.log('ESPN3 Found nav item %s' % selected_nav_id[0])
                process_item_list(navigation_item.findall('.//twoLineMenuItem'))
                process_item_list(navigation_item.findall('.//twoLineEnhancedMenuItem'))
                xbmcplugin.setContent(pluginhandle, 'episodes')
    else: # If there are no navigation items then just dump all of the menu entries
        xbmc.log('ESPN3: Dumping all menu items')
        process_item_list(et.findall('.//twoLineMenuItem'))
        process_item_list(et.findall('.//twoLineEnhancedMenuItem'))
        xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

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

def INDEX_ITEM_UPCOMING(stash_json, item):
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
    if now > starttime:
        length = length - (now - starttime)
        ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
    if now < starttime:
        etime = time.strftime("%m/%d %I:%M %p",time.localtime(starttime))
        ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
    aired = time.strftime("%Y-%m-%d", time.localtime(starttime))

    description = get_metadata(item)

    infoLabels = {'title': ename,
                  'genre':sport,
                  'duration':length,
                  'studio': stash_json['network'],
                  'mpaa':mpaa,
                  'aired':aired,
                  'plot': description}

    authurl = dict()
    authurl[MODE] = UPCOMING_MODE
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)


def INDEX_TV_SHELF(stash_json, item):
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
        xbmc.log(TAG + ' Setting length to %s' % length)
        ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
    aired = time.strftime("%Y-%m-%d",time.localtime(starttime))

    network = stash_json['network']
    if network == 'longhorn':
        channel_color = 'BF5700'
    elif network == 'sec' or network == 'secplus':
        channel_color = '004C8D'
    else:
        channel_color = 'CC0000'
    network = network.replace('espn', 'ESPN')
    network = network.replace('sec', 'SEC')
    network = network.replace('longhorn', 'Longhorn')
    blackout = check_blackout(item)
    blackout_text = ''
    if blackout:
        blackout_text = '[BLACKOUT]'
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
    authurl[EVENT_ID] = stash_json['eventId']
    authurl[SESSION_URL] = stash_json['sessionUrl']
    authurl[MODE] = PLAY_TV_MODE
    authurl[NETWORK_NAME] = stash_json['network']
    authurl[EVENT_NAME] = stash_json['name'].encode('iso-8859-1')
    authurl[EVENT_GUID] = stash_json['guid'].encode('iso-8859-1')
    authurl[EVENT_PARENTAL_RATING] = mpaa
    addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)

def CATEGORIES():
    include_premium = adobe_activate_api.is_authenticated()
    channel_list = events.get_channel_list(include_premium)
    curdate = datetime.utcnow()
    upcoming = int(selfAddon.getSetting('upcoming'))+1
    days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
    addDir(translation(30029),
           dict(ESPN_URL=events.get_live_events_url(channel_list), MODE=LIVE_EVENTS_MODE),
           defaultlive)
    addDir(translation(30030),
           dict(ESPN_URL=events.get_upcoming_events_url(channel_list) + '&endDate='+days+'&startDate='+curdate.strftime("%Y%m%d"), MODE=LIST_SPORTS_MODE),
           defaultupcoming)
    enddate = '&endDate='+ (curdate+timedelta(days=1)).strftime("%Y%m%d")
    replays1 = [5,10,15,20,25]
    replays1 = replays1[int(selfAddon.getSetting('replays1'))]
    start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
    replays2 = [10,20,30,40,50]
    replays2 = replays2[int(selfAddon.getSetting('replays2'))]
    start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
    replays3 = [30,60,90,120]
    replays3 = replays3[int(selfAddon.getSetting('replays3'))]
    start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
    replays4 = [60,90,120,240]
    replays4 = replays4[int(selfAddon.getSetting('replays4'))]
    start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
    startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
    addDir(translation(30031)+str(replays1)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start1, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays2)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start2, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays3)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start3, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays3)+'-'+str(replays4)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +'&endDate='+start3+'&startDate='+start4, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30032),
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+startAll, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def LISTSPORTS(args):
    espn_url = args.get(ESPN_URL)[0]
    if 'action=replay' in espn_url:
        image = defaultreplay
    elif 'action=upcoming' in espn_url:
        image = defaultupcoming
    else:
        image = defaultimage
    addDir(translation(30034), dict(ESPN_URL=espn_url, MODE=LIVE_EVENTS_MODE), image)
    sports = []
    sport_elements = util.get_url_as_xml_soup_cache(espn_url).findall('.//sportDisplayValue')
    for sport in sport_elements:
        sport = sport.text.encode('utf-8')
        if sport not in sports:
            sports.append(sport)
    for sport in sports:
        addDir(sport, dict(ESPN_URL=espn_url, MODE=INDEX_SPORTS_MODE, SPORT=sport), image)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def INDEX_EVENT(event, live, upcoming, replay, chosen_sport):
    sport = event.find('sportDisplayValue').text.encode('utf-8')
    desktopStreamSource = event.find('desktopStreamSource').text
    ename = event.find('name').text
    eventid = event.get('id')
    simulcastAiringId = event.find('simulcastAiringId').text
    networkid = event.find('networkId').text
    if networkid is not None:
        network = player_config.get_network_name(networkid)
    sport2 = event.find('sport').text
    if sport <> sport2:
        sport += ' ('+sport2+')'
    league = event.find('league').text
    location = event.find('site').text
    fanart = event.find('.//thumbnail/large').text
    fanart = fanart.split('&')[0]
    mpaa = event.find('parentalRating').text
    starttime = int(event.find('startTimeGmtMs').text)/1000
    etime = time.strftime("%I:%M %p",time.localtime(float(starttime)))
    endtime = int(event.find('endTimeGmtMs').text)/1000
    start = time.strftime("%m/%d/%Y %I:%M %p",time.localtime(starttime))
    aired = time.strftime("%Y-%m-%d",time.localtime(starttime))
    udate = time.strftime("%m/%d",time.localtime(starttime))
    now = datetime.now().strftime('%H%M')
    etime24 = time.strftime("%H%M",time.localtime(starttime))
    aspect_ratio = event.find('aspectRatio').text
    length = str(int(round((endtime - time.time()))))
    title_time = etime
    if live and now > etime24:
        color = str(selfAddon.getSetting('color'))
    elif live:
        color = '999999'
    else:
        color = 'E0E0E0'
        length = str(int(round((endtime - starttime))))
        title_time = ' - '.join((udate, etime))

    if network == 'longhorn':
        channel_color = 'BF5700'
    elif network == 'sec' or network == 'secplus':
        channel_color = '004C8D'
    else:
        channel_color = 'CC0000'

    ename = '[COLOR=FF%s]%s[/COLOR] [COLOR=FFB700EB]%s[/COLOR] [COLOR=FF%s]%s[/COLOR]' % (channel_color, network, title_time, color, ename)

    length_minutes = int(length) / 60

    end = event.find('summary').text
    if end is None or len(end) == 0:
        end = event.find('caption').text

    if end is None:
        end = ''
    end += '\nNetwork: ' + network

    plot = ''
    if sport <> None and sport <> ' ':
        plot += 'Sport: '+sport+'\n'
    if league <> None and league <> ' ':
        plot += 'League: '+league+'\n'
    if location <> None and location <> ' ':
        plot += 'Location: '+location+'\n'
    if start <> None and start <> ' ':
        plot += 'Air Date: '+start+'\n'
    if length <> None and length <> ' ' and live:
        plot += 'Duration: Approximately '+ str(length_minutes)+' minutes remaining'+'\n'
    elif length <> None and length <> ' ' and (replay or upcoming):
        plot += 'Duration: '+ str(length_minutes) +' minutes'+'\n'
    plot += end
    infoLabels = {'title': ename,
                  'genre':sport,
                  'plot':plot,
                  'aired':aired,
                  'premiered':aired,
                  'duration':length,
                  'studio':network,
                  'mpaa':mpaa,
                  'videoaspect' : aspect_ratio}

    session_url = 'http://broadband.espn.go.com/espn3/auth/watchespn/startSession?'
    session_url += '&channel='+network
    session_url += '&simulcastAiringId='+simulcastAiringId

    authurl = dict()
    authurl[EVENT_ID] = eventid
    authurl[MODE] = UPCOMING_MODE if upcoming else PLAY_MODE
    authurl[NETWORK_NAME] = event.find('adobeResource').text
    authurl[EVENT_NAME] = event.find('name').text.encode('utf-8')
    authurl[EVENT_GUID] = event.find('guid').text.encode('utf-8')
    authurl[EVENT_PARENTAL_RATING] = event.find('parentalRating').text
    authurl[SESSION_URL] = session_url
    addLink(ename, authurl, fanart, fanart, infoLabels=infoLabels)

def INDEX(args):
    espn_url = args.get(ESPN_URL)[0]
    chosen_sport = args.get(SPORT, None)
    if chosen_sport is not None:
        chosen_sport = chosen_sport[0]
    chosen_network = args.get(NETWORK_ID, None)
    if chosen_network is not None:
        chosen_network = chosen_network[0]
    live = 'action=live' in espn_url
    upcoming = 'action=upcoming' in espn_url
    replay = 'action=replay' in espn_url
    if live:
        data = events.get_events(espn_url)
    else:
        data = util.get_url_as_xml_soup_cache(espn_url).findall(".//event")
    num_espn3 = 0
    num_secplus = 0
    num_events = 0
    for event in data:
        sport = event.find('sportDisplayValue').text.encode('utf-8')
        if chosen_sport <> sport and chosen_sport is not None:
            continue
        networkid = event.find('networkId').text
        if chosen_network <> networkid and chosen_network is not None:
            continue
        if networkid == ESPN3_ID and chosen_network is None and live :
            num_espn3 = num_espn3 + 1
        elif networkid == SECPLUS_ID and chosen_network is None and live :
            num_secplus = num_secplus + 1
        else:
            num_events = num_events + 1
            INDEX_EVENT(event, live, upcoming, replay, chosen_sport)
    # Don't show ESPN3 folder if there are no premium events
    if num_events == 0:
        for event in data:
            sport = event.find('sportDisplayValue').text.encode('utf-8')
            if chosen_sport <> sport and chosen_sport is not None:
                continue
            INDEX_EVENT(event, live, upcoming, replay, chosen_sport)
    # Dir for ESPN3/SECPlus
    elif chosen_network is None:
        if num_espn3 > 0:
            translation_number = 30191 if num_espn3 == 1 else 30190
            addDir('[COLOR=FFCC0000]' + (translation(translation_number) % num_espn3) + '[/COLOR]',
               dict(ESPN_URL=espn_url, MODE=LIVE_EVENTS_MODE, NETWORK_ID=ESPN3_ID),
               defaultlive)
        if num_secplus > 0:
            translation_number = 30201 if num_espn3 == 1 else 30200
            addDir('[COLOR=FF004C8D]' + (translation(translation_number) % num_secplus) + '[/COLOR]',
               dict(ESPN_URL=espn_url, MODE=LIVE_EVENTS_MODE, NETWORK_ID=SECPLUS_ID),
               defaultlive)
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

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
    return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

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
            xbmc.log('ESPN3: User needs login to ESPN3')
            requires_auth = True
    return requires_auth


def PLAY_LEGACY_TV(args):
    # check blackout differently for legacy shows
    event_id = args.get(EVENT_ID)[0]
    network_name = args.get(NETWORK_NAME)[0]
    url = 'http://broadband.espn.go.com/espn3/auth/watchespn/util/isUserBlackedOut?eventId=' + event_id
    xbmc.log(TAG + 'Blackout url %s' % url)
    blackout_data = util.get_url_as_json(url)
    if network_name == 'espn3':
        blackout = blackout_data['E3BlackOut']
    else:
        blackout = blackout_data['LinearBlackOut']
    if blackout == 'true':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30040))
        return
    PLAY_TV(args)

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

    xbmc.log('ESPN3: start_session_url: ' + start_session_url)

    session_json = util.get_url_as_json(start_session_url)
    if check_error(session_json):
        return

    playback_url = session_json['session']['playbackUrls']['default']
    stream_quality = str(selfAddon.getSetting('StreamQuality'))
    bitrate_limit = int(selfAddon.getSetting('BitrateLimit'))
    xbmc.log(TAG + 'Stream Quality %s' % stream_quality)
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
                             (stream_info['bandwidth'], stream_info['average_bandwidth']))
                stream_options.append(translation(30450) % (resolution,
                                                      frame_rate,
                                                      bandwidth))
            dialog = xbmcgui.Dialog()
            stream_index = dialog.select(translation(30440), stream_options)
            if stream_index < 0:
                success = False
            else:
                selfAddon.setSetting(id='StreamQualityIndex', value=str(stream_index))

        xbmc.log(TAG + 'Chose stream %d' % stream_index)
        item = xbmcgui.ListItem(path=m3u8_obj.playlists[stream_index].uri)
        return xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)
    else:
        item = xbmcgui.ListItem(path=finalurl)
        return xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)

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
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
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
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get(MODE, None)

xbmc.log('ESPN3: args %s' % args)

refresh = False
if mode is not None and mode[0] == AUTHENTICATE_MODE:
    xbmc.log('Authenticate Device')
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
    xbmc.log("Generate Main Menu")
    CATEGORIES_ATV(refresh)
elif mode[0] == CATEGORY_SHOWCASE_MODE:
    CATEGORIES_SHOWCASE(args)
elif mode[0] == LIVE_EVENTS_MODE:
    xbmc.log("Indexing Videos")
    INDEX(args)
elif mode[0] == LIST_SPORTS_MODE:
    xbmc.log("List sports")
    LISTSPORTS(args)
elif mode[0] == INDEX_SPORTS_MODE:
    xbmc.log("Index by sport")
    INDEX(args)
elif mode[0] == PLAY_MODE:
    PLAY_LEGACY_TV(args)
elif mode[0] == PLAY_ITEM_MODE:
    PLAY_ITEM(args)
elif mode[0] == PLAY_TV_MODE:
    PLAY_TV(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming")
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=False,updateListing=True)
elif mode[0] == CATEGORY_SHELF_MODE:
    CATEGORY_SHELF(args)
elif mode[0] == OLD_LISTING_MODE:
    xbmc.log("Old listing mode")
    CATEGORIES()
elif mode[0] == CATEGORY_SPORTS_MODE:
    CATEGORY_SPORTS(args)
elif mode[0] == CATEGORY_CHANNELS_MODE:
    CATEGORY_CHANNELS(args)
