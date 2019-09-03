from addon_util import *
from register_mode import RegisterMode
from plugin_routing import *

TAG = 'AndroidTV: '
PLACE = 'androidtv'

HOME = 'HOME'
ANDROID_HOME = 'ANDROID_HOME'
SPORTS = 'SPORTS'
CHANNELS = 'CHANNELS'
BUCKET = 'BUCKET'
URL_MODE = 'URL_MODE'
URL = 'URL'

@plugin.route('/android-tv')
def android_tv_root_menu():
    url = base64.b64decode(
        'aHR0cHM6Ly93YXRjaC5wcm9kdWN0LmFwaS5lc3BuLmNvbS9hcGkvcHJvZHVjdC92MS9hbmRyb2lkL3R2L2hvbWU=')
    self.parse_json(args, url)
    xbmcplugin.endOfDirectory(plugin.handle)

@plugin.route('/android-tv/<path:url>')
def url_mode(self, url):
    self.parse_json(args, url)
    xbmcplugin.endOfDirectory(plugin.handle)
