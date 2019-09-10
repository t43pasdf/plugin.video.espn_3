import logging
import util
import time

from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, setContent, endOfDirectory

from plugin_routing import *
from addon_util import get_url, compare
from item_indexer import index_item, get_item_listing_text
from play_routes import *

BUCKET = 'BUCKET'

@plugin.route('/page-api')
def page_api_url():
    url = arg_as_string('url')
    parse_json(url)
    endOfDirectory(plugin.handle)


@plugin.route('/page-api/buckets/<path:bucket_path>')
def page_api_buckets(bucket_path):
    url = arg_as_string('url')
    bucket_url = arg_as_string('bucket_url')
    parse_json(bucket_url)
    endOfDirectory(plugin.handle)


def parse_json(url, bucket_path=None):
    logging.debug('Looking at url %s %s' % (url, bucket_path))
    selected_bucket = bucket_path
    if selected_bucket is not None:
        selected_bucket = selected_bucket.split('/')
        logging.debug('Looking at bucket %s' % selected_bucket)
    json_data = util.get_url_as_json_cache(get_url(url))
    if 'buckets' in json_data['page']:
        buckets = json_data['page']['buckets']
        process_buckets(url, buckets, selected_bucket, list())


def process_buckets(url, buckets, selected_buckets, current_bucket_path):
    selected_bucket = None if selected_buckets is None or len(selected_buckets) == 0 else selected_buckets[0]
    logging.debug('Selected buckets: %s Current Path: %s' % (selected_buckets, current_bucket_path))
    original_bucket_path = current_bucket_path
    for bucket in buckets:
        current_bucket_path = list(original_bucket_path)
        current_bucket_path.append(str(bucket['id']))
        if selected_bucket is not None and str(bucket['id']) != selected_bucket:
            continue
        if ('contents' in bucket or 'buckets' in bucket) and selected_bucket is None and len(buckets) > 1:
            if bucket['type'] != 'images':
                bucket_path = '/'.join(current_bucket_path)
                bucket_url = bucket['links']['self']
                addDirectoryItem(plugin.handle, plugin.url_for(page_api_buckets, bucket_path=bucket_path, url=url, bucket_url=bucket_url),
                                 ListItem(bucket['name']), True)
        else:
            if 'buckets' in bucket:
                if selected_buckets is not None and len(selected_buckets) > 0:
                    process_buckets(url, bucket['buckets'], selected_buckets[1:], current_bucket_path)
                else:
                    process_buckets(url, bucket['buckets'], list(), current_bucket_path)
            else:
                if 'contents' in bucket:
                    bucket['contents'].sort(cmp=compare_contents)
                    for content in bucket['contents']:
                        content_type = content['type']
                        if content_type == 'network' or content_type == 'subcategory' or content_type == 'category' or content_type == 'program':
                            content_url = content['links']['self']
                            if 'imageHref' in content:
                                fanart = content['imageHref']
                            else:
                                fanart = None
                            addDirectoryItem(plugin.handle, plugin.url_for(page_api_url, url=content_url),
                                             ListItem(content['name'], iconImage=fanart), True)
                        else:
                            index_content(content)
                            setContent(plugin.handle, 'episodes')


def index_content(content):
    if 'tracking' in 'content':
        index_v1_content(content)
    else:
        index_v3_content(content)

def parse_duration(duration_str):
    formats = [
        '%H:%M:%S',
        '%M:%S',
        '%S'
    ]
    for format in formats:
        try:
            duration = time.strptime(duration_str, format)
            return duration
        except:
            pass
    ret = time.localtime()
    ret.tm_hour = 0
    ret.tm_min = 0
    ret.tm_sec = 0
    return ret

def get_rank_text(rank):
    if rank is None or rank == '':
        return ''
    return str(rank) + ''

def get_possesion_text(event):
    if event['teamOnePossession'] or event['teamTwoPossession']:
        return '%s has possession\n' % (event['teamOneName'] if event['teamOnePossession'] else event['teamTwoName'])
    return ''

def get_team_name(event, number):
    key_name = 'team%sName' % number
    if event['teamOneRank'] is not None and event['teamTwoRank'] is not None:
        key_rank = 'team%sRank' % number
        return '%s (%s)' % (event[key_name], get_rank_text(event[key_rank]))
    return event[key_name]

