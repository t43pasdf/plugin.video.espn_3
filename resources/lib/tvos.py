
import json
import re
import time
import urllib
from datetime import datetime, timedelta

import xbmcplugin

import util
import player_config
import adobe_activate_api
from globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL
from addon_util import *
from register_mode import RegisterMode

TAG = 'TVOS: '
PLACE = 'tvos'
ROOT = ''

HOME = 'HOME'
SPORTS = 'SPORTS'
CHANNELS = 'CHANNELS'
BUCKET = 'BUCKET'

class TVOS:
    @RegisterMode(PLACE)
    def __init__(self):
        pass

    def make_mode(self, destination):
        return '/' + PLACE + '/' + destination

    @RegisterMode(ROOT)
    def root_menu(self, args):
        addDir('Home', dict(MODE=self.make_mode(HOME)), defaultlive)
        addDir('Channels', dict(MODE=self.make_mode(CHANNELS)), defaultlive)
        addDir('Sports', dict(MODE=self.make_mode(SPORTS)), defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(HOME)
    def home(self, args):
        selected_bucket = args.get(BUCKET, None)
        if selected_bucket is not None:
            selected_bucket = selected_bucket[0]
            xbmc.log(TAG + 'Looking at bucket %s' % selected_bucket)
        url = 'http://watch.product.api.espn.com/api/product/v1/tvos/watchespn/home'
        json_data = util.get_url_as_json_cache(url)
        buckets = json_data['page']['buckets']
        for bucket in buckets:
            if selected_bucket is not None:
                xbmc.log(TAG + 'Checking bucket %s' % bucket['id'])
                if str(bucket['id']) == selected_bucket:
                    xbmc.log(TAG + 'Found bucket')
                    for content in bucket['contents']:
                        fanart = content['imageHref']
                        infoLabels = {'title': content['name'],
                                      'duration': content['tracking']['duration'],
                                      'studio': content['source']}

                        authurl = dict()
                        authurl[EVENT_ID] = content['id']
                        authurl[SESSION_URL] = content['airings'][0]['videoHref']
                        authurl[MODE] = PLAY_TV_MODE if 'adobeRSS' in content else PLAY_ITEM_MODE
                        if 'adobeRSS' in content:
                            authurl[ADOBE_RSS] = content['adobeRSS']
                        addLink(content['name'].encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)

                        xbmcplugin.setContent(pluginhandle, 'episodes')
            else:
                addDir(bucket['name'], dict(BUCKET=bucket['id'], MODE=self.make_mode(HOME)), defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CHANNELS)
    def channels(self, args):
        pass

    @RegisterMode(SPORTS)
    def sports(self, args):
        pass
