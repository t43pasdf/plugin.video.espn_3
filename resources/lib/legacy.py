# Legacy menu system
import time
from datetime import datetime, timedelta

import xbmc
import xbmcgui
import xbmcplugin

import util
import player_config
import events
import adobe_activate_api
from globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, defaultimage, defaultfanart, translation, pluginhandle, LOG_LEVEL
from menu_listing import *
from register_mode import RegisterMode

from addon_util import *

TAG = 'Legacy: '

PLACE = 'legacy'
ROOT = ''
LIST_SPORTS_MODE = 'LIST_SPORTS'
INDEX_SPORTS_MODE = 'INDEX_SPORTS'

class Legacy(MenuListing):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        include_premium = adobe_activate_api.is_authenticated()
        channel_list = events.get_channel_list(include_premium)
        curdate = datetime.utcnow()
        upcoming = int(selfAddon.getSetting('upcoming'))+1
        days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
        addDir(translation(30029),
               dict(ESPN_URL=events.get_live_events_url(channel_list), MODE=self.make_mode(LIVE_EVENTS_MODE)),
               defaultlive)
        addDir(translation(30030),
               dict(ESPN_URL=events.get_upcoming_events_url(channel_list) + '&endDate=' + days + '&startDate=' + curdate.strftime("%Y%m%d"), MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultupcoming)
        enddate = '&endDate='+ (curdate+timedelta(days=1)).strftime("%Y%m%d")
        replays1 = [5,10,15,20,25]
        replays1 = replays1[int(selfAddon.getSetting('replays1'))]
        start1 = (curdate-timedelta(days=replays1)).strftime("%Y%m%d")
        replays2 = [10,20,30,40,50]
        replays2 = replays2[int(selfAddon.getSetting('replays2'))]
        start2 = (curdate-timedelta(days=replays2)).strftime("%Y%m%d")
        replays3 = [30,60,90,120]
        replays3 = replays3[int(selfAddon.getSetting('replays3'))]
        start3 = (curdate-timedelta(days=replays3)).strftime("%Y%m%d")
        replays4 = [60,90,120,240]
        replays4 = replays4[int(selfAddon.getSetting('replays4'))]
        start4 = (curdate-timedelta(days=replays4)).strftime("%Y%m%d")
        startAll = (curdate-timedelta(days=365)).strftime("%Y%m%d")
        addDir(translation(30031) + str(replays1) +' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start1, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays2) +' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start2, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays3) +' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + start3, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30031) + str(replays3) +'-' + str(replays4) +' Days',
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + '&endDate=' + start3 + '&startDate=' + start4, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        addDir(translation(30032),
               dict(ESPN_URL=events.get_replay_events_url(channel_list) + enddate + '&startDate=' + startAll, MODE=self.make_mode(LIST_SPORTS_MODE)),
               defaultreplay)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(LIST_SPORTS_MODE)
    def list_sports(self, args):
        espn_url = args.get(ESPN_URL)[0]
        if 'action=replay' in espn_url:
            image = defaultreplay
        elif 'action=upcoming' in espn_url:
            image = defaultupcoming
        else:
            image = defaultimage
        addDir(translation(30034), dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE)), image)
        sports = []
        sport_elements = util.get_url_as_xml_soup_cache(espn_url).findall('.//sportDisplayValue')
        for sport in sport_elements:
            sport = sport.text.encode('utf-8')
            if sport not in sports:
                sports.append(sport)
        for sport in sports:
            addDir(sport, dict(ESPN_URL=espn_url, MODE=self.make_mode(INDEX_SPORTS_MODE), SPORT=sport), image)
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(LIVE_EVENTS_MODE)
    def live_events_mode(self, args):
        espn_url = args.get(ESPN_URL)[0]
        chosen_sport = args.get(SPORT, None)
        if chosen_sport is not None:
            chosen_sport = chosen_sport[0]
        chosen_network = args.get(NETWORK_ID, None)
        if chosen_network is not None:
            chosen_network = chosen_network[0]
        live = 'action=live' in espn_url
        upcoming = 'action=upcoming' in espn_url
        replay = 'action=replay' in espn_url
        if live:
            data = events.get_events(espn_url)
        else:
            data = util.get_url_as_xml_soup_cache(espn_url).findall(".//event")
        num_espn3 = 0
        num_secplus = 0
        num_events = 0
        for event in data:
            sport = event.find('sportDisplayValue').text.encode('utf-8')
            if chosen_sport <> sport and chosen_sport is not None:
                continue
            networkid = event.find('networkId').text
            if chosen_network <> networkid and chosen_network is not None:
                continue
            if networkid == ESPN3_ID and chosen_network is None and live :
                num_espn3 = num_espn3 + 1
            elif networkid == SECPLUS_ID and chosen_network is None and live :
                num_secplus = num_secplus + 1
            else:
                num_events = num_events + 1
                self.index_event(event, live, upcoming, replay, chosen_sport)
        # Don't show ESPN3 folder if there are no premium events
        if num_events == 0:
            for event in data:
                sport = event.find('sportDisplayValue').text.encode('utf-8')
                if chosen_sport <> sport and chosen_sport is not None:
                    continue
                self.index_event(event, live, upcoming, replay, chosen_sport)
        # Dir for ESPN3/SECPlus
        elif chosen_network is None:
            if num_espn3 > 0:
                translation_number = 30191 if num_espn3 == 1 else 30190
                addDir('[COLOR=FFCC0000]' + (translation(translation_number) % num_espn3) + '[/COLOR]',
                   dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), NETWORK_ID=ESPN3_ID),
                   defaultlive)
            if num_secplus > 0:
                translation_number = 30201 if num_espn3 == 1 else 30200
                addDir('[COLOR=FF004C8D]' + (translation(translation_number) % num_secplus) + '[/COLOR]',
                   dict(ESPN_URL=espn_url, MODE=self.make_mode(LIVE_EVENTS_MODE), NETWORK_ID=SECPLUS_ID),
                   defaultlive)
        xbmcplugin.setContent(pluginhandle, 'episodes')
        xbmcplugin.endOfDirectory(pluginhandle)

    def index_event(self, event, live, upcoming, replay, chosen_sport):
        sport = event.find('sportDisplayValue').text.encode('utf-8')
        ename = event.find('name').text
        eventid = event.get('id')
        simulcastAiringId = event.find('simulcastAiringId').text
        networkid = event.find('networkId').text
        if networkid is not None:
            network = player_config.get_network_name(networkid)
        sport2 = event.find('sport').text
        if sport <> sport2:
            sport += ' (' + sport2 + ')'
        league = event.find('league').text
        location = event.find('site').text
        fanart = event.find('.//thumbnail/large').text
        fanart = fanart.split('&')[0]
        mpaa = event.find('parentalRating').text
        starttime = int(event.find('startTimeGmtMs').text) / 1000
        etime = time.strftime("%I:%M %p", time.localtime(float(starttime)))
        endtime = int(event.find('endTimeGmtMs').text) / 1000
        start = time.strftime("%m/%d/%Y %I:%M %p", time.localtime(starttime))
        aired = time.strftime("%Y-%m-%d", time.localtime(starttime))
        udate = time.strftime("%m/%d", time.localtime(starttime))
        now = datetime.now().strftime('%H%M')
        etime24 = time.strftime("%H%M", time.localtime(starttime))
        aspect_ratio = event.find('aspectRatio').text
        length = str(int(round((endtime - time.time()))))
        title_time = etime
        if live and now > etime24:
            color = 'FFFFFF'
        elif live:
            color = '999999'
        else:
            color = 'E0E0E0'
            length = str(int(round((endtime - starttime))))
            title_time = ' - '.join((udate, etime))

        if network == 'longhorn':
            channel_color = 'BF5700'
        elif network == 'sec' or network == 'secplus':
            channel_color = '004C8D'
        else:
            channel_color = 'CC0000'

        ename = '[COLOR=FF%s]%s[/COLOR] [COLOR=FFB700EB]%s[/COLOR] [COLOR=FF%s]%s[/COLOR]' % (
        channel_color, network, title_time, color, ename)

        length_minutes = int(length) / 60

        end = event.find('summary').text
        if end is None or len(end) == 0:
            end = event.find('caption').text

        if end is None:
            end = ''
        end += '\nNetwork: ' + network

        plot = ''
        if sport <> None and sport <> ' ':
            plot += translation(30620) % sport + '\n'
        if league <> None and league <> ' ':
            plot += translation(30630) % league + '\n'
        if location <> None and location <> ' ':
            plot += translation(30640) % location + '\n'
        if start <> None and start <> ' ':
            plot += translation(30650) % start + '\n'
        if length <> None and length <> ' ' and live:
            plot += translation(30660) % str(length_minutes) + '\n'
        elif length <> None and length <> ' ' and (replay or upcoming):
            plot += translation(30670) % str(length_minutes) + '\n'
        plot += end
        infoLabels = {'title': ename,
                      'genre': sport,
                      'plot': plot,
                      'aired': aired,
                      'premiered': aired,
                      'duration': length,
                      'studio': network,
                      'mpaa': mpaa,
                      'videoaspect': aspect_ratio}

        session_url = base64.b64decode('aHR0cDovL2Jyb2FkYmFuZC5lc3BuLmdvLmNvbS9lc3BuMy9hdXRoL3dhdGNoZXNwbi9zdGFydFNlc3Npb24/')
        session_url += '&channel=' + network
        session_url += '&simulcastAiringId=' + simulcastAiringId

        authurl = dict()
        authurl[EVENT_ID] = eventid
        authurl[MODE] = UPCOMING_MODE if upcoming else PLAY_MODE
        authurl[NETWORK_NAME] = event.find('adobeResource').text
        authurl[EVENT_NAME] = event.find('name').text.encode('utf-8')
        authurl[EVENT_GUID] = event.find('guid').text.encode('utf-8')
        authurl[EVENT_PARENTAL_RATING] = event.find('parentalRating').text
        authurl[SESSION_URL] = session_url
        addLink(ename, authurl, fanart, fanart, infoLabels=infoLabels)
