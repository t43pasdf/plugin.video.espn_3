import urlparse

from xbmcplugin import addDirectoryItem, setContent, endOfDirectory

from item_indexer import index_item, get_item_listing_text
from play_routes import *
import espnplus

BUCKET = 'BUCKET'

def make_channel_id(id, name):
    return '%s' % (name)

@plugin.route('/page-api')
def page_api_url():
    url = arg_as_string('url')
    parse_json(url)
    endOfDirectory(plugin.handle)

@plugin.route('/page-api/bucket/<bucket_id>')
def page_api_url_bucket(bucket_id):
    url = arg_as_string('url')
    parse_json(url)
    endOfDirectory(plugin.handle)

@plugin.route('/page-api/channel')
def page_api_channel():
    url = arg_as_string('url')
    channel_id = arg_as_string('channel_id')
    parse_json(url, channel_id=channel_id)
    endOfDirectory(plugin.handle)


@plugin.route('/page-api/buckets/<path:bucket_path>')
def page_api_buckets(bucket_path):
    url = arg_as_string('url')
    bucket_url = arg_as_string('bucket_url')
    parse_json(bucket_url, bucket_path)
    endOfDirectory(plugin.handle)

def get_v3_url(url):
    components = urlparse.urlparse(url)
    current_qs = components.query
    if current_qs is None:
        current_qs = ''
    qs = urlparse.parse_qs(current_qs)
    # TODO: Add tz, features, zipcode
    entitlements = ','.join(espnplus.get_entitlements())
    logging.debug('QS: %s' % qs)
    qs['entitlements'] = entitlements
    qs['countryCode'] = 'US'
    qs['lang'] = 'en'
    qs['zipcode'] = player_config.get_zipcode()
    qs['tz'] = player_config.get_timezone_utc_offest()
    new_components = (components.scheme, components.netloc, components.path, components.params, urllib.urlencode(qs, doseq=True), components.fragment)
    return urlparse.urlunparse(new_components)

def parse_json(url, bucket_path=None, channel_id=None):
    logging.debug('Looking at url %s %s' % (url, bucket_path))
    selected_bucket = bucket_path
    if selected_bucket is not None:
        selected_bucket = selected_bucket.split('/')
        logging.debug('Looking at bucket %s' % selected_bucket)
    json_data = util.get_url_as_json_cache(get_v3_url(url))
    buckets = []
    header_bucket = None
    if 'header' in json_data['page'] and 'bucket' in json_data['page']['header']:
        description = util.get_nested_value(json_data, ['page', 'header', 'description'])
        subtitle = util.get_nested_value(json_data, ['page', 'header', 'subtitle'])
        director = util.get_nested_value(json_data, ['page', 'header', 'director'])
        plot = '%s\n%s\n%s\n' % (subtitle, description, director)
        header_bucket = json_data['page']['header']['bucket']
        header_bucket['contents'][0]['plot'] = plot
    if 'buckets' in json_data['page']:
        buckets = buckets + json_data['page']['buckets']
    was_search = 'name' in json_data['page'] and json_data['page']['name'] == 'Suggestions'
    process_buckets(url, header_bucket, buckets, selected_bucket, list(), channel_filter=channel_id, was_search=was_search)


