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


import os

import util
from resources.lib.kodiutils import addon_profile_path
import pytz
import datetime

# 1 hour
TIME_DIFFERENCE = 60 * 60

PLAYER_CONFIG_FILE = 'player_config.xml'
PLAYER_CONFIG_FILE = os.path.join(addon_profile_path, PLAYER_CONFIG_FILE)
PLAYER_CONFIG_URL = 'https://espn.go.com/watchespn/player/config'

USER_DATA_FILE = 'user_data.json'
USER_DATA_FILE = os.path.join(addon_profile_path, USER_DATA_FILE)
USER_DATA_URL = 'http://broadband.espn.com/espn3/auth/watchespn/user'


def get_config():
    return util.get_url_as_xml_cache(PLAYER_CONFIG_URL, PLAYER_CONFIG_FILE, TIME_DIFFERENCE)


def get_user_data():
    return util.get_url_as_json_cache(USER_DATA_URL, USER_DATA_FILE, TIME_DIFFERENCE)


def get_user_location():
    return get_user_data()['user']['location']


def can_access_free_content():
    return 'isp' in get_user_data()['user']['authentication']


def get_timezone():
    return get_user_location()['timeZone']


def get_timezone_utc_offest():
    tz = pytz.timezone(get_timezone())
    return 'UTC%s' % tz.localize(datetime.datetime.now()).strftime('%z')


def get_zipcode():
    return get_user_location()['zipcode']


def get_dma():
    return get_user_location()['dma']


def get_networks():
    networks = get_config().findall('.//network')
    # Manually append the ACC network because their config file isn't up to date
    networks.append({
        'id': 'n821',
        'name': 'acc'
    })
    return networks


# Handle elementtree 1.2.8 which doesn't support [@ xpath notation
def select_feed_by_id(feed_id):
    try:
        return get_config().find('.//feed[@id=\'' + feed_id + '\']').text
    except:  # noqa: E722
        feeds = get_config().findall('.//feed')
        for feed in feeds:
            if feed.get('id') == feed_id:
                return feed.text
    return None


def get_live_event_url():
    return select_feed_by_id('liveEvent')


def get_replay_event_url():
    return select_feed_by_id('replayEvent')


def get_upcoming_event_url():
    return select_feed_by_id('upcomingEvent')


def get_network_name(network_id):
    # Manual fix for goal line network_id
    if network_id == 'n25':
        network_id = 'ngl'
    network = get_network(network_id)
    if network is None:
        return 'Unknown network %s' % network_id
    else:
        return network.get('name')


def get_network(network_id):
    networks = get_networks()
    for network in networks:
        if network.get('id') == network_id:
            return network
    return None
