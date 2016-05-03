#!/usr/bin/python2

import xbmc
import os
import time
import urllib
import urllib2
import xml.etree.ElementTree as ET

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

def get_url_as_xml_soup_cache(url, cache_file, timeout = 1):
    if not is_file_valid(cache_file, timeout):
        xbmc.log('ESPN3: Fetching config file %s from %s' % (cache_file, url))
        fetch_file(url, cache_file)
    else:
        xbmc.log('ESPN3: Using cache %s for %s' % (url, cache_file))
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
            xbmc.log('EPSN3: Fixing up data because of no xml preamble')
            data = '<?xml version="1.0" encoding="ISO-8859-1" ?>' + data
        data_tree = ET.fromstring(data)

    return data_tree

