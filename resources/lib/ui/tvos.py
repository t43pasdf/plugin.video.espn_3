# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished
# to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from xbmcplugin import addDirectoryItem, endOfDirectory

from resources.lib import page_api
from resources.lib.addon_util import make_list_item
from resources.lib.plugin_routing import plugin
from resources.lib.kodiutils import get_string
from resources.lib.constants import TV_OS_SPORTS, TV_OS_HOME, TV_OS_CHANNELS

ROOT = '/tvos'


@plugin.route(ROOT)
def tvos_root_menu():
    page_api.parse_json(TV_OS_HOME)

    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=TV_OS_SPORTS),
                     make_list_item(get_string(30550)), True)
    addDirectoryItem(plugin.handle,
                     plugin.url_for(page_api.page_api_url, url=TV_OS_CHANNELS),
                     make_list_item(get_string(30560)), True)
    endOfDirectory(plugin.handle)
