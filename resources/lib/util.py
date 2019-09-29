# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import xbmc
import os
import time
import json
import xml.etree.ElementTree as ET
import hashlib
import re
import codecs

from globals import global_session
from kodiutils import addon_profile_path

TAG = 'ESPN3 util: '


def is_file_valid(cache_file, timeout):
    if os.path.isfile(cache_file):
        modified_time = os.path.getmtime(cache_file)
        current_time = time.time()
        return current_time - modified_time < timeout
    return False


def fetch_file(url, cache_file, encoding):
    resp = global_session.get(url)
    with codecs.open(cache_file, 'w', encoding) as file:
        file.write(resp.text)


def clear_cache(url):
    cache_file = hashlib.sha224(url).hexdigest()
    try:
        os.remove(os.path.join(addon_profile_path, cache_file + '.xml'))
    except:
        pass

    try:
        os.remove(os.path.join(addon_profile_path, cache_file + '.json'))
    except:
        pass


def get_url_as_xml_cache(url, cache_file=None, timeout=180, encoding='utf-8'):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(addon_profile_path, cache_file + '.xml')
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url), xbmc.LOGDEBUG)
        fetch_file(url, cache_file, encoding)
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (cache_file, url), xbmc.LOGDEBUG)
    with open(cache_file) as xml_file:
        xml_data = xml_file.read()
        return load_element_tree(xml_data)

# ESPN files are in iso-8859-1 and sometimes do not have the xml preamble
def load_element_tree(data):
    try:
        parser = ET.XMLParser(encoding='iso-8859-1')
        data_tree = ET.fromstring(data, parser)
    except:
        if '<?xml version' not in data:
            xbmc.log(TAG + 'Fixing up data because of no xml preamble', xbmc.LOGDEBUG)
            try:
                data_tree = ET.fromstring('<?xml version="1.0" encoding="ISO-8859-1" ?>' + data)
            except:
                try:
                    data_tree = ET.fromstring('<?xml version="1.0" encoding="windows-1252" ?>' + data)
                except:
                    # One last chance to fix up the data
                    xbmc.log(TAG + 'removing invalid xml characters', xbmc.LOGDEBUG)
                    data = re.sub('[\\x00-\\x1f]', '', data)
                    data = re.sub('[\\x7f-\\x9f]', '', data)
                    data_tree = ET.fromstring('<?xml version="1.0" encoding="ISO-8859-1" ?>' + data)
        else:
            data_tree = ET.fromstring(data)

    return data_tree


def get_url_as_json(url):
    return global_session.get(url).json()


def get_url_as_json_cache(url, cache_file=None, timeout=180):
    if cache_file is None:
        cache_file = hashlib.sha224(url).hexdigest()
        cache_file = os.path.join(addon_profile_path, cache_file + '.json')
    if not is_file_valid(cache_file, timeout):
        xbmc.log(TAG + 'Fetching config file %s from %s' % (cache_file, url), xbmc.LOGDEBUG)
        fetch_file(url, cache_file, 'utf-8')
    else:
        xbmc.log(TAG + 'Using cache %s for %s' % (cache_file, url), xbmc.LOGDEBUG)

    with open(cache_file) as json_file:
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
    p = re.compile('([\\w\\.:/&\\?=%,-]{2,})')
    return p.findall(method)


def get_nested_value(dict_val, keys, defaultvalue=None):
    local_dict = dict_val
    for key in keys:
        try:
            local_dict = local_dict[key]
        except:
            return defaultvalue
    return local_dict
