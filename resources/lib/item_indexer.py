from xbmcplugin import addDirectoryItem

from play_routes import *


def format_time(etime):
    return etime

def get_item_listing_text(event_name, starttime, duration, status, network, blackout, auth_types, requires_package=False, sport=None, sport2=None):
    if sport != sport2 and len(sport2) > 0:
        sport += ' (' + sport2 + ')'
    length = duration
    if len(network) > 0:
        ename = '[B]%s[/B]' % event_name
    else:
        ename = event_name

    if starttime is not None:
        now = time.time()
        etime = time.strftime("%I:%M %p", starttime)
        if status == 'replay':
            etime_local = starttime
            if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
                etime = time.strftime("%m/%d/%Y", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = etime + ' - ' + ename
        elif status == 'live':
            starttime_time = time.mktime(starttime)
            length -= (time.time() - starttime_time)
            ename = ename + ' - ' + etime
        else:
            now_time = time.localtime(now)
            if now_time.tm_year == starttime.tm_year and \
                    now_time.tm_mon == starttime.tm_mon and \
                    now_time.tm_mday == starttime.tm_mday:
                etime = time.strftime("%I:%M %p", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = etime + ' - ' + ename
        aired = time.strftime("%Y-%m-%d", starttime)
    else:
        aired = 0

    blackout_text = ''
    if blackout:
        blackout_text = translation(30580)
    if len(blackout_text) > 0:
        ename = blackout_text + ' ' + ename
    if len(network) > 0:
        if selfAddon.getSetting('NoColors') == 'true':
            ename = network + ' ' + ename
        else:
            # ename = '[B]%s[/B] %s' % (network, ename)
            ename = '%s %s' % (network, ename)

    requires_auth = check_auth_types(auth_types)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = 'Requires Authentication - ' + ename
    if requires_package:
        ename = 'Requires ESPN+ Package - ' + ename
    return ename, length

# TODO: Make use of get_item_listing_text
def index_item(args):
    if args['type'] == 'over':
        return
    sport = args['sport']
    ename = args['eventName']
    sport2 = args['subcategory'] if 'subcategory' in args else sport
    if sport != sport2 and len(sport2) > 0:
        sport += ' (' + sport2 + ')'
    starttime = args['starttime'] if 'starttime' in args else None
    length = int(args['duration'])

    if starttime is not None:
        now = time.time()
        etime = time.strftime("%I:%M %p", starttime)
        if 'replay' in args['type']:
            etime_local = starttime
            if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
                etime = time.strftime("%m/%d/%Y", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = etime + ' - ' + ename
        elif args['type'] == 'live':
            starttime_time = time.mktime(starttime)
            length -= (time.time() - starttime_time)
            ename += ' - ' + etime
        else:
            now_time = time.localtime(now)
            if now_time.tm_year == starttime.tm_year and \
                            now_time.tm_mon == starttime.tm_mon and \
                            now_time.tm_mday == starttime.tm_mday:
                etime = time.strftime("%I:%M %p", starttime)
            else:
                etime = time.strftime("%m/%d %I:%M %p", starttime)
            ename = etime + ' - ' + ename
        aired = time.strftime("%Y-%m-%d", starttime)
    else:
        aired = 0

    network_id = args['networkId'] if 'networkId' in args else ''
    if network_id == 'longhorn':
        channel_color = 'BF5700'
    elif network_id == 'sec' or network_id == 'secplus':
        channel_color = '004C8D'
    elif network_id == 'accextra':
        channel_color = '013ca6'
    else:
        channel_color = 'CC0000'
    if 'networkName' in args:
        network = args['networkName']
    else:
        network = network_id
    xbmc.log(TAG + 'network_id ' + network_id, xbmc.LOGDEBUG)
    if network_id in NETWORK_ID_TO_NETWORK_NAME:
        network = translation(NETWORK_ID_TO_NETWORK_NAME[network_id])
    blackout = args['blackout'] if 'blackout' in args else False
    blackout_text = ''
    if blackout:
        blackout_text = translation(30580)
    if len(blackout_text) > 0:
        ename = blackout_text + ' ' + ename
    if len(network) > 0:
        if selfAddon.getSetting('NoColors') == 'true':
            ename = network + ' ' + ename
        else:
            ename = '[B]%s[/B] ' % (network) + ename

    description = args['description']
    auth_types = get_auth_types_from_network(network_id)
    requires_auth = check_auth_types(auth_types)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = '*' + ename

    xbmc.log(TAG + 'Duration %s' % length, xbmc.LOGDEBUG)

    mpaa = args['parentalRating'] if 'parentRating' in args else 'U'
    infoLabels = {'title': ename,
                  'genre': sport,
                  'duration': length,
                  'studio': network,
                  'mpaa': mpaa,
                  'plot': description,
                  'aired': aired,
                  'premiered': aired}

    fanart = args['imageHref']

    if args['type'] == 'upcoming':
        addDirectoryItem(plugin.handle,
                         plugin.url_for(upcoming_event, event_id=args['eventId'], starttime=etime, event_name=ename),
                         make_list_item(ename, icon=fanart, infoLabels=infoLabels))
    else:
        adobeRSS = args['adobeRSS'] if 'adobeRSS' in args else None
        guid = args['guid'] if 'guid' in args else None
        if adobeRSS is None and guid is None:
            addDirectoryItem(plugin.handle,
                             plugin.url_for(PLAY_ITEM, url=args['sessionUrl']),
                             make_list_item(ename, icon=fanart, infoLabels=infoLabels))
        else:
            if 'adobeRSS' in args:
                adobe_rss = args['adobeRSS']
            else:
                adobe_rss = adobe_activate_api.get_resource(args['channelResourceId'],
                                                           args['eventName'], args['guid'],
                                                           mpaa)

            if include_item(network_id):
                logging.debug('Adding %s with handle %d and id %s' % (ename, plugin.handle, args['eventId']))
                logging.debug(adobe_rss)
                addDirectoryItem(plugin.handle,
                                 plugin.url_for(PLAY_TV, event_id=args['eventId'],
                                                session_url=args['sessionUrl'], network_name=args['networkId'],
                                                resource=urllib.quote_plus(adobe_rss.encode('utf-8'))),
                                 make_list_item(ename, icon=fanart, infoLabels=infoLabels))
            else:
                logging.debug('Skipping %s' % args['networkId'])


def index_listing(listing):
    # 2016-06-06T18:00:00EDT
    # EDT is discarded due to http://bugs.python.org/issue22377
    time_format = '%Y-%m-%dT%H:%M:%S'
    starttime = time.strptime(listing['startTime'][:-3], time_format)
    endtime = time.strptime(listing['endTime'][:-3], time_format)
    duration = (time.mktime(endtime) - time.mktime(starttime))
    xbmc.log(TAG + ' Duration: %s' % duration, xbmc.LOGDEBUG)

    index_item({
        'sport': get_league(listing),
        'eventName': listing['name'],
        'subcategory': get_subcategory(listing),
        'imageHref': listing['thumbnails']['large']['href'],
        'parentalRating': listing['parentalRating'],
        'starttime': starttime,
        'duration': duration,
        'type': listing['type'],
        'networkId': listing['broadcasts'][0]['abbreviation'],
        'networkName': listing['broadcasts'][0]['name'],
        'blackout': check_json_blackout(listing),
        'description': listing['keywords'],
        'eventId': listing['eventId'],
        'sessionUrl': listing['links']['source']['hls']['default']['href'],
        'guid': listing['guid'],
        'channelResourceId': listing['broadcasts'][0]['adobeResource']

    })


def index_video(listing):
    starttime = None
    duration = listing['duration']
    index_item({
        'sport': get_league(listing),
        'eventName': listing['headline'],
        'imageHref': listing['posterImages']['default']['href'],
        'starttime': starttime,
        'duration': duration,
        'type': 'live',
        'networkId': '',
        'description': listing['description'],
        'eventId': listing['id'],
        'sessionUrl': listing['links']['source']['HLS']['HD']['href']
    })
