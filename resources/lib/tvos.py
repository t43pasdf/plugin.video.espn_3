
import json
import re
import time
import urllib
from datetime import datetime, timedelta
import base64

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
URL_MODE = 'URL_MODE'
URL = 'URL'

class TVOS:
    @RegisterMode(PLACE)
    def __init__(self):
        pass

    def make_mode(self, destination):
        return '/' + PLACE + '/' + destination

    @RegisterMode(ROOT)
    def root_menu(self, args):
        url = base64.b64decode(
            'aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
        self.parse_json(args, url)

        addDir(translation(30550), dict(MODE=self.make_mode(SPORTS)), defaultlive)
        addDir(translation(30560), dict(MODE=self.make_mode(CHANNELS)), defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(HOME)
    def home(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CHANNELS)
    def channels(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2NoYW5uZWxz')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(SPORTS)
    def sports(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL3Nwb3J0cw==')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(URL_MODE)
    def url_mode(self, args):
        url = args.get(URL)[0]
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    def process_buckets(self, url, buckets, selected_buckets, current_bucket_path):
        selected_bucket = None if selected_buckets is None or len(selected_buckets) == 0 else selected_buckets[0]
        xbmc.log(TAG + 'Selected buckets: %s Current Path: %s' % (selected_buckets, current_bucket_path), LOG_LEVEL)
        original_bucket_path = current_bucket_path
        for bucket in buckets:
            current_bucket_path = list(original_bucket_path)
            current_bucket_path.append(str(bucket['id']))
            if selected_bucket is not None and str(bucket['id']) != selected_bucket:
                continue
            if ('contents' in bucket or 'buckets' in bucket) and selected_bucket is None and len(buckets) > 1:
                if bucket['type'] != 'images':
                    bucket_path = '/'.join(current_bucket_path)
                    addDir(bucket['name'],
                           dict(URL=url, MODE=self.make_mode(URL_MODE), BUCKET=bucket_path), defaultlive)
            else:
                if 'buckets' in bucket:
                    if selected_buckets is not None and len(selected_buckets) > 0:
                        self.process_buckets(url, bucket['buckets'], selected_buckets[1:], current_bucket_path)
                    else:
                        self.process_buckets(url, bucket['buckets'], list(), current_bucket_path)
                else:
                    if 'contents' in bucket:
                        for content in bucket['contents']:
                            content_type = content['type']
                            if content_type == 'network' or content_type == 'subcategory' or content_type == 'category':
                                content_url = content['links']['self']
                                if 'imageHref' in content:
                                    fanart = content['imageHref']
                                else:
                                    fanart = defaultfanart
                                addDir(content['name'], dict(URL=content_url, MODE=self.make_mode(URL_MODE)), fanart)
                            else:
                                self.index_content(content)
                                xbmcplugin.setContent(pluginhandle, 'episodes')

    def parse_json(self, args, url):
        xbmc.log(TAG + 'Looking at url %s' % url, LOG_LEVEL)
        selected_bucket = args.get(BUCKET, None)
        if selected_bucket is not None:
            selected_bucket = selected_bucket[0].split('/')
            xbmc.log(TAG + 'Looking at bucket %s' % selected_bucket, LOG_LEVEL)
        json_data = util.get_url_as_json_cache(get_url(url))
        if 'buckets' in json_data['page']:
            buckets = json_data['page']['buckets']
            self.process_buckets(url, buckets, selected_bucket, list())

    def index_content(self, content):
        status = content['status'] if 'status' in content else 'live'
        sport = content['tracking']['sport']
        ename = content['name']
        sport2 = content['subtitle'] if 'subtitle' in content else sport
        if sport <> sport2:
            sport += ' (' + sport2 + ')'
        fanart = content['imageHref']

        duration = 0
        if 'tracking' in content and 'duration' in content['tracking']:
            duration = int(content['tracking']['duration'])

        starttime = None
        if 'date' in content and 'time' in content:
            now_time = time.localtime(time.time())
            year = time.strftime('%Y', now_time)
            # Correct no zero padding in the time hours
            time_part = content['time']
            if time_part.find(':') == 1:
                time_part = '0' + time_part
            starttime = time.strptime(year + ' ' + content['date'] + ' ' + time_part, '%Y %A, %B %d %I:%M %p')
        xbmc.log(TAG + 'startime %s' % starttime, LOG_LEVEL)
        if starttime is not None:
            now = time.time()
            etime = time.strftime("%I:%M %p", starttime)
            if status == 'replay':
                etime_local = starttime
                if etime_local.tm_hour == 0 and etime_local.tm_min == 0:
                    etime = time.strftime("%m/%d/%Y", starttime)
                else:
                    etime = time.strftime("%m/%d %I:%M %p", starttime)
                ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
            elif status == 'live':
                starttime_time = time.mktime(starttime)
                duration = duration - (time.time() - starttime_time)
                ename += ' [COLOR=FFB700EB]' + etime + '[/COLOR]'
            else:
                now_time = time.localtime(now)
                if now_time.tm_year == starttime.tm_year and \
                                now_time.tm_mon == starttime.tm_mon and \
                                now_time.tm_mday == starttime.tm_mday:
                    etime = time.strftime("%I:%M %p", starttime)
                else:
                    etime = time.strftime("%m/%d %I:%M %p", starttime)
                ename = '[COLOR=FFB700EB]' + etime + '[/COLOR] ' + ename
            aired = time.strftime("%Y-%m-%d", starttime)
        else:
            aired = 0

        network = content['tracking']['network'] if 'network' in content['tracking'] else ''
        network_name = content['source']
        if network == 'longhorn':
            channel_color = 'BF5700'
        elif network == 'sec' or network == 'secplus':
            channel_color = '004C8D'
        else:
            channel_color = 'CC0000'
        # TODO: Blackout check
        blackout = False
        blackout_text = ''
        if blackout:
            blackout_text = translation(30580)
        if network_name != '':
            ename = '[COLOR=FF%s]%s[/COLOR] %s %s' % (channel_color, network_name, blackout_text, ename)

        if 'date' in content and 'time' in content:
            description = content['date'] + ' ' + content['time']
            if 'tracking' in content:
                description += '\n' + content['tracking']['sport']
        else:
            description = ''

        requires_auth = does_requires_auth(network)
        if requires_auth and not adobe_activate_api.is_authenticated():
            ename = '*' + ename

        infoLabels = {'title': ename,
                      'genre': sport,
                      'duration': duration,
                      'studio': network_name,
                      'plot': description,
                      'aired': aired,
                      'premiered': aired}

        authurl = dict()
        if content['type'] == 'upcoming' or ('status' in content and  content['status'] == 'upcoming'):
            authurl[MODE] = UPCOMING_MODE
        else:
            authurl[EVENT_ID] = content['id']
            authurl[MODE] = PLAY_TV_MODE if 'adobeRSS' in content else PLAY_ITEM_MODE
            if 'adobeRSS' in content:
                authurl[ADOBE_RSS] = content['adobeRSS'].encode('iso-8859-1')
                authurl[NETWORK_NAME] = content['tracking']['network']
                authurl[SESSION_URL] = content['airings'][0]['videoHref']
            else:
                authurl[PLAYBACK_URL] = content['airings'][0]['videoHref']
        addLink(ename.encode('iso-8859-1'), authurl, fanart, fanart, infoLabels=infoLabels)
