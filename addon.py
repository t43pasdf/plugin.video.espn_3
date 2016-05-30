#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import base64
import json
import re
import time
import urllib
import urlparse
from datetime import datetime, timedelta


import xbmcgui
import xbmcplugin

from resources.lib import util
from resources.lib import player_config
from resources.lib import adobe_activate_api
from resources.lib.globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL
from resources.lib.constants import *
from resources.lib.addon_util import *

from resources.lib import legacy
from resources.lib import appletv

TAG = 'ESPN3: '


def PLAY_ITEM(args):
    url = args.get(PLAYBACK_URL)[0]
    item = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

base_url = sys.argv[0]
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get(MODE, None)

xbmc.log('ESPN3: args %s' % args, LOG_LEVEL)

refresh = False
if mode is not None and mode[0] == AUTHENTICATE_MODE:
    xbmc.log('Authenticate Device', LOG_LEVEL)
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
            adobe_activate_api.authenticate()
            dialog.ok(translation(30310), translation(30370))
        except urllib2.HTTPError as e:
            dialog.ok(translation(30037), translation(30420) % e)
    mode = None
    refresh = True
elif mode is not None and mode[0] == AUTHENTICATION_DETAILS_MODE:
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30380),
                      translation(30390) % adobe_activate_api.get_authentication_expires(),
                      nolabel = translation(30360),
                      yeslabel = translation(30430))
    if ok:
        adobe_activate_api.deauthorize()
    mode = None
    refresh = True

if mode == None:
    adobe_activate_api.clean_up_authorization_tokens()
    xbmc.log("Generate Main Menu", LOG_LEVEL)
    appletv.CATEGORIES_ATV(refresh)
elif mode[0] == CATEGORY_SHOWCASE_MODE:
    appletv.CATEGORIES_SHOWCASE(args)
elif mode[0] == LIVE_EVENTS_MODE:
    xbmc.log("Indexing Videos", LOG_LEVEL)
    legacy.INDEX(args)
elif mode[0] == LIST_SPORTS_MODE:
    xbmc.log("List sports", LOG_LEVEL)
    legacy.LISTSPORTS(args)
elif mode[0] == INDEX_SPORTS_MODE:
    xbmc.log("Index by sport", LOG_LEVEL)
    legacy.INDEX(args)
elif mode[0] == PLAY_MODE:
    legacy.PLAY_LEGACY_TV(args)
elif mode[0] == PLAY_ITEM_MODE:
    PLAY_ITEM(args)
elif mode[0] == PLAY_TV_MODE:
    PLAY_TV(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming", LOG_LEVEL)
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=False,updateListing=True)
elif mode[0] == CATEGORY_SHELF_MODE:
    appletv.CATEGORY_SHELF(args)
elif mode[0] == OLD_LISTING_MODE:
    xbmc.log("Old listing mode", LOG_LEVEL)
    legacy.CATEGORIES()
elif mode[0] == CATEGORY_SPORTS_MODE:
    appletv.CATEGORY_SPORTS(args)
elif mode[0] == CATEGORY_CHANNELS_MODE:
    appletv.CATEGORY_CHANNELS(args)
