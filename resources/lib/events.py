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

from resources.lib import player_config, util


def get_channel_list(include_premium):
    networks = player_config.get_networks()
    network_ids = []
    for network in networks:
        network_name = network.get('name')
        if include_premium or network_name == 'espn3' or network_name == 'accextra':
            network_ids.append(network_name)
    return network_ids


def get_live_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_live_event_url() + '&channel=' + query_params


def get_upcoming_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_upcoming_event_url() + '&channel=' + query_params


def get_replay_events_url(network_names=None):
    if network_names is None:
        network_names = []
    query_params = ','.join(network_names)
    return player_config.get_replay_event_url() + '&channel=' + query_params


def get_live_events(network_names=None):
    if network_names is None:
        network_names = []
    et = util.get_url_as_xml_cache(player_config.get_live_event_url(), encoding='ISO-8859-1')
    return et.findall('.//event')


def get_events(url):
    et = util.get_url_as_xml_cache(url, encoding='ISO-8859-1')
    return et.findall('.//event')