def process_buckets(url, header_bucket, buckets, selected_buckets, current_bucket_path, channel_filter=None, was_search=False):
    selected_bucket = None if selected_buckets is None or len(selected_buckets) == 0 else selected_buckets[0]
    logging.debug('Selected buckets: %s Current Path: %s' % (selected_buckets, current_bucket_path))
    original_bucket_path = current_bucket_path
    if header_bucket is not None and selected_bucket is None:
        index_bucket_content(url, header_bucket, channel_filter)
    for bucket in buckets:
        current_bucket_path = list(original_bucket_path)
        current_bucket_path.append(str(bucket['id']))
        if selected_bucket is not None and str(bucket['id']) != selected_bucket:
            continue
        if ('contents' in bucket or 'buckets' in bucket) and selected_bucket is None and len(buckets) > 1:
            if bucket.get('type', '') != 'images':
                bucket_path = '/'.join(current_bucket_path)
                if 'links' in bucket and 'self' in bucket['links'] and not was_search:
                    bucket_url = bucket['links']['self']
                    # bucket_path shouldn't be needed because we are using the full url to it
                    addDirectoryItem(plugin.handle, plugin.url_for(page_api_url_bucket, bucket_id=bucket['id'], url=bucket_url),
                                     ListItem(bucket['name']), True)
                else:
                    # The items are listed directly in the bucket, not in a sub-url, so use the bucket_path
                    addDirectoryItem(plugin.handle, plugin.url_for(page_api_buckets, bucket_path=bucket_path, url=url,
                                                                   bucket_url=url),
                                     ListItem(bucket['name']), True)
        else:
            logging.debug('Processing bucket %s' % bucket['id'])
            if 'buckets' in bucket:
                if selected_buckets is not None and len(selected_buckets) > 0:
                    process_buckets(url, None, bucket['buckets'], selected_buckets[1:], current_bucket_path)
                else:
                    process_buckets(url, None, bucket['buckets'], list(), current_bucket_path)
            else:
                index_bucket_content(url, bucket, channel_filter)

def index_bucket_content(url, bucket, channel_filter):
    if 'contents' in bucket:
        bucket['contents'].sort(cmp=compare_contents)
        grouped_events = dict()
        source_id_data = dict()
        content_indexed = 0
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
                setContent(plugin.handle, 'episodes')
                source_id = util.get_nested_value(content, ['streams', 0, 'source', 'id'])
                source_name = util.get_nested_value(content, ['streams', 0, 'source', 'name'])
                channel_id = make_channel_id(source_id, source_name)
                if channel_filter is None:
                    source_type = util.get_nested_value(content, ['streams', 0, 'source', 'type'])
                    if source_type == 'online':
                        if channel_id not in grouped_events:
                            grouped_events[channel_id] = []
                        grouped_events[channel_id].append(content)
                        source_id_data[channel_id] = {'name': source_name, 'id': source_id}
                    else:
                        index_content(content)
                        content_indexed = content_indexed + 1
                elif channel_filter == channel_id:
                    index_content(content)
                    content_indexed = content_indexed + 1

        # Handle grouped contents
        group_source_ids = list(grouped_events.keys())
        group_source_ids.sort(cmp=compare_network_ids)
        for group_source_id in group_source_ids:
            contents = grouped_events[group_source_id]
            source_data = source_id_data[group_source_id]
            # Index the content directly if he haven't indexed a lot of things
            if content_indexed <= 3:
                for content in contents:
                    index_content(content)
            else:
                name = source_data['name']
                id = source_data['id']
                if len(name) == 0 and id == 'ESPN_PPV':
                    name = 'ESPN+ PPV'
                elif len(name) == 0:
                    name = id
                addDirectoryItem(plugin.handle, plugin.url_for(page_api_channel, channel_id=group_source_id, url=url),
                                 ListItem(name), True)


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


