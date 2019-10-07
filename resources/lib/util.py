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
import time
import json
import xml.etree.ElementTree as ET
import hashlib
import re
import logging
import io

from resources.lib.globals import global_session
from resources.lib.kodiutils import addon_profile_path

logger = logging.getLogger(__name__)


def is_file_valid(cache_file, timeout):
    if os.path.isfile(cache_file):
        modified_time = os.path.getmtime(cache_file)
        current_time = time.time()
        return current_time - modified_time < timeout
    return False


def fetch_file(url, cache_file):
    resp = global_session.get(url)
    with io.open(cache_file, 'w', encoding='utf-8') as file:
        file.write(resp.text)


def clear_cache(url):
    cache_file = hashlib.sha224(url).hexdigest()
    try:
        os.remove(os.path.join(addon_profile_path, cache_file + '.xml'))
    except OSError:
        pass

    try:
        os.remove(os.path.join(addon_profile_path, cache_file + '.json'))
    except OSError:
        pass


def get_url_as_xml_cache(url, cache_file=None, timeout=180, encoding='utf-8'):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(addon_profile_path, cache_file + '.xml')
    if not is_file_valid(cache_file, timeout):
        logger.debug('Fetching config file %s from %s' % (cache_file, url))
        fetch_file(url, cache_file)
    else:
        logger.debug('Using cache %s for %s' % (cache_file, url))
    with io.open(cache_file, 'r', encoding='utf-8') as xml_file:
        xml_data = xml_file.read()
        return load_element_tree(xml_data)


# ESPN files are in iso-8859-1 and sometimes do not have the xml preamble
def load_element_tree(data):
    if '<?xml version' not in data:
        logger.debug('Fixing up data because of no xml preamble')
        iso_data = '<?xml version="1.0" encoding="ISO-8859-1" ?>' + data.encode('utf-8')
    else:
        iso_data = data.encode('utf-8')
    iso_data = re.sub('[\\x00-\\x1f]', '', iso_data)
    iso_data = re.sub('[\\x7f-\\x9f]', '', iso_data)
    iso_data = re.sub('&(?!amp;)', '&amp;', iso_data)
    try:
        parser = ET.XMLParser(encoding='iso-8859-1')
        data_tree = ET.fromstring(iso_data, parser)
    except ET.ParseError as e:
        logger.debug('Unable to parse xml %s' % e)
        data_tree = ET.fromstring(iso_data)

    return data_tree


def get_url_as_json(url):
    return global_session.get(url).json()


def get_url_as_json_cache(url, cache_file=None, timeout=180):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(addon_profile_path, cache_file + '.json')
    if not is_file_valid(cache_file, timeout):
        logger.debug('Fetching config file %s from %s' % (cache_file, url))
        fetch_file(url, cache_file)
    else:
        logger.debug('Using cache %s for %s' % (cache_file, url))

    with io.open(cache_file, 'r', encoding='utf-8') as json_file:
        json_data = json_file.read()

        if json_data.startswith('ud='):
            json_data = json_data.replace('ud=', '')
            json_data = json_data.replace('\'', '"')
        try:
            return json.loads(json_data)
        except Exception as e:
            clear_cache(url)
            raise e


# espn.page.loadSportPage('url');
# -> url
def parse_url_from_method(method):
    http_start = method.find('http')
    end = method.find('\')')
    return method[http_start:end]


# espn.page.loadMore('loadMoreLiveAndUpcoming', 'nav-0', 'url')
def parse_method_call(method):
    p = re.compile('([\\w.:/&?,-]{2,})')
    return p.findall(method)


def get_nested_value(dict_val, keys, defaultvalue=None):
    local_dict = dict_val
    for key in keys:
        try:
            local_dict = local_dict[key]
        except KeyError:
            return defaultvalue
    return local_dict
