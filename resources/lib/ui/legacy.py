# Legacy menu system
from datetime import datetime, timedelta

from resources.lib import events
from resources.lib.globals import defaultreplay, \
    defaultupcoming
from resources.lib.item_indexer import *
from resources.lib.kodiutils import get_setting_as_int

LIST_SPORTS_MODE = 'LIST_SPORTS'
INDEX_SPORTS_MODE = 'INDEX_SPORTS'
ROOT = '/legacy'

@plugin.route(ROOT)
def legacy_root_menu():
    include_premium = adobe_activate_api.is_authenticated()
    channel_list = events.get_channel_list(include_premium)
    curdate = datetime.utcnow()
    upcoming = int(selfAddon.getSetting('upcoming'))+1
    days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
    # Live
    addDirectoryItem(plugin.handle,
                     plugin.url_for(live_events_mode, espn_url=events.get_live_events_url(channel_list)),
                     make_list_item(translation(30029)), True)
    # Upcoming
    espn_url = events.get_upcoming_events_url(channel_list) + '&endDate=' + days + '&startDate=' + curdate.strftime("%Y%m%d")
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_live_events_url(channel_list)),
                     make_list_item(translation(30030)), True)
    enddate = '&endDate=' + (curdate+timedelta(days=1)).strftime("%Y%m%d")
    replays1 = [5, 10, 15, 20, 25]
    replays1 = replays1[get_setting_as_int('replays1')]
    start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
    replays2 = [10, 20, 30, 40, 50]
    replays2 = replays2[get_setting_as_int('replays2')]
    start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
    replays3 = [30, 60, 90, 120]
    replays3 = replays3[get_setting_as_int('replays3')]
    start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
    replays4 = [60, 90, 120, 240]
    replays4 = replays4[get_setting_as_int('replays4')]
    start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
    startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_replay_events_url(
                         channel_list) + enddate + '&startDate=' + start1),
                     make_list_item(translation(30031) % replays1), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_replay_events_url(
                         channel_list) + enddate + '&startDate=' + start2),
                     make_list_item(translation(30031) % replays2), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_replay_events_url(
                         channel_list) + enddate + '&startDate=' + start3),
                     make_list_item(translation(30031) % replays3), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_replay_events_url(
                         channel_list) + '&endDate=' + start3 + '&startDate=' + start4),
                     make_list_item(translation(30033) % (replays3, replays4)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(list_sports, espn_url=events.get_replay_events_url(
                         channel_list) + enddate + '&startDate=' + startAll),
                     make_list_item(translation(30032)), True)
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/list-sports')
def list_sports():
    espn_url = arg_as_string('espn_url')
    if 'action=replay' in espn_url:
        image = defaultreplay
    elif 'action=upcoming' in espn_url:
        image = defaultupcoming
    else:
        image = None
    addDirectoryItem(plugin.handle,
                     plugin.url_for(live_events_mode, espn_url=espn_url),
                     make_list_item(translation(30034), icon=image), True)
    sports = []
    sport_elements = util.get_url_as_xml_cache(espn_url, encoding='ISO-8859-1').findall('.//sportDisplayValue')
    for sport in sport_elements:
        sport = sport.text.encode('utf-8')
        if sport not in sports:
            sports.append(sport)
    for sport in sports:
        addDirectoryItem(plugin.handle,
                         plugin.url_for(live_sport_events_mode, sport=sport, espn_url=espn_url),
                         make_list_item(sport, icon=image), True)

    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/live')
def live_events_mode():
    espn_url = arg_as_string('espn_url')
    index_legacy_live_events(espn_url)
    xbmcplugin.setContent(plugin.handle, 'episodes')
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/live/network/<network_id>')
def live_network_events_mode(network_id):
    espn_url = arg_as_string('espn_url')
    index_legacy_live_events(espn_url, network_id=network_id)
    xbmcplugin.setContent(plugin.handle, 'episodes')
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/live/sport/<sport>')
def live_sport_events_mode(sport):
    espn_url = arg_as_string('espn_url')
    index_legacy_live_events(espn_url, sport=sport)
    xbmcplugin.setContent(plugin.handle, 'episodes')
    xbmcplugin.endOfDirectory(plugin.handle)

