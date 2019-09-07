from xbmcplugin import addDirectoryItem, endOfDirectory

from resources.lib import page_api

from resources.lib.addon_util import *
from resources.lib.plugin_routing import *

ROOT = '/tvos'

@plugin.route(ROOT)
def tvos_root_menu():
    page_api.parse_json(TV_OS_HOME)

    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=TV_OS_SPORTS),
                     make_list_item(translation(30550)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=TV_OS_CHANNELS),
                     make_list_item(translation(30560)), True)
    endOfDirectory(plugin.handle)
