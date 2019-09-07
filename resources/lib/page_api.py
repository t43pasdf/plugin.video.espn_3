import logging
import util
import time

from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, setContent, endOfDirectory

from plugin_routing import *
from addon_util import get_url, compare
from item_indexer import index_item

BUCKET = 'BUCKET'


@plugin.route('/page-api')
def page_api_url():
    url = arg_as_string('url')
    parse_json(url)
    endOfDirectory(plugin.handle)


@plugin.route('/page-api/buckets/<path:bucket_path>')
def page_api_buckets(bucket_path):
    url = arg_as_string('url')
    parse_json(url, bucket_path)
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
                addDirectoryItem(plugin.handle, plugin.url_for(page_api_buckets, bucket_path=bucket_path, url=url),
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
        #TODO: Blackout check
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
    lnetwork = l['source'] if 'source' in l else None
    rnetwork = r['source'] if 'source' in r else None
    ltype = l['status'] if 'status' in l else 'clip'
    rtype = r['status'] if 'status' in r else 'clip'
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
