#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris
# Released under GPL(v2)

import urllib, xbmcplugin, xbmcaddon, xbmcgui, os, random, string, re
import time
from adobe import ADOBE
from globals import *
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import base64

import player_config
import events
import util
from espn import ESPN
from mso_provider import get_mso_provider
from user_details import UserDetails
import urlparse

LIVE_EVENTS_MODE = 'LIVE_EVENTS'
PLAY_MODE = 'PLAY'
LIST_SPORTS_MODE = 'LIST_SPORTS'
INDEX_SPORTS_MODE = 'INDEX_SPORTS'
UPCOMING_MODE = 'UPCOMING'
NETWORK_ID = 'NETWORK_ID'
EVENT_ID = 'EVENT_ID'
SIMULCAST_AIRING_ID = 'SIMULCAST_AIRING_ID'
DESKTOP_STREAM_SOURCE = 'DESKTOP_STREAM_SOURCE'

ESPN_URL = 'ESPN_URL'
MODE = 'MODE'
SPORT = 'SPORT'

BAM_NS = '{http://services.bamnetworks.com/media/types/2.1}'

def CATEGORIES():
    include_premium = selfAddon.getSetting('ShowPremiumChannels') == 'true'
    channel_list = events.get_channel_list(include_premium)
    curdate = datetime.utcnow()
    upcoming = int(selfAddon.getSetting('upcoming'))+1
    days = (curdate+timedelta(days=upcoming)).strftime("%Y%m%d")
    addDir(translation(30029),
           dict(ESPN_URL=events.get_live_events_url(channel_list), MODE=LIVE_EVENTS_MODE),
           defaultlive)
    addDir(translation(30030),
           dict(ESPN_URL=events.get_upcoming_events_url(channel_list) + '&endDate='+days+'&startDate='+curdate.strftime("%Y%m%d"), MODE=LIST_SPORTS_MODE),
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
    addDir(translation(30031)+str(replays1)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start1, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays2)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start2, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays3)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+start3, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30031)+str(replays3)+'-'+str(replays4)+' Days',
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +'&endDate='+start3+'&startDate='+start4, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    addDir(translation(30032),
           dict(ESPN_URL=events.get_replay_events_url(channel_list) +enddate+'&startDate='+startAll, MODE=LIST_SPORTS_MODE),
           defaultreplay)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def LISTNETWORKS(url,name):
    pass

