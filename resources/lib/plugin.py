#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import urllib2

import xbmcaddon
from xbmcplugin import addDirectoryItem, endOfDirectory

from plugin_routing import *
from resources.lib import events
from ui import tvos, appletv, legacy, roku
from resources.lib.addon_util import *
from resources.lib import kodilogging
import adobe_activate_api
from ui.legacy import legacy_root_menu
from page_api import page_api_url


TAG = 'ESPN3: '
ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()


@plugin.route('/')
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
    if not adobe_activate_api.is_authenticated():
        addDirectoryItem(plugin.handle,
                         plugin.url_for(authenticate),
                         ListItem('[COLOR=FFFF0000]' + translation(30300) + '[/COLOR]'))
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
    if adobe_activate_api.is_authenticated():
        addDirectoryItem(plugin.handle,
           plugin.url_for(authentication_details),
           ListItem(translation(30380)))
    endOfDirectory(plugin.handle, updateListing=refresh, cacheToDisc=False)


@plugin.route('/authenticate')
def authenticate():
    logger.debug('Authenticate Device')
    if adobe_activate_api.is_authenticated():
        logger.debug('Device already authenticated, skipping authentication')
    else:
        regcode = adobe_activate_api.get_regcode()
        dialog = xbmcgui.Dialog()
        ok = dialog.yesno(translation(30310),
                          translation(30320),
                          translation(30330) % regcode,
                          translation(30340),
                          translation(30360),
                          translation(30350))
        if ok:
            try:
                adobe_activate_api.authenticate(regcode)
                dialog.ok(translation(30310), translation(30370))
            except urllib2.HTTPError as e:
                dialog.ok(translation(30037), translation(30420) % e)
    plugin.run('/?refresh=True&clear-cache=True')


@plugin.route('/authentication-details')
def authentication_details():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30380),
                      translation(30390) % adobe_activate_api.get_authentication_expires(),
                      translation(30700) % (player_config.get_dma(), player_config.get_timezone()),
                      nolabel=translation(30360),
                      yeslabel=translation(30430))
    if ok:
        adobe_activate_api.deauthorize()
    plugin.run('/?refresh')


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
