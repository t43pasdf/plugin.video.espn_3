import os
import sys
import xbmc
import xbmcaddon
import requests
import json

selfAddon = xbmcaddon.Addon()
addon_data_path = xbmc.translatePath(selfAddon.getAddonInfo('path')).decode('utf-8')
translation = selfAddon.getLocalizedString
defaultimage = os.path.join(addon_data_path, 'icon.png')
defaultfanart = os.path.join(addon_data_path, 'fanart.jpg')
defaultlive = os.path.join(addon_data_path, 'resources/media/new_live.png')
defaultreplay = os.path.join(addon_data_path, 'resources/media/new_replay.png')
defaultupcoming = os.path.join(addon_data_path, 'resources/media/new_upcoming.png')

ADDON_PATH_PROFILE = xbmc.translatePath(selfAddon.getAddonInfo('profile')).decode('utf-8')
if not os.path.exists(ADDON_PATH_PROFILE):
        os.makedirs(ADDON_PATH_PROFILE)

# User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

def CLEAR_SAVED_DATA():
    try:
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'adobe-cookies.lwp'))
    except:
        pass
    try:
        os.remove(os.path.join(ADDON_PATH_PROFILE, 'user_data.json'))
    except:
        pass
    try:
        for root, dirs, files in os.walk(ADDON_PATH_PROFILE):
            for currentFile in files:
                if currentFile.lower().endswith('.xml') and not currentFile.lower() == 'settings.xml':
                    os.remove(os.path.join(ADDON_PATH_PROFILE, currentFile))
                if currentFile.lower().endswith('.json') and not currentFile.lower() == 'adobe.json':
                    os.remove(os.path.join(ADDON_PATH_PROFILE, currentFile))
    except:
        pass
    selfAddon.setSetting(id='ClearData', value='false')

if selfAddon.getSetting('ClearData') == 'true':
    CLEAR_SAVED_DATA()

global_session = requests.Session()

if selfAddon.getSetting('DisableSSL') == 'true':
    global_session.verify = False

if selfAddon.getSetting('DisableInputStream') == 'false':
    # Check that it is enabled
    addon_id = 'inputstream.hls'
    rpc_request = json.dumps({"jsonrpc": "2.0",
                              "method": "Addons.GetAddonDetails",
                              "id": 1,
                              "params": {"addonid": "%s" % addon_id,
                                         "properties": ["enabled"]}
                              })
    response = json.loads(xbmc.executeJSONRPC(rpc_request))
    try:
        if response['result']['addon']['enabled'] is False:
            selfAddon.setSetting(id='DisableInputStream', value='true')
    except KeyError:
        message = response['error']['message']
        code = response['error']['code']
        error = 'Requested |%s| received error |%s| and code: |%s|' % (rpc_request, message, code)
        xbmc.log(error, xbmc.LOGDEBUG)
        selfAddon.setSetting(id='DisableInputStream', value='true')
