# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from xbmcplugin import setContent

from resources.lib.item_indexer import *
from resources.lib.plugin import *

ROOT = '/appletv'

@plugin.route(ROOT)
def appletv_root_menu():
    trending_mode()
    addDirectoryItem(plugin.handle,
                     plugin.url_for(appletv_featured),
                     make_list_item(get_string(30680)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(appletv_sports),
                     make_list_item(get_string(30550)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(appletv_channels),
                     make_list_item(get_string(30560)), True)
    endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/featured')
def appletv_featured():
    et = util.get_url_as_xml_cache(get_url(APPLE_TV_FEATURED))
    for showcase in et.findall('.//showcase/items/showcasePoster'):
        name = showcase.get('accessibilityLabel')
        image = showcase.find('./image').get('src')
        url = util.parse_url_from_method(showcase.get('onPlay'))
        addDirectoryItem(plugin.handle,
                         plugin.url_for(appletv_showcase, url=url),
                         make_list_item(name, image), True)
    collections = et.findall('.//collectionDivider')
    shelfs = et.findall('.//shelf')
    for i in range(0, len(collections)):
        collection_divider = collections[i]
        shelf = shelfs[i]
        title = collection_divider.find('title').text
        name = shelf.get('id')
        addDirectoryItem(plugin.handle,
                         plugin.url_for(appletv_shelf, shelf_id=name),
                         make_list_item(title), True)
    endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/showcase')
def appletv_showcase():
    url = arg_as_string('url')
    selected_nav_id = arg_as_string('nav_id')
    et = util.get_url_as_xml_cache(get_url(url))
    navigation_items = et.findall('.//navigation/navigationItem')
    logging.debug('Found %s items' % len(navigation_items))
    if selected_nav_id is '' and len(navigation_items) > 0:
        for navigation_item in navigation_items:
            name = navigation_item.find('./title').text
            nav_id = navigation_item.get('id')
            menu_item = navigation_item.find('.//twoLineMenuItem')
            if menu_item is None:
                menu_item = navigation_item.find('.//twoLineEnhancedMenuItem')
            if menu_item is not None and not menu_item.get('id') == 'no-event':
                addDirectoryItem(plugin.handle,
                                 plugin.url_for(appletv_showcase, url=url, nav_id=nav_id),
                                 make_list_item(name), True)
    elif len(navigation_items) > 0:
        for navigation_item in navigation_items:
            if str(navigation_item.get('id')) == selected_nav_id:
                logging.debug('Found nav item %s' % selected_nav_id)
                process_item_list(navigation_item.findall('.//twoLineMenuItem'))
                process_item_list(navigation_item.findall('.//twoLineEnhancedMenuItem'))
                setContent(plugin.handle, 'episodes')
    else: # If there are no navigation items then just dump all of the menu entries
        logging.debug('Dumping all menu items')
        process_item_list(et.findall('.//twoLineMenuItem'))
        process_item_list(et.findall('.//twoLineEnhancedMenuItem'))
        setContent(plugin.handle, 'episodes')
    endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/shelf/<shelf_id>')
def appletv_shelf(shelf_id):
    et = util.get_url_as_xml_cache(get_url(APPLE_TV_FEATURED))
    for shelf in et.findall('.//shelf'):
        name = shelf.get('id')
        if name == shelf_id:
            process_item_list(shelf.findall('.//sixteenByNinePoster'))
    setContent(plugin.handle, 'episodes')
    endOfDirectory(plugin.handle)

@plugin.route(ROOT + '/sports')
def appletv_sports():
    et = util.get_url_as_xml_cache(get_url(APPLE_TV_SPORTS))
    images = et.findall('.//image')
    sports = et.findall('.//oneLineMenuItem')
    for i in range(0, min(len(images), len(sports))):
        sport = sports[i]
        image = images[i]
        name = sport.get('accessibilityLabel')
        image = image.text
        url = util.parse_url_from_method(sport.get('onSelect'))
        addDirectoryItem(plugin.handle,
                         plugin.url_for(appletv_showcase, url=url),
                         make_list_item(name, image), True)
    endOfDirectory(plugin.handle, updateListing=False)

@plugin.route(ROOT + '/channels')
def appletv_channels():
    et = util.get_url_as_xml_cache(get_url(APPLE_TV_CHANNELS))
    for channel in et.findall('.//oneLineMenuItem'):
        name = channel.get('accessibilityLabel')
        image = channel.find('.//image').text
        url = util.parse_url_from_method(channel.get('onSelect'))
        addDirectoryItem(plugin.handle,
                         plugin.url_for(appletv_showcase, url=url),
                         make_list_item(name, image), True)
    setContent(plugin.handle, 'episodes')
    endOfDirectory(plugin.handle, updateListing=False)

def trending_mode():
    json_data = util.get_url_as_json_cache(get_url(WATCH_API_V1_TRENDING))
    for listing in json_data['listings']:
        index_listing(listing)
    for video in json_data['videos']:
        index_video(video)

# Items can play as is and do not need authentication
def index_item_shelf(stash_json):
    description = stash_json['description']
    item = stash_json['internal_item']
    description = description + '\n\n' + get_metadata(item)

    index_item({
        'sport': stash_json['sportName'],
        'eventName': stash_json['name'],
        'imageHref': stash_json['imageHref'],
        'duration': int(stash_json['duration']),
        'description': description,
        'sessionUrl': stash_json['playbackUrl'],
        'type': 'live'
    })

def index_tv_shelf(stash_json, upcoming):
    if 'description' in stash_json:
        description = stash_json['description']
    else:
        description = ''
    item = stash_json['internal_item']
    description = description + '\n\n' + get_metadata(item)

    index_item({
        'sport': stash_json['categoryName'],
        'eventName': stash_json['name'],
        'subcategory': stash_json['subcategoryName'],
        'imageHref':stash_json['imageHref'],
        'parentalRating':stash_json['parentalRating'],
        'starttime' : time.localtime(int(stash_json['startTime']) / 1000),
        'duration': int(stash_json['duration']),
        'type' : stash_json['type'],
        'networkId' : stash_json['network'],
        'blackout' : check_blackout(item),
        'description' : description,
        'eventId' : stash_json['eventId'] if stash_json['eventId'] != '' else stash_json['id'],
        'sessionUrl': stash_json['sessionUrl'],
        'guid': stash_json['guid'],
        'channelResourceId': stash_json['channelResourceId']
    })

def process_item_list(item_list):
    stashes = list()
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
                    menu_label = get_string(30570)
                url = method_info[3]
                nav_id = method_info[2]
                url = url + '&navigationItemId=' + nav_id
                logging.debug('Load more url %s' % url)
                addDirectoryItem(plugin.handle,
                                 plugin.url_for(appletv_showcase, url=url),
                                 make_list_item(menu_label), True)
        elif not item.get('id') == 'no-event':
            if stash_element is None:
                # Assume goes to another onPlay with a url
                name = item.get('accessibilityLabel')
                image = item.find('./image').get('src')
                url = util.parse_url_from_method(item.get('onPlay'))
                addDirectoryItem(plugin.handle,
                                 plugin.url_for(appletv_showcase, url=url),
                                 make_list_item(name, image), True)
            else:
                stash = stash_element.text.encode('ISO-8859-1')
                # Some of the json is baddly formatted
                stash = re.sub(r'\s+"', '"', stash)
                stash_json = json.loads(stash) #, 'utf-8')
                stash_json['internal_item'] = item
                stashes.append(stash_json)

    logging.debug('sorting %s items' % len(stashes))
    stashes.sort(cmp=compare_appletv)
    for stash_json in stashes:
        if stash_json['type'] == 'upcoming':
            index_tv_shelf(stash_json, True)
        elif 'sessionUrl' in stash_json:
            index_tv_shelf(stash_json, False)
        else:
            index_item_shelf(stash_json)

def get_metadata(item):
    metadata_keys_element = item.find('.//metadataKeys')
    metadata_values_element = item.find('.//metadataValues')
    description = ''
    if metadata_keys_element is not None and metadata_values_element is not None:
        key_labels = metadata_keys_element.findall('.//label')
        value_labels = metadata_values_element.findall('.//label')
        for i in range(0, min(len(key_labels), len(value_labels))):
            if value_labels[i].text is not None:
                description += '%s: %s\n' % (key_labels[i].text, value_labels[i].text)
    return description

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

def get_time(listing):
    return time.localtime(int(listing['startTime']) / 1000) if 'startTime' in listing else None

def compare_appletv(l, r):
    lnetwork = l['network'] if 'network' in l else None
    rnetwork = r['network'] if 'network' in r else None
    ltype = l['type'] if 'type' in l else 'clip'
    rtype = r['type'] if 'type' in r else 'clip'
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