def index_legacy_live_events(espn_url, sport=None, network_id=None):
    chosen_sport = sport
    chosen_network = network_id
    live = 'action=live' in espn_url
    upcoming = 'action=upcoming' in espn_url
    replay = 'action=replay' in espn_url
    if live:
        data = events.get_events(espn_url)
    else:
        data = util.get_url_as_xml_cache(espn_url, encoding='ISO-8859-1').findall(".//event")
    num_espn3 = 0
    num_secplus = 0
    num_accextra = 0
    num_events = 0
    for event in data:
        sport = event.find('sportDisplayValue').text.encode('utf-8')
        if chosen_sport != sport and chosen_sport is not None:
            continue
        networkid = event.find('networkId').text
        if chosen_network != networkid and chosen_network is not None:
            continue
        if networkid == ESPN3_ID and chosen_network is None and live:
            num_espn3 += 1
        elif networkid == SECPLUS_ID and chosen_network is None and live:
            num_secplus += 1
        elif networkid == ACC_EXTRA_ID and chosen_network is None and live:
            num_accextra += 1
        else:
            num_events += 1
            _index_event(event, live, upcoming, replay, chosen_sport)
    # Don't show ESPN3 folder if there are no premium events
    if num_events == 0:
        for event in data:
            sport = event.find('sportDisplayValue').text.encode('utf-8')
            if chosen_sport != sport and chosen_sport is not None:
                continue
            _index_event(event, live, upcoming, replay, chosen_sport)
    # Dir for ESPN3/SECPlus/ACC Extra
    elif chosen_network is None:
        if num_espn3 > 0 and selfAddon.getSetting('ShowEspn3') == 'true':
            translation_number = 30191 if num_espn3 == 1 else 30190
            name = (translation(translation_number) % num_espn3)
            addDirectoryItem(plugin.handle,
                             plugin.url_for(live_network_events_mode, espn_url=espn_url, network_id=ESPN3_ID),
                             make_list_item(name), True)
        if num_secplus > 0 and selfAddon.getSetting('ShowSecPlus') == 'true':
            translation_number = 30201 if num_secplus == 1 else 30200
            name = (translation(translation_number) % num_secplus)
            addDirectoryItem(plugin.handle,
                             plugin.url_for(live_network_events_mode, espn_url=espn_url, network_id=SECPLUS_ID),
                             make_list_item(name), True)
        if num_accextra > 0 and selfAddon.getSetting('ShowAccExtra') == 'true':
            translation_number = 30203 if num_accextra == 1 else 30202
            name = (translation(translation_number) % num_accextra)
            addDirectoryItem(plugin.handle,
                             plugin.url_for(live_network_events_mode, espn_url=espn_url, network_id=ACC_EXTRA_ID),
                             make_list_item(name), True)

def _index_event(event, live, upcoming, replay, chosen_sport):
    xbmc.log(TAG + ' processing event %s' % event.get('id'), xbmc.LOGDEBUG)
    networkId = event.find('networkId').text
    networkName = ''
    if networkId is not None:
        networkName = player_config.get_network_name(networkId)
    xbmc.log(TAG + ' networkName %s' % networkName, xbmc.LOGDEBUG)

    fanart = event.find('.//thumbnail/large').text
    if fanart is not None:
        fanart = fanart.split('&')[0]
    starttime = int(event.find('startTimeGmtMs').text) / 1000
    endtime = int(event.find('endTimeGmtMs').text) / 1000
    length = int(round((endtime - starttime)))
    xbmc.log(TAG + 'duration %s' % length, xbmc.LOGDEBUG)
    session_url = base64.b64decode(
        'aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi9zdGFydFNlc3Npb24/')
    session_url += 'channel=' + networkName
    if event.find('simulcastAiringId') is not None and event.find('simulcastAiringId').text is not None:
        session_url += '&simulcastAiringId=' + event.find('simulcastAiringId').text

    description = event.find('summary').text
    if description is None or len(description) == 0:
        description = event.find('caption').text
    if description is None:
        description = ''

    check_blackout = event.find('checkBlackout').text
    blackout = False
    if check_blackout == 'true':
        blackout = check_event_blackout(event.get('id'))

    index_item({
        'sport': event.find('sportDisplayValue').text,
        'eventName': event.find('name').text,
        'subcategory': event.find('sport').text,
        'imageHref': fanart,
        'parentalRating': event.find('parentalRating').text,
        'starttime': time.localtime(starttime),
        'duration': length,
        'type': event.get('type'),
        'networkId': networkName,
        'networkName': networkName,
        'blackout': blackout,
        'description': description,
        'eventId': event.get('id'),
        'sessionUrl': session_url,
        'guid': event.find('guid').text,
        'channelResourceId': event.find('adobeResource').text
    })