def LISTSPORTS(args):
    espn_url = args.get(ESPN_URL)[0]
    if 'action=replay' in espn_url:
        image = defaultreplay
    elif 'action=upcoming' in espn_url:
        image = defaultupcoming
    else:
        image = defaultimage
    addDir(translation(30034), dict(ESPN_URL=espn_url, MODE=LIVE_EVENTS_MODE), image)
    sports = []
    sport_elements = events.get_soup_events_cached(espn_url).findall('.//sportDisplayValue')
    for sport in sport_elements:
        sport = sport.text.encode('utf-8')
        if sport not in sports:
            sports.append(sport)
    for sport in sports:
        addDir(sport, dict(ESPN_URL=espn_url, MODE=INDEX_SPORTS_MODE, SPORT=sport), image)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def INDEX(args):
    espn_url = args.get(ESPN_URL)[0]
    chosen_sport = args.get(SPORT, None)
    if chosen_sport is not None:
        chosen_sport = chosen_sport[0]
    live = 'action=live' in espn_url
    upcoming = 'action=upcoming' in espn_url
    replay = 'action=replay' in espn_url
    if live:
        data = events.get_events(espn_url)
    else:
        data = events.get_soup_events_cached(espn_url).findall(".//event")
    for event in data:
        sport = event.find('sportDisplayValue').text.encode('utf-8')
        desktopStreamSource = event.find('desktopStreamSource').text
        if chosen_sport <> sport and chosen_sport is not None:
            continue
        elif desktopStreamSource == 'HLS' and StreamType == 'true':
            pass
        else:
            ename = event.find('name').text
            eventid = event.get('id')
            simulcastAiringId = event.find('simulcastAiringId').text
            networkid = event.find('networkId').text
            if networkid is not None:
                network = player_config.get_network_name(networkid)
            sport2 = event.find('sport').text
            if sport <> sport2:
                sport += ' ('+sport2+')'
            league = event.find('league').text
            location = event.find('site').text
            fanart = event.find('.//thumbnail/large').text
            fanart = fanart.split('&')[0]
            mpaa = event.find('parentalRating').text
            starttime = int(event.find('startTimeGmtMs').text)/1000
            etime = time.strftime("%I:%M %p",time.localtime(float(starttime)))
            endtime = int(event.find('endTimeGmtMs').text)/1000
            start = time.strftime("%m/%d/%Y %I:%M %p",time.localtime(starttime))
            aired = time.strftime("%Y-%m-%d",time.localtime(starttime))
            udate = time.strftime("%m/%d",time.localtime(starttime))
            now = datetime.now().strftime('%H%M')
            etime24 = time.strftime("%H%M",time.localtime(starttime))
            aspect_ratio = event.find('aspectRatio').text
            length = str(int(round((endtime - time.time()))))
            title_time = etime
            if live and now > etime24:
                color = str(selfAddon.getSetting('color'))
            elif live:
                color = '999999'
            else:
                color = 'E0E0E0'
                length = str(int(round((endtime - starttime))))
                title_time = ' - '.join((udate, etime))

            channel_color = 'CC0000'

            ename = '[COLOR=FF%s]%s[/COLOR] [COLOR=FFB700EB]%s[/COLOR] [COLOR=FF%s]%s[/COLOR]' % (channel_color, network, title_time, color, ename)

            length_minutes = int(length) / 60

            end = event.find('summary').text
            if end is None or len(end) == 0:
                end = event.find('caption').text

            if end is None:
                end = ''
            end += '\nNetwork: ' + network

            plot = ''
            if sport <> None and sport <> ' ':
                plot += 'Sport: '+sport+'\n'
            if league <> None and league <> ' ':
                plot += 'League: '+league+'\n'
            if location <> None and location <> ' ':
                plot += 'Location: '+location+'\n'
            if start <> None and start <> ' ':
                plot += 'Air Date: '+start+'\n'
            if length <> None and length <> ' ' and live:
                plot += 'Duration: Approximately '+ str(length_minutes)+' minutes remaining'+'\n'
            elif length <> None and length <> ' ' and (replay or upcoming):
                plot += 'Duration: '+ str(length_minutes) +' minutes'+'\n'
            plot += end
            infoLabels = {'title': ename,
                          'genre':sport,
                          'plot':plot,
                          'aired':aired,
                          'premiered':aired,
                          'duration':length,
                          'studio':network,
                          'mpaa':mpaa,
                          'videoaspect' : aspect_ratio}

            authurl = dict()
            authurl[EVENT_ID] = eventid
            authurl[SIMULCAST_AIRING_ID] = simulcastAiringId
            authurl[DESKTOP_STREAM_SOURCE] = desktopStreamSource
            authurl[NETWORK_ID] = networkid
            authurl[MODE] = UPCOMING_MODE if upcoming else PLAY_MODE
            addLink(ename, authurl, fanart, fanart, infoLabels=infoLabels)
    xbmcplugin.setContent(pluginhandle, 'episodes')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def PLAYESPN3(url):
    PLAY(url,'n360')

def check_blackout(authurl):
    tree = util.get_url_as_xml_soup(authurl)
    authstatus = tree.find('.//' + BAM_NS + 'auth-status')
    blackoutstatus = tree.find('.//' + BAM_NS + 'blackout-status')
    if authstatus.find('./' + BAM_NS + 'successStatus') is not None:
        if authstatus.find('.//' + BAM_NS + 'notAuthorizedStatus') is not None:
            if authstatus.find('.//' + BAM_NS + 'errorMessage') is not None:
                dialog = xbmcgui.Dialog()
                import textwrap
                errormessage = authstatus.find('.//' + BAM_NS + 'errormessage').text
                try:
                    errormessage = textwrap.fill(errormessage, width=50).split('\n')
                    dialog.ok(translation(30037), errormessage[0],errormessage[1],errormessage[2])
                except:
                    dialog.ok(translation(30037), errormessage[0])
                return (tree, True)
        else:
            if blackoutstatus.find('.//' + BAM_NS + 'errorCode') is not None:
                if blackoutstatus.find('.//' + BAM_NS + 'errorMessage') is not None:
                    dialog = xbmcgui.Dialog()
                    dialog.ok(translation(30040), blackoutstatus.find('.//' + BAM_NS + 'errorMessage').text)
                    return (tree, True)
    return (tree, False)

