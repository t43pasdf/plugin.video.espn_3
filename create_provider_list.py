#!/usr/bin/python2

'''
Generates a list of TV providers for settings.xml
'''
import urllib
from bs4 import BeautifulSoup


url = 'http://api-app.espn.com/v1/watch/clients/watchespn-flash/providers?_accept=text/xml&mvpd=true'
urllib.urlretrieve(url, 'providers.xml')
providers_soup = BeautifulSoup(open('providers.xml').read())
providers = providers_soup.findAll('providersitem')
provider_names = []
for provider in providers:
    provider_names.append(provider.find('name').text)

print '|'.join(provider_names)
