#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

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
from ui import tvos, appletv, legacy, roku
from ui.legacy import legacy_root_menu

TAG = 'ESPN3: '
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()

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
    current_time = time.strftime("%I:%M %p", time.localtime(time.time()))
    parse_json(WATCH_API_V3_WEB_HOME)

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