def PLAY_PROTECTED_CONTENT(args):

    if not check_user_settings():
        return

    user_data = player_config.get_user_data()
    affiliateid = user_data.find('.//affiliate/name').text

    simulcastAiringId = args.get(SIMULCAST_AIRING_ID)[0]
    streamType = args.get(DESKTOP_STREAM_SOURCE)[0]
    networkId = args.get(NETWORK_ID)[0]

    requestor = ESPN()
    mso_provider = get_mso_provider(selfAddon.getSetting('provider'))
    user_details = UserDetails(selfAddon.getSetting('username'), selfAddon.getSetting('password'))


    adobe = ADOBE(requestor, mso_provider, user_details)
    media_token = adobe.GET_MEDIA_TOKEN()
    resource_id = requestor.get_resource_id()

    if media_token is None:
        return

    start_session_url = player_config.get_start_session_url()
    start_session_url += 'affiliate='+affiliateid
    start_session_url += '&channel='+player_config.get_network_name(networkId)
    start_session_url += '&partner=watchespn'
    start_session_url += '&playbackScenario=HTTP_CLOUD_MOBILE'
    start_session_url += '&v=2.0.0'
    start_session_url += '&platform=android_tablet'
    start_session_url += '&sdkVersion=1.1.0'
    start_session_url += '&token='+urllib.quote(base64.b64encode(media_token))
    start_session_url += '&resource=' + urllib.quote(base64.b64encode(resource_id))
    start_session_url += '&simulcastAiringId='+simulcastAiringId
    start_session_url += '&tokenType=ADOBEPASS'

    xbmc.log('ESPN3: start_session_url: ' + start_session_url)

    (tree, result) = check_blackout(start_session_url)
    if result:
        return

    pkan = tree.find('.//' + BAM_NS + 'pkanJar').text
    # FFMPEG does not support hds so use hls
    smilurl = tree.find('.//' + BAM_NS + 'hls-backup-url').text
    xbmc.log('ESPN3:  smilurl: '+smilurl)
    xbmc.log('ESPN3:  streamType: '+streamType)
    if smilurl == ' ' or smilurl == '':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30038),translation(30039))
        return

    finalurl = smilurl
    ua = urllib.quote('VisualOn OSMP+ Player(Linux;Android;WatchESPN/1.0_Handset)')
    finalurl = finalurl + '|User-Agent=' + ua + '&Cookie=_mediaAuth=' + urllib.quote(base64.b64encode(pkan))
    xbmc.log('ESPN3: finalurl %s' % finalurl)
    item = xbmcgui.ListItem(path=finalurl)
    return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

