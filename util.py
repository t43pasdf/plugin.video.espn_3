#!/usr/bin/python2

import xbmc
import os
import time
import urllib
import urllib2
import json
import xml.etree.ElementTree as ET
import hashlib

from globals import ADDON_PATH_PROFILE

TAG = 'ESPN3 util: '

def is_file_valid(cache_file, timeout):
    if os.path.isfile(cache_file):
        modified_time = os.path.getmtime(cache_file)
        current_time = time.time()
        return current_time - modified_time < timeout
    return False


def fetch_file(url, cache_file):
    urllib.urlretrieve(url, cache_file)

def load_file(cache_file):
    return open(cache_file, mode='r')

def get_url_as_xml_soup_cache(url, cache_file = None, timeout = 300):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(ADDON_PATH_PROFILE, cache_file + '.xml')
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url))
        fetch_file(url, cache_file)
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (url, cache_file))
    xml_file = open(cache_file)
    xml_data = xml_file.read()
    xml_file.close()
    return load_element_tree(xml_data)

def get_url_as_xml_soup(url):
    config_data = urllib2.urlopen(url).read()
    return load_element_tree(config_data)

# ESPN files are in iso-8859-1 and sometimes do not have the xml preamble
def load_element_tree(data):
    try:
        parser = ET.XMLParser(encoding='iso-8859-1')
        data_tree = ET.fromstring(data, parser)
    except:
        if '<?xml version' not in data:
            xbmc.log(TAG + 'Fixing up data because of no xml preamble')
            data = '<?xml version="1.0" encoding="ISO-8859-1" ?>' + data
        data_tree = ET.fromstring(data)

    return data_tree

def get_url_as_json(url):
    response = urllib2.urlopen(url)
    return json.load(response)

def get_url_as_json_cache(url, cache_file, timeout = 1):
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url))
        fetch_file(url, cache_file)
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (url, cache_file))
    json_file = open(cache_file)
    json_data = json_file.read()
    json_file.close()
    json_data = json_data.replace('ud=', '')
    json_data = json_data.replace('\'', '"')
    xbmc.log('json: %s' % json_data)
    return json.loads(json_data)

# espn.page.loadSportPage('http://espn.go.com/watchespn/appletv/league?abbreviation=nba');
# -> http://espn.go.com/watchespn/appletv/league?abbreviation=nba
def parse_url_from_method(method):
    http_start = method.find('http')
    end = method.find('\');')
    return method[http_start:end]

