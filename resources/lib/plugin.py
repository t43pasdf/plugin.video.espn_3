#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import json
import urllib2
import urlparse
import m3u8

import xbmcaddon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory


import logging

import legacy

from plugin_routing import *
from resources.lib import appletv
from resources.lib import events
from resources.lib import roku
from resources.lib import tvos
from resources.lib.addon_util import *
from resources.lib.globals import defaultlive, defaultreplay, UA_PC
from resources.lib import kodilogging
import adobe_activate_api
from resources.lib.legacy import legacy_root_menu
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
        addDir('[COLOR=FFFF0000]' + translation(30300) + '[/COLOR]',
               dict(MODE=AUTHENTICATE_MODE),
               defaultreplay)
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
    # if selfAddon.getSetting('ShowAppleTVMenu') == 'true':
    #     addDir(translation(30730),
    #            dict(MODE='/appletv/'),
    #            defaultlive)
    if get_setting_as_bool('ShowLegacyMenu'):
        addDirectoryItem(plugin.handle, plugin.url_for(legacy_root_menu),
                         ListItem(translation(30740)), True)
    # if selfAddon.getSetting('ShowRokuMenu') == 'true':
    #     addDir(translation(30760),
    #            dict(MODE='/roku/'),
    #            defaultlive)
    # if selfAddon.getSetting('ShowTVOSMenu') == 'true':
    #     addDirectoryItem(plugin.handle, translation(30750),
    #            dict(MODE='/tvos/'),
    #            defaultlive)
    if adobe_activate_api.is_authenticated():
        addDirectoryItem(plugin.handle,
           plugin.url_for(authentication_details),
           ListItem('[COLOR=FF00FF00]' + translation(30380) + '[/COLOR]'))
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
    plugin.run('/?refresh')


@plugin.route('/authentication-details')
def authentication_details():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30380),
                      translation(30390) % adobe_activate_api.get_authentication_expires(),
                      translation(30700) % (player_config.get_dma(), player_config.get_timezone()),
                      translation(30710) % (player_config.get_can_sso(), player_config.get_sso_abuse()),
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
