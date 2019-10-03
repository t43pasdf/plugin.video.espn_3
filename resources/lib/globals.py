import os

import requests
from resources.lib.kodiutils import addon_data_path, get_setting_as_bool, kodi_json_request, set_setting

defaultimage = os.path.join(addon_data_path, 'resources/icon.png')
defaultfanart = os.path.join(addon_data_path, 'resources/fanart.jpg')
defaultlive = os.path.join(addon_data_path, 'resources/media/new_live.png')
defaultreplay = os.path.join(addon_data_path, 'resources/media/new_replay.png')
defaultupcoming = os.path.join(addon_data_path, 'resources/media/new_upcoming.png')

# User Agents
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
UA_ATV = 'AppleCoreMedia/1.0.0.13Y234 (Apple TV; U; CPU OS 9_2 like Mac OS X; en_us)'

global_session = requests.Session()

if get_setting_as_bool('DisableSSL'):
    global_session.verify = False

if not get_setting_as_bool('DisableInputStream'):
    # Check that it is enabled
    addon_id = 'inputstream.hls'
    rpc_request = {"jsonrpc": "2.0",
                   "method": "Addons.GetAddonDetails",
                   "id": 1,
                   "params": {"addonid": "%s" % addon_id,
                              "properties": ["enabled"]}
                   }
    result = kodi_json_request(rpc_request)
    if result is None:
        set_setting('DisableInputStream', True)
    else:
        if result['addon']['enabled'] is False:
            set_setting('DisableInputStream', True)
