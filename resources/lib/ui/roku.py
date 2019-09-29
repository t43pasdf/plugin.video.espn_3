from xbmcplugin import endOfDirectory, setContent

from resources.lib import adobe_activate_api
from resources.lib.addon_util import *
from resources.lib.item_indexer import *
from resources.lib.plugin_routing import *

ROOT = '/roku'
MIN_THUMBNAIL_WIDTH = 500

@plugin.route(ROOT)
def roku_root_menu():
    # Roku config
    url = base64.b64decode(
        'aHR0cDovL2Fzc2V0cy5lc3BuLmdvLmNvbS9wcm9kL2Fzc2V0cy93YXRjaGVzcG4vcm9rdS9jb25maWcuanNvbg==')
    json_data = util.get_url_as_json_cache(get_url(url))
    for group in json_data['config']['featured']['groups']:
        if group['visibility'] == 'not authenticated':
            # This represents the duplicate Browse by Sport
            continue
        extra = ''
        if group['visibility'] == 'authenticated':
            if not adobe_activate_api.is_authenticated():
                extra = '*'
        if len(group['contents']) > 1:
            extra += group['name'] + ' - '
        for content in group['contents']:
            addDirectoryItem(plugin.handle,
                             plugin.url_for(roku_url_mode, url=content['href']),
                             ListItem(extra + content['name']), True)
    endOfDirectory(plugin.handle)

def get_thumbnail(category):
    max_width = 0
    href = ''
    key = 'thumbnails'
    if 'thumbnails' not in category:
        key = 'images'
    if key in category:
        for thumbnail_key in category[key]:
            thumbnail = category[key][thumbnail_key]
            if 'slates' == thumbnail_key:
                return thumbnail['large']['href']
            width = thumbnail['width']
            if width >= MIN_THUMBNAIL_WIDTH:
                return thumbnail['href']
            elif width > max_width:
                max_width = width
                href = thumbnail['href']
    return href

@plugin.route(ROOT + '/url')
def roku_url_mode():
    url = arg_as_string('url')
    category_id = arg_as_string(ID)
    json_data = util.get_url_as_json_cache(get_url(url))
    if 'listings' in json_data:
        json_data['listings'].sort(cmp=compare_roku)
        for listing in json_data['listings']:
            index_listing(listing)
        setContent(plugin.handle, 'episodes')
    if 'videos' in json_data:
        for video in json_data['videos']:
            index_video(video)
        setContent(plugin.handle, 'episodes')
    if 'categories' in json_data:
        for category in json_data['categories']:
            if category_id is None or category_id == '':
                if 'api' in category['links'] and 'subcategories' not in category:
                    addDirectoryItem(plugin.handle,
                                     plugin.url_for(roku_url_mode, url=category['links']['api']['video']['href']),
                                     make_list_item(category['name'], get_thumbnail(category)), True)
                elif 'subcategories' in category:
                    # Collapse sub categories
                    for subcategory in category['subcategories']:
                        if 'api' in subcategory['links']:
                            addDirectoryItem(plugin.handle,
                                             plugin.url_for(roku_url_mode,
                                                            url=subcategory['links']['api']['video']['href']),
                                             make_list_item(category['name'] + ' - ' + subcategory['name'], get_thumbnail(category)), True)
            elif category_id == str(category['id']):
                if 'api' in category['links']:
                    addDirectoryItem(plugin.handle,
                                     plugin.url_for(roku_url_mode,
                                                    url=category['links']['api']['video']['href']),
                                     make_list_item(category['name'] + ' - Clips',
                                                    get_thumbnail(category)), True)
                if 'subcategories' in category:
                    for subcategory in category['subcategories']:
                        if 'api' in subcategory['links']:
                            addDirectoryItem(plugin.handle,
                                             plugin.url_for(roku_url_mode,
                                                            url=subcategory['links']['api']['video']['href']),
                                             make_list_item(subcategory['name'], get_thumbnail(category)), True)
    if 'clients' in json_data:
        for client in json_data['clients']:
            for channel in client['channels']:
                addDirectoryItem(plugin.handle,
                                 plugin.url_for(roku_url_mode,
                                                url=channel['links']['api']['listings']['href']),
                                 make_list_item(channel['name'], get_thumbnail(channel)), True)
    endOfDirectory(plugin.handle)


def get_time(listing):
    if 'startTime' in listing:
        time_format = '%Y-%m-%dT%H:%M:%S'
        return time.strptime(listing['startTime'][:-3], time_format)
    return None


def compare_roku(l, r):
    lnetwork = l['broadcasts'][0]['name'] if 'broadcasts' in l else None
    rnetwork = r['broadcasts'][0]['name'] if 'broadcasts' in r else None
    ltype = l['type']
    rtype = r['type']
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
