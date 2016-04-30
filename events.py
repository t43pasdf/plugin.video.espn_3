#!/usr/bin/python2

import os
import time
import urllib
from bs4 import BeautifulSoup

import player_config
import util
from player_config import get_live_event_url

def get_channel_list():
    networks = player_config.get_networks()
    network_ids = []
    for network in networks:
        network_ids.append(network['name'])
    return network_ids

def get_live_events_url(network_names = []):
    query_params = ','.join(network_names)
    return player_config.get_live_event_url() + '&channel=' + query_params

def get_live_events(network_names = []):
    soup = util.get_url_as_xml_soup(get_live_event_url())
    return soup.findAll('event')

def get_events(url):
    soup = util.get_url_as_xml_soup(url)
    return soup.findAll('event')

if __name__ == '__main__':
    events = get_live_events(get_channel_list())
    for event in events:
        print '%s - %s' % (event.find('name').text, event.find('networkId').text)