# TODO: Take into account blackout/packages
def index_v3_content(content):
    logging.debug('Indexing %s' % content)
    type = content['type']
    status = content['status']
    if type == 'show'or type == 'film':
        index_v3_show(content)
        return
    if type == 'vod':
        index_v3_vod(content)
        return
    if status == 'upcoming':
        index_v3_upcoming(content)
        return

    stream = content['streams'][0]
    duration = parse_duration(stream['duration'])
    duration_seconds = duration.tm_hour * 3600 + duration.tm_min * 60 + duration.tm_sec

    subtitle = content.get('subtitle', '')
    plot = subtitle
    if 'event' in content:
        event = content['event']
        if event['type'] == 'tvt':
            plot = '%s\n%s vs. (%s)\n%s - %s\n%s%s' % \
                   (subtitle,
                    get_team_name(event, 'One'),
                    get_team_name(event, 'Two'),
                    event['teamOneScore'], event['teamTwoScore'],
                    get_possesion_text(event),
                    event['statusTextOne'])

    starttime = get_time(content)
    if 'date' in content and 'time' in content:
        #  TODO: Include duration in plot
        plot = content['date'] + ' ' + content['time'] + '\n' + plot

    event_id = content['eventId'] if 'eventId' in content else content['id']

    ename, length = get_item_listing_text(content['name'], starttime, duration_seconds, content['status'],
                                  stream['source']['name'], 'blackoutText' in content,
                                  stream['authTypes'])

    infoLabels = {'title': ename,
                  'genre': subtitle,
                  'duration': length,
                  'studio': stream['source']['name'],
                  'plot': plot}

    addDirectoryItem(plugin.handle,
                     plugin.url_for(play_event, event_id=event_id,
                                    event_url=stream['links']['play'],
                                    auth_types=stream['authTypes']),
                     make_list_item(ename, infoLabels=infoLabels))

# TODO: Implement
def index_v3_show(content):
    pass

def index_v3_vod(content):
    pass

def index_v3_upcoming(content):
    pass

def index_v1_content(content):
    logging.debug('Indexing %s' % content)
    duration = 0
    if 'tracking' in content and 'duration' in content['tracking']:
        duration = int(content['tracking']['duration'])
    starttime = get_time(content)
    if 'date' in content and 'time' in content:
        description = content['date'] + ' ' + content['time']
        if 'tracking' in content:
            description += '\n' + content['tracking']['sport']
    else:
        description = ''
    networkId = ''
    networkName = ''
    if 'adobeRSS' in content:
        networkId = content['tracking']['network'] if 'network' in content['tracking'] else ''
        networkName = content['source']
    league = content['tracking']['league']
    index_item({
        'sport': content['tracking']['sport'],
        'eventName': content['name'] + ' (' + league + ')',
        'subcategory': content['subtitle'] if 'subtitle' in content else content['tracking']['sport'],
        'imageHref': content['imageHref'],
        'parentalRating': 'U',
        'starttime': starttime,
        'duration': duration,
        'type': content['status'] if 'status' in content else 'live',
        'networkId': networkId,
        'networkName': networkName,
        # TODO: Blackout check
        'blackout': False,
        'description': description,
        'eventId': content['id'],
        'sessionUrl': content['airings'][0]['videoHref'] if 'airings' in content else None,
        'adobeRSS': content['adobeRSS'] if 'adobeRSS' in content else None
    })

def get_time(content):
    starttime = None
    if 'date' in content and 'time' in content:
        now_time = time.localtime(time.time())
        year = time.strftime('%Y', now_time)
        # Correct no zero padding in the time hours
        time_part = content['time']
        if time_part.find(':') == 1:
            time_part = '0' + time_part
        starttime = time.strptime(year + ' ' + content['date'] + ' ' + time_part, '%Y %A, %B %d %I:%M %p')
    return starttime


def compare_contents(l, r):
    lnetwork = util.get_nested_value(l, ['streams', 0, 'source', 'id'])
    rnetwork = util.get_nested_value(r, ['streams', 0, 'source', 'id'])
    try:
        lnetwork_sort = NETWORK_ID_SORT_ORDER.index(lnetwork.lower())
    except:
        lnetwork_sort = 1000
    try:
        rnetwork_sort = NETWORK_ID_SORT_ORDER.index(rnetwork.lower())
    except:
        rnetwork_sort = 1000
    ltype = l['status'] if 'status' in l else 'clip'
    rtype = r['status'] if 'status' in r else 'clip'
    return compare(get_time(l), lnetwork_sort, ltype, get_time(r), rnetwork_sort, rtype)
