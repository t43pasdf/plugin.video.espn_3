# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time

import xbmcaddon
from xbmcplugin import addDirectoryItem, endOfDirectory

import adobe_activate_api
import settings_file
from page_api import page_api_url, parse_json, get_v3_url
from plugin_routing import *
from resources.lib import events
from resources.lib import kodilogging
from resources.lib.addon_util import *
from resources.lib.settings_file import SettingsFile
from ui import tvos, appletv, legacy, roku
from ui.legacy import legacy_root_menu

TAG = 'ESPN3: '
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()

class SearchSettings(SettingsFile):
    def __init__(self):
        SettingsFile.__init__(self, 'search.json')
        self.max_search_history_items = 20
        self.load_config()

    def load_config(self):
        self.in_search_results = self.settings.get('inSearchResults', False)
        self.last_search_url = self.settings.get('lastSearchResultsUrl', '')
        self.search_history = self.settings.get('searchHistory', [])

    def set_in_search_results(self):
        self.settings['inSearchResults'] = True
        self.load_config()

    def set_not_in_search_results(self):
        self.settings['inSearchResults'] = False
        self.load_config()

    def set_last_search_query(self, query):
        self.settings['lastSearchResultsUrl'] = query
        if len(query) <= 0:
            self.set_not_in_search_results()
        self.load_config()

    def add_search_history(self, query):
        self.search_history.insert(0, query)
        if len(self.search_history) > self.max_search_history_items:
            self.search_history = self.search_history[0:self.max_search_history_items]
        self.settings['searchHistory'] = self.search_history
        self.load_config()

    def clear_search_history(self):
        self.settings['searchHistory'] = []
        self.load_config()

search_settings = SearchSettings()

def handle_search(search_query):
    networks = 'espn1,espn2,espnu,espnews,espndeportes,sec,longhorn,buzzerbeater,goalline,espn3,espnclassic,acc'
    search_url = 'https://watch-search.espn.com/api/product/v3/watchespn/web/suggest?q=%s&size=20&authNetworks=%s&includeDtcContent=true' % (
    search_query, networks)
    search_settings.set_last_search_query(search_url)
    parse_json(search_url)
    endOfDirectory(plugin.handle, succeeded=True, cacheToDisc=False)


@plugin.route('/search/clear-history')
def clear_search_history():
    search_settings.clear_search_history()
    xbmcgui.Dialog().ok(translation(40520), translation(40521))

@plugin.route('/search/results')
def search_results():
    search_query = arg_as_string('q')
    handle_search(search_query)

@plugin.route('/search/input')
def search_input():
    if search_settings.in_search_results:
        search_query = search_settings.last_search_url
    else:
        dialog = xbmcgui.Dialog()
        search_query = dialog.input(translation(40510), type=xbmcgui.INPUT_ALPHANUM)
        if len(search_query) > 0:
            search_settings.add_search_history(search_query)
    if len(search_query) > 0:
        search_settings.set_in_search_results()
        handle_search(search_query)

@plugin.route('/search')
def search():
    search_settings.set_last_search_query('')
    addDirectoryItem(plugin.handle, plugin.url_for(search_input),
                     ListItem('[B]%s[/B]' % translation(40501)), True)
    for search_history in search_settings.search_history:
        addDirectoryItem(plugin.handle, plugin.url_for(search_results, q=search_history),
                         ListItem(search_history), True)
    endOfDirectory(plugin.handle, succeeded=True)

