# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time
import logging

try:
    from urllib import quote_plus
except ImportError:
    from urllib.parse import quote_plus

from xbmcplugin import addDirectoryItem
from resources.lib.kodiutils import get_setting_as_bool, get_string
from resources.lib.addon_util import check_auth_types, get_auth_types_from_network, make_list_item, \
    include_item, get_league, get_subcategory, check_json_blackout
from resources.lib.constants import NETWORK_ID_TO_NETWORK_NAME

from resources.lib import adobe_activate_api

from resources.lib.play_routes import upcoming_event, play_item, play_tv
from resources.lib.plugin_routing import plugin


def format_time(etime):
    return etime


def get_item_listing_text(event_name, starttime, duration, status, network,
                          blackout, auth_types, requires_package=False, sport=None, sport2=None):
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

    blackout_text = ''
    if blackout:
        blackout_text = get_string(30580)
    if len(blackout_text) > 0:
        ename = blackout_text + ' ' + ename
    if len(network) > 0:
        if get_setting_as_bool('NoColors'):
            ename = network + ' ' + ename
        else:
            # ename = '[B]%s[/B] %s' % (network, ename)
            ename = '%s %s' % (network, ename)

    requires_auth = check_auth_types(auth_types)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = get_string(40300) + ' - ' + ename
    if requires_package:
        ename = get_string(40310) + ' - ' + ename
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

    etime = time.time()
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
    if 'networkName' in args:
        network = args['networkName']
    else:
        network = network_id
    logging.debug('network_id ' + network_id)
    if network_id in NETWORK_ID_TO_NETWORK_NAME:
        network = get_string(NETWORK_ID_TO_NETWORK_NAME[network_id])
    blackout = args['blackout'] if 'blackout' in args else False
    blackout_text = ''
    if blackout:
        blackout_text = get_string(30580)
    if len(blackout_text) > 0:
        ename = blackout_text + ' ' + ename
    if len(network) > 0:
        if get_setting_as_bool('NoColors'):
            ename = network + ' ' + ename
        else:
            ename = '[B]%s[/B] ' % (network) + ename

    description = args['description']
    auth_types = get_auth_types_from_network(network_id)
    requires_auth = check_auth_types(auth_types)
    if requires_auth and not adobe_activate_api.is_authenticated():
        ename = '*' + ename

    logging.debug('Duration %s' % length)

    mpaa = args['parentalRating'] if 'parentRating' in args else 'U'
    info_labels = {'title': ename,
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
                         plugin.url_for(upcoming_event, event_id=args['eventId'], starttime=etime,
                                        event_name=quote_plus(ename.encode('utf-8'))),
                         make_list_item(ename, icon=fanart, info_labels=info_labels))
    else:
        adobe_rss = args['adobeRSS'] if 'adobeRSS' in args else None
        guid = args['guid'] if 'guid' in args else None
        if adobe_rss is None and guid is None:
            addDirectoryItem(plugin.handle,
                             plugin.url_for(play_item, url=args['sessionUrl'], event_id=args['eventId']),
                             make_list_item(ename, icon=fanart, info_labels=info_labels))
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
                                 plugin.url_for(play_tv, event_id=args['eventId'],
                                                session_url=args['sessionUrl'], network_name=args['networkId'],
                                                resource=quote_plus(adobe_rss.encode('utf-8'))),
                                 make_list_item(ename, icon=fanart, info_labels=info_labels))
            else:
                logging.debug('Skipping %s' % args['networkId'])


def index_listing(listing):
    # 2016-06-06T18:00:00EDT
    # EDT is discarded due to http://bugs.python.org/issue22377
    time_format = '%Y-%m-%dT%H:%M:%S'
    starttime = time.strptime(listing['startTime'][:-3], time_format)
    endtime = time.strptime(listing['endTime'][:-3], time_format)
    duration = (time.mktime(endtime) - time.mktime(starttime))
    logging.debug(' Duration: %s' % duration)
    logging.debug(listing)

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
        'eventId': listing['eventId'] if len(str(listing['eventId'])) > 0 else listing['id'],
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
