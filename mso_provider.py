import urllib2

import player_config
import util

class MSOProvider:

    def __init__(self, mso_name, mso_id):
        self.mso_id = mso_id
        self.mso_name = mso_name

    def get_mso_id(self):
        return self.mso_id
    def get_mso_name(self):
        return self.mso_name

def get_mso_provider(provider_name):
    url = player_config.get_providers_url()
    providers_soup = util.get_url_as_xml_soup(url)
    providers = providers_soup.findAll('providersitem')
    for provider in providers:
        if provider_name == provider.find('name').text:
            return MSOProvider(provider_name, provider.find('abbreviation').text)
    return None
