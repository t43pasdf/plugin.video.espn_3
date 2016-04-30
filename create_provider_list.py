#!/usr/bin/python2

'''
Generates a list of TV providers for settings.xml
'''
import urllib2

import player_config
import util

url = player_config.get_providers_url()
providers_soup = util.get_url_as_xml_soup(url)
providers = providers_soup.findAll('providersitem')
provider_names = []
for provider in providers:
    provider_names.append(provider.find('name').text)

print '|'.join(provider_names)
