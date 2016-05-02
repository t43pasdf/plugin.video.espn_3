#!/usr/bin/python2
import os
import hashlib

import player_config
import util
import globals
from player_config import get_live_event_url

def get_channel_list(include_premium):
    networks = player_config.get_networks()
    network_ids = []
    for network in networks:
        network_name = network.get('name')
        if include_premium or network_name == 'espn3':
            network_ids.append(network_name)
    return network_ids

def get_live_events_url(network_names = []):
    query_params = ','.join(network_names)
    return player_config.get_live_event_url() + '&channel=' + query_params

def get_upcoming_events_url(network_names = []):
    query_params = ','.join(network_names)
    return player_config.get_upcoming_event_url() + '&channel=' + query_params

def get_replay_events_url(network_names = []):
    query_params = ','.join(network_names)
    return player_config.get_replay_event_url() + '&channel=' + query_params

def get_live_events(network_names = []):
    soup = util.get_url_as_xml_soup(get_live_event_url())
    return soup.findall('.//event')

def get_events(url):
    soup = util.get_url_as_xml_soup(url)
    return soup.findall('.//event')

def get_soup_events_cached(url):
    cache_file = hashlib.sha224(url).hexdigest()
    cache_file = os.path.join(globals.ADDON_PATH_PROFILE, cache_file + '.xml')
    soup = util.get_url_as_xml_soup_cache(url, cache_file, 360)
    return soup

if __name__ == '__main__':
    events = get_live_events(get_channel_list(True))
    for event in events:
        print '%s - %s' % (event.find('name').text, event.find('networkId').text)