# TODO: This may need to log in the user with adobe
# if their ISP doesn't support it 100%
def PLAY_FREE_CONTENT(args):
    user_data = player_config.get_user_data()
    affiliateid = user_data.find('.//affiliate/name').text

    eventid = args.get(EVENT_ID)[0]
    simulcastAiringId = args.get(SIMULCAST_AIRING_ID)[0]
    streamType = args.get(DESKTOP_STREAM_SOURCE)[0]
    networkId = args.get(NETWORK_ID)[0]

    pk = ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(51)])
    pkan = pk + ('%3D')
    network = player_config.get_network(networkId)
    playedId = network.get('playerId')
    cdnName = network.get('defaultCdn')
    channel = network.get('name')
    if streamType == 'HLS':
        networkurl = 'http://broadband.espn.go.com/espn3/auth/watchespn/startSession?v=1.5'
    elif streamType == 'HDS' or streamType == 'RTMP':
        networkurl = 'https://espn-ws.bamnetworks.com/pubajaxws/bamrest/MediaService2_0/op-findUserVerifiedEvent/v-2.1'
    authurl = networkurl
    if '?' in authurl:
        authurl +='&'
    else:
        authurl +='?'

    if streamType == 'HLS':
        authurl += 'affiliate='+affiliateid
        authurl += '&pkan='+pkan
        authurl += '&pkanType=SWID'
        authurl += '&simulcastAiringId='+simulcastAiringId
    elif streamType == 'HDS' or streamType == 'RTMP':
        authurl += 'identityPointId='+affiliateid
        authurl += '&partnerContentId='+eventid
        authurl += '&contentId='+contentId
    authurl += '&cdnName='+cdnName
    authurl += '&channel='+channel
    authurl += '&playbackScenario=FMS_CLOUD'
    authurl += '&eventid='+eventid
    authurl += '&rand='+str(random.randint(100000,999999))
    authurl += '&playerId='+playedId

    xbmc.log('ESPN3: Content URL %s' % authurl)

    (tree, result) = check_blackout(authurl)
    if result:
        return

    smilurl = tree.find('.//' + BAM_NS + 'url').text
    xbmc.log('ESPN3:  smilurl: %s' % smilurl)
    if smilurl is None or smilurl == ' ' or smilurl == '':
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30038),translation(30039))
        return

    if streamType == 'HLS':
        finalurl = smilurl
        item = xbmcgui.ListItem(path=finalurl)
        return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

    elif streamType == 'HDS' or streamType == 'RTMP':
        # Not Tested
        auth = smilurl.split('?')[1]
        smilurl += '&rand='+str(random.randint(100000,999999))

        #Grab smil url to get rtmp url and playpath
        html = get_html(smilurl)
        soup = BeautifulSoup(html, 'html.parser')
        rtmp = soup.findAll('meta')[0]['base']
        # Live Qualities
        #     0,     1,     2,      3,      4
        # Replay Qualities
        #            0,     1,      2,      3
        # Lowest, Low,  Medium, High,  Highest
        # 200000,400000,800000,1200000,1800000
        playpath=False
        if selfAddon.getSetting("askquality") == 'true':
            streams = soup.findAll('video')
            quality=xbmcgui.Dialog().select(translation(30033), [str(int(stream['system-bitrate'])/1000)+'kbps' for stream in streams])
            if quality!=-1:
                playpath = streams[quality]['src']
            else:
                return
        if 'ondemand' in rtmp:
            if not playpath:
                playpath = soup.findAll('video')[int(selfAddon.getSetting('replayquality'))]['src']
            finalurl = rtmp+'/?'+auth+' playpath='+playpath
        elif 'live' in rtmp:
            if not playpath:
                select = int(selfAddon.getSetting('livequality'))
                videos = soup.findAll('video')
                videosLen = len(videos)-1
                if select > videosLen:
                    select = videosLen
                playpath = videos[select]['src']
            finalurl = rtmp+' live=1 playlist=1 subscribe='+playpath+' playpath='+playpath+'?'+auth
        item = xbmcgui.ListItem(path=finalurl)
        return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)

def check_user_settings():
    mso_provider = get_mso_provider(selfAddon.getSetting('provider'))
    username = selfAddon.getSetting('username')
    password = selfAddon.getSetting('password')
    if mso_provider is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30100))
        return False
    if username is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30110))
        return False
    if password is None:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(30037), translation(30120))
        return False
    return True


def PLAY(args):
    networkId = args.get(NETWORK_ID)[0]
    if networkId == 'n360':
        PLAY_FREE_CONTENT(args)
    else:
        PLAY_PROTECTED_CONTENT(args)

def addLink(name, url, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)

    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    liz.setProperty('IsPlayable', 'true')
    liz.setIconImage(iconimage)
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, iconimage, fanart=False, infoLabels=False):
    u = sys.argv[0] + '?' + urllib.urlencode(url)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if not infoLabels:
        infoLabels={"Title": name}
    liz.setInfo(type="Video", infoLabels=infoLabels)
    if not fanart:
        fanart=defaultfanart
    liz.setProperty('fanart_image',fanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get(MODE, None)

xbmc.log('ESPN3: args %s' % args)

if mode == None:
    xbmc.log("Generate Main Menu")
    CATEGORIES()
elif mode[0] == LIVE_EVENTS_MODE:
    xbmc.log("Indexing Videos")
    INDEX(args)
elif mode[0] == LIST_SPORTS_MODE:
    xbmc.log("List sports")
    LISTSPORTS(args)
elif mode[0] == INDEX_SPORTS_MODE:
    xbmc.log("Index by sport")
    INDEX(args)
elif mode[0] == PLAY_MODE:
    PLAY(args)
elif mode[0] == UPCOMING_MODE:
    xbmc.log("Upcoming")
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30035), translation(30036))