def index_v3_content(content):
    logging.debug('Indexing %s' % content)
    type = content['type']
    if type == 'show'or type == 'film' or type == 'product':
        index_v3_show(content)
        return
    if type == 'vod':
        index_v3_vod(content)
        return
    
    status = content['status']

    subtitle = content.get('subtitle', '')
    plot = subtitle
    if 'event' in content:
        event = content['event']
        if event['type'] == 'tvt':
            plot = '%s\n%s vs. %s\n%s - %s\n%s%s' % \
                   (subtitle,
                    get_team_name(event, 'One'),
                    get_team_name(event, 'Two'),
                    event['teamOneScore'], event['teamTwoScore'],
                    get_possesion_text(event),
                    event['statusTextOne'])
    if 'plot' in content:
        plot = content['plot']

    starttime = get_time(content)
    if 'date' in content and 'time' in content:
        #  TODO: Include duration in plot
        plot = content['date'] + ' ' + content['time'] + '\n' + plot

    event_id = content['eventId'] if 'eventId' in content else content['id']

    more_than_one_stream = len(content['streams']) > 1
    for stream in content['streams']:
        if 'duration' in stream:
            duration = parse_duration(stream['duration'])
            duration_seconds = duration.tm_hour * 3600 + duration.tm_min * 60 + duration.tm_sec
        else:
            duration_seconds = 0

        name = content['name']
        if more_than_one_stream:
            name = name + ' - ' + stream['name']

        entitlements = espnplus.get_entitlements()
        packages = util.get_nested_value(stream, ['packages'], [])
        has_entitlement = is_entitled(packages, entitlements)
        ename, length = get_item_listing_text(name, starttime, duration_seconds, content['status'],
                                      stream['source']['name'], 'blackoutText' in content,
                                      stream['authTypes'], requires_package=not has_entitlement)

        source_name = util.get_nested_value(content, ['stream', 0, 'source', 'name'])

        fanart = util.get_nested_value(content, ['imageHref'])


        infoLabels = {'title': ename,
                      'genre': subtitle,
                      'duration': length,
                      'studio': source_name,
                      'plot': plot}

        if status == 'upcoming':
            starttime_text = time.strftime("%m/%d/%Y %I:%M %p", starttime)
            addDirectoryItem(plugin.handle,
                             plugin.url_for(upcoming_event, event_id=event_id,
                                            event_name=urllib.quote_plus(name.encode('utf-8')), starttime=starttime_text,
                                            packages='|'.join(packages)),
                             make_list_item(ename, infoLabels=infoLabels))
        else:
            addDirectoryItem(plugin.handle,
                             plugin.url_for(play_event, event_id=event_id,
                                            event_url=stream['links']['play'],
                                            auth_types='|'.join(stream['authTypes'])),
                             make_list_item(ename, infoLabels=infoLabels, icon=fanart))

# {
# "id": "d2ecb4c1-8fd1-4008-906d-e066e5170cd0",
# "name": "Indianapolis 500 On Demand",
# "type": "show",
# "imageFormat": "5x2",
# "size": "md",
# "imageHref": "http://s.espncdn.com/stitcher/artwork/5x2.jpg?width=400&source=https://artwork.espncdn.com/series/d2ecb4c1-8fd1-4008-906d-e066e5170cd0/5x2/960x384_201804161812.jpg&cb=12&showBadge=true&package=ESPN_PLUS",
# "links": {
#     "self": "https://watch.product.api.espn.com/api/product/v3/watchespn/web/series/d2ecb4c1-8fd1-4008-906d-e066e5170cd0?tz=America%2FPuerto_Rico&lang=en",
#     "web": "http://www.espn.com/watch/series/d2ecb4c1-8fd1-4008-906d-e066e5170cd0/indianapolis-500-on-demand",
#     "shareUrl": "http://www.espn.com/watch/series/d2ecb4c1-8fd1-4008-906d-e066e5170cd0/indianapolis-500-on-demand"
#     }
# },
def index_v3_show(content):
    content_url = content['links']['self']
    name = content['name']
    fanart = content['imageHref']
    addDirectoryItem(plugin.handle, plugin.url_for(page_api_url, url=content_url),
                     ListItem(name, iconImage=fanart), True)

def index_v3_vod(content):
    plot = content.get('description', '')

    event_id = content['eventId'] if 'eventId' in content else content['id']

    more_than_one_stream = len(content['streams']) > 1
    for stream in content['streams']:
        duration = parse_duration(stream['duration'])
        duration_seconds = duration.tm_hour * 3600 + duration.tm_min * 60 + duration.tm_sec

        name = content['name']
        if more_than_one_stream:
            name = name + ' - ' + stream['name']

        ename, length = get_item_listing_text(name, None, duration_seconds, None,
                                              '', 'blackoutText' in content,
                                              [])

        source_name = util.get_nested_value(content, ['stream', 0, 'source', 'name'])

        fanart = util.get_nested_value(content, ['imageHref'])

        infoLabels = {'title': ename,
                      'duration': length,
                      'studio': source_name,
                      'plot': plot}

        addDirectoryItem(plugin.handle,
                         plugin.url_for(play_vod, event_id=event_id,
                                        url=stream['links']['play']),
                         make_list_item(ename, infoLabels=infoLabels, icon=fanart))


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

def compare_network_ids(l, r):
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
    return lnetwork_sort - rnetwork_sort
