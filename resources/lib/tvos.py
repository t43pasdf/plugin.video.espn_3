from addon_util import *
from globals import defaultlive
from menu_listing import *
from register_mode import RegisterMode
from plugin_routing import *
import page_api
from xbmcplugin import addDirectoryItem

TAG = 'TVOS: '
ROOT = '/tvos'

@plugin.route(ROOT)
def tvos_root_menu():
    # TVOS home
    url = base64.b64decode(
        'aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
    page_api.parse_json(url)

    sports_url = url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2NoYW5uZWxz')
    channels_url = url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL3Nwb3J0cw==')
    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=channels_url),
                     make_list_item(translation(30550)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=sports_url),
                     make_list_item(translation(30560)), True)
    xbmcplugin.endOfDirectory(plugin.handle)
