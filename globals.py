import os, sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

selfAddon = xbmcaddon.Addon(id='plugin.video.espn_3')
translation = selfAddon.getLocalizedString
defaultimage = 'special://home/addons/plugin.video.espn_3/icon.png'
defaultfanart = 'special://home/addons/plugin.video.espn_3/fanart.jpg'
defaultlive = 'special://home/addons/plugin.video.espn_3/resources/media/new_live.png'
defaultreplay = 'special://home/addons/plugin.video.espn_3/resources/media/new_replay.png'
defaultupcoming = 'special://home/addons/plugin.video.espn_3/resources/media/new_upcoming.png'
pluginhandle = int(sys.argv[1])

ADDONDATA = xbmc.translatePath('special://profile/addon_data/plugin.video.espn_3/')
if not os.path.exists(ADDONDATA):
    os.makedirs(ADDONDATA)

# KODI ADDON GLOBALS
ADDON_HANDLE = int(sys.argv[1])
ROOTDIR = xbmcaddon.Addon(id='plugin.video.espn_3').getAddonInfo('path')
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)
FANART = ROOTDIR+"/fanart.jpg"
ICON = ROOTDIR+"/icon.png"

#User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

def CLEAR_SAVED_DATA():
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
    try:
        for root, dirs, files in os.walk(ADDON_PATH_PROFILE):
            for currentFile in files:
                if currentFile.lower().endswith('.xml') and not currentFile.lower() == 'settings.xml':
                    os.remove(os.path.join(ADDON_PATH_PROFILE, currentFile))
    except:
        pass
    ADDON.setSetting(id='ClearData', value='false')

if selfAddon.getSetting('ClearData') == 'true':
    CLEAR_SAVED_DATA()

if selfAddon.getSetting('DisableSSL') == 'true':
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