@plugin.route('/')
def new_index():
    # New index will have the channels listed and then the buckets from the watch
    # web product
    refresh = arg_as_bool('refresh')
    clear_cache = arg_as_bool('clear-cache')
    try:
        adobe_activate_api.clean_up_authorization_tokens()
    except:
        logger.debug('Unable to clean up authoorization tokens')
        adobe_activate_api.reset_settings()
    if clear_cache:
        util.clear_cache(get_v3_url(WATCH_API_V3_LIVE))
        util.clear_cache(get_v3_url(WATCH_API_V3_WEB_HOME))

    parse_json(WATCH_API_V3_LIVE)
    addDirectoryItem(plugin.handle, plugin.url_for(search),
                     ListItem(translation(40500)), True)
    parse_json(WATCH_API_V3_WEB_HOME)

    current_time = time.strftime("%I:%M %p", time.localtime(time.time()))
    addDirectoryItem(plugin.handle, plugin.url_for(new_index, refresh=True),
                     ListItem(translation(30850) % current_time), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(index),
                     ListItem('Old Index'), True)

    endOfDirectory(plugin.handle, succeeded=True, updateListing=refresh, cacheToDisc=False)


@plugin.route('/old-index')
def index():
    refresh = arg_as_bool('refresh')
    clear_cache = arg_as_bool('clear-cache')
    try:
        adobe_activate_api.clean_up_authorization_tokens()
    except:
        logger.debug('Unable to clean up authoorization tokens')
        adobe_activate_api.reset_settings()
    if clear_cache:
        include_premium = adobe_activate_api.is_authenticated()
        channel_list = events.get_channel_list(include_premium)
        util.clear_cache(events.get_live_events_url(channel_list))

    current_time = time.strftime("%I:%M %p", time.localtime(time.time()))
    addDirectoryItem(plugin.handle, plugin.url_for(index, refresh=True),
                     ListItem(translation(30850) % current_time), True)
    include_premium = adobe_activate_api.is_authenticated()
    channel_list = events.get_channel_list(include_premium)
    espn_url = events.get_live_events_url(channel_list)
    legacy.index_legacy_live_events(espn_url)
    if get_setting_as_bool('ShowAndroidTVMenu'):
        url = base64.b64decode(
            'aHR0cHM6Ly93YXRjaC5wcm9kdWN0LmFwaS5lc3BuLmNvbS9hcGkvcHJvZHVjdC92MS9hbmRyb2lkL3R2L2hvbWU=')
        addDirectoryItem(plugin.handle, plugin.url_for(page_api_url, url=url),
                         ListItem(translation(30780)), True)
    if get_setting_as_bool('ShowAppleTVMenu'):
        addDirectoryItem(plugin.handle, plugin.url_for(appletv.appletv_root_menu),
                         ListItem(translation(30730)), True)
    if get_setting_as_bool('ShowLegacyMenu'):
        addDirectoryItem(plugin.handle, plugin.url_for(legacy_root_menu),
                         ListItem(translation(30740)), True)
    if get_setting_as_bool('ShowRokuMenu'):
        addDirectoryItem(plugin.handle, plugin.url_for(roku.roku_root_menu),
                         ListItem(translation(30760)), True)
    if get_setting_as_bool('ShowTVOSMenu'):
        addDirectoryItem(plugin.handle,
                         plugin.url_for(tvos.tvos_root_menu),
                         ListItem(translation(30750)), True)
    endOfDirectory(plugin.handle, updateListing=refresh, cacheToDisc=False)



# if mode is None:
#
#     xbmc.log("Generate Main Menu", xbmc.LOGDEBUG)
#     try:
#         index(refresh)
#     except IOError as exception:
#         xbmc.log('SSL certificate failure %s' % exception, xbmc.LOGDEBUG)
#         xbmc.log('%s-%s-%s' % (exception.errno, exception.message, exception.strerror), xbmc.LOGDEBUG)
#         if '[SSL: CERTIFICATE_VERIFY_FAILED]' in str(exception.strerror):
#             dialog = xbmcgui.Dialog()
#             ok = dialog.yesno(translation(30037), translation(30910))
#             if ok:
#                 selfAddon.setSetting('DisableSSL', 'true')
#                 index(refresh)
#             else:
#                 raise exception
#         else:
#             raise exception

def run():
    plugin.run()
    settings_file.save_settings()

