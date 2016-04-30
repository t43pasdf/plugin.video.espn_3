import re
import os
import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import json
import string, random
import urllib, urllib2, httplib2
import HTMLParser
import time
import cookielib
import base64
from StringIO import StringIO
import gzip

def CLEAR_SAVED_DATA():
    print "IN CLEAR"
    try:
        os.remove(ADDON_PATH_PROFILE+'/device.id')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/provider.info')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/cookies.lwp')
    except:
        pass
    try:
        os.remove(ADDON_PATH_PROFILE+'/auth.token')
    except:
        pass
    ADDON.setSetting(id='clear_data', value='false')


selfAddon = xbmcaddon.Addon(id='plugin.video.espn_3')
translation = selfAddon.getLocalizedString
defaultimage = 'special://home/addons/plugin.video.espn_3/icon.png'
defaultfanart = 'special://home/addons/plugin.video.espn_3/fanart.jpg'
defaultlive = 'special://home/addons/plugin.video.espn_3/resources/media/new_live.png'
defaultreplay = 'special://home/addons/plugin.video.espn_3/resources/media/new_replay.png'
defaultupcoming = 'special://home/addons/plugin.video.espn_3/resources/media/new_upcoming.png'
StreamType = selfAddon.getSetting('StreamType')
pluginpath = selfAddon.getAddonInfo('path')
pluginhandle = int(sys.argv[1])

ADDONDATA = xbmc.translatePath('special://profile/addon_data/plugin.video.espn_3/')
if not os.path.exists(ADDONDATA):
    os.makedirs(ADDONDATA)
USERFILE = os.path.join(ADDONDATA,'userdata.xml')

# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.espn_3').getAddonInfo('path')
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
KODI_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"
ROOT_URL = 'http://stream.nbcsports.com/data/mobile/'

#Settings file location
settings = xbmcaddon.Addon(id='plugin.video.espn_3')

#Main settings
#QUALITY = int(settings.getSetting(id="quality"))
#USER_AGENT = str(settings.getSetting(id="user-agent"))

ORIGIN = ''
REFERER = ''


#User Agents
UA_IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12H143'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ADOBE_PASS = 'AdobePassNativeClient/1.9 (iPhone; U; CPU iPhone OS 8.4 like Mac OS X; en-us)'
UA_NBCSN = 'AppleCoreMedia/1.0.0.12H143 (iPhone; U; CPU OS 8_4 like Mac OS X; en_us)'
UA_ANDROID = 'AdobePassNativeClient/1.7.3 (Linux; U; Android 5.1.1; en-us)'

#Create Random Device ID and save it to a file
fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
if not os.path.isfile(fname):
    if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
    new_device_id = ''.join([random.choice('0123456789abcdef') for x in range(64)])
    device_file = open(fname,'w')
    device_file.write(new_device_id)
    device_file.close()

fname = os.path.join(ADDON_PATH_PROFILE, 'device.id')
device_file = open(fname,'r')
DEVICE_ID = device_file.readline()
device_file.close()

#Create a file for storing Provider info
fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
if os.path.isfile(fname):
    provider_file = open(fname,'r')
    last_provider = provider_file.readline()
    provider_file.close()

provider_file = open(fname,'w')
provider_file.write(selfAddon.getSetting('provider'))
provider_file.close()


#Event Colors
FREE = 'FF43CD80'
LIVE = 'FF00B7EB'
UPCOMING = 'FFFFB266'
FREE_UPCOMING = 'FFCC66FF'
