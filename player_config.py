#!/usr/bin/python2

import os
import time
import globals
import urllib
from bs4 import BeautifulSoup

import util

TIME_DIFFERENCE = 60 * 60 * 24;

PLAYER_CONFIG_FILE = 'player_config.xml'
PLAYER_CONFIG_FILE = os.path.join(globals.ADDON_PATH_PROFILE, PLAYER_CONFIG_FILE)
PLAYER_CONFIG_URL = 'https://espn.go.com/watchespn/player/config'

def get_config_soup():
    return util.get_url_as_xml_soup_cache(PLAYER_CONFIG_URL, PLAYER_CONFIG_FILE, TIME_DIFFERENCE)

def get_networks():
    networks = get_config_soup().findAll('network')
    return networks

def get_live_event_url():
    return get_config_soup().find('feed', {'id' : 'liveEvent'}).text

def get_start_session_url():
    return get_config_soup().find('feed', {'id' : 'startSession'}).text

def get_providers_url():
    return get_config_soup().find('feed', {'id' : 'adobePassProviders'}).text

def get_network(network_id):
    networks = get_networks()
    for network in networks:
        if network['id'] == network_id:
            return network['name']
    return 'Unknown network %s' % network_id

if __name__ == '__main__':
    networks = get_networks()
    for network in networks:
        print '%s - %s' % (network['id'], network['name'])

    print 'live url %s: ' % get_live_event_url()

