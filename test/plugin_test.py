import io
import pytest
import polib
import os


from resources.lib.kodiutils import ADDON
from resources.lib.globals import global_session
from resources.lib import kodiutils
import xbmcplugin
import xbmc

po = polib.pofile('resources/language/resource.language.en_GB/strings.po')


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")


@pytest.fixture(autouse=True)
def change_addon_path(monkeypatch):
    cache_path = os.path.join('test', 'cache')
    if not os.path.exists(cache_path):
        os.mkdir(cache_path)

    def get_addon_path(path):
        return cache_path

    def translate_path(path):
        return path
    monkeypatch.setattr(ADDON, 'getAddonInfo', get_addon_path)
    monkeypatch.setattr(xbmc, 'translatePath', translate_path)
    monkeypatch.setattr(kodiutils, 'addon_data_path', cache_path)
    monkeypatch.setattr(kodiutils, 'addon_profile_path', cache_path)


def get_localized_string(string_id):
    for entry in po:
        if entry.msgctxt == ('#%s' % string_id):
            return entry.msgid
    print('Unable to find string %s' % string_id)
    return str(string_id)


def empty_method():
    pass


def get_file_contents(file):
    with io.open(file, 'r', encoding='utf-8') as f:
        return f.read()


url_to_file = {
    'https://bam-sdk-configs.bamgrid.com/bam-sdk/v2.0/espn-a9b93989/browser/v3.4/linux/chrome/prod.json': 'test/files/prod.json',
    'http://broadband.espn.com/espn3/auth/watchespn/user': 'test/files/user.json',
    'https://watch.product.api.espn.com/api/product/v3/watchespn/web/bucket?lang=en&tz=UTC-0400&countryCode=US&bucketId=5060&zipcode=12188&entitlements=': 'test/files/live-bucket.json',
    'https://watch.product.api.espn.com/api/product/v3/watchespn/web/home?entitlements=&lang=en&tz=UTC-0400&zipcode=12188&countryCode=US': 'test/files/home.json',
}


class Resp:
    def __init__(self, text):
        self.text = text


def get_data(url):
    # print('getting data for %s' % url)
    if url in url_to_file:
        data = get_file_contents(url_to_file[url])
    else:
        print('Missing data for %s' % url)
        data = url
    return Resp(data)


def add_directory_item(handle, url, display_text, *args, **kwargs):
    print('Added item for %s' % url)


def test_new_index(monkeypatch):
    from resources.lib import adobe_activate_api
    monkeypatch.setattr(ADDON, 'getLocalizedString', get_localized_string)
    monkeypatch.setattr(adobe_activate_api, 'clean_up_authorization_tokens', empty_method)
    monkeypatch.setattr(global_session, 'get', get_data)
    monkeypatch.setattr(xbmcplugin, 'addDirectoryItem', add_directory_item)
    from resources.lib.plugin import new_index
    new_index()
