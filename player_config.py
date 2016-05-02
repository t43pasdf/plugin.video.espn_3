#!/usr/bin/python2

import os
import time
import globals
import urllib
import xbmc

import util

# 1 day
TIME_DIFFERENCE = 60 * 60 * 24;

PLAYER_CONFIG_FILE = 'player_config.xml'
PLAYER_CONFIG_FILE = os.path.join(globals.ADDON_PATH_PROFILE, PLAYER_CONFIG_FILE)
PLAYER_CONFIG_URL = 'https://espn.go.com/watchespn/player/config'

USER_DATA_FILE = 'user_data.xml'
USER_DATA_FILE = os.path.join(globals.ADDON_PATH_PROFILE, USER_DATA_FILE)
USER_DATA_URL = 'http://broadband.espn.go.com/espn3/auth/watchespn/userData?format=xml'

PROVIDERS_FILE = 'providers.xml'
PROVIDERS_FILE = os.path.join(globals.ADDON_PATH_PROFILE, PROVIDERS_FILE)

#TODO: Hook up check rights?
CHECK_RIGHTS_URL = 'http://broadband.espn.go.com/espn3/auth/espnnetworks/user'

def get_config_soup():
    return util.get_url_as_xml_soup_cache(PLAYER_CONFIG_URL, PLAYER_CONFIG_FILE, TIME_DIFFERENCE)

def get_user_data():
    return util.get_url_as_xml_soup_cache(USER_DATA_URL, USER_DATA_FILE, TIME_DIFFERENCE)

def get_providers_data():
    return util.get_url_as_xml_soup_cache(get_providers_url(), PROVIDERS_FILE, TIME_DIFFERENCE)

def get_networks():
    networks = get_config_soup().findall('.//network')
    return networks

# Handle elementtree 1.2.8 which doesn't support [@ xpath notation
def select_feed_by_id(feed_id):
    try:
        return get_config_soup().find('.//feed[@id=\'' + feed_id + '\']').text
    except:
        feeds = get_config_soup().findall('.//feed')
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

def get_start_session_url():
    return select_feed_by_id('startSession')

def get_providers_url():
    return select_feed_by_id('adobePassProviders')

def get_network_name(network_id):
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

if __name__ == '__main__':
    networks = get_networks()
    for network in networks:
        print '%s - %s' % (network['id'], network['name'])

    print 'live url %s: ' % get_live_event_url()

