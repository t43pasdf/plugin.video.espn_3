import urlparse
import urllib
import os
import xbmc
import xbmcgui
import urllib2
import time
from datetime import datetime

from globals import ADDON_PATH_PROFILE, UA_ANDROID, UA_PC, DEVICE_ID, UA_ADOBE_PASS, selfAddon
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

import gzip
from StringIO import StringIO
import cookielib

# Fixes an issue with 32bit systems not supporting times after 2038
def fix_cookie_expires(cj):
    for cookie in cj:
        if cookie.expires > 2000000000:
            cookie.expires = 2000000000

# Ignores adobepass://
class IgnoreHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, mgs, hdrs):
        if 'location' in hdrs and 'adobepass://' in hdrs['location']:
            xbmc.log('ESPN3: Ignoring redirect to %s' % hdrs['location'])
            return {'action' : 'skip_redirect', 'location' : hdrs['location']}
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, mgs, hdrs)

class ADOBE():

    def __init__(self, requestor, mso_provider, user_details):
        self.requestor = requestor
        self.mso_provider = mso_provider
        self.user_details = user_details

    def get_auth_token_file(self):
        return os.path.join(ADDON_PATH_PROFILE, 'auth.token')

    def get_auth_token(self):
        auth_token_file = self.get_auth_token_file()
        if os.path.isfile(auth_token_file):
            device_file = open(auth_token_file,'r')
            auth_token_contents = device_file.readline()
            # Verify the auth token isn't expired
            soup = BeautifulSoup(auth_token_contents, 'html.parser')
            token_expires_node = soup.find('simpletokenexpires')
            if not token_expires_node:
                xbmc.log('ESPN3: Removing %s because it doesn\'t have expires' % auth_token_contents)
                os.remove(auth_token_file)
                return ''
            token_expires_str = token_expires_node.text[:19]
            xbmc.log('ESPN3: Token expires at %s' % token_expires_str)
            expires_format = '%Y/%m/%d %H:%M:%S'
            try:
                token_expires = datetime.strptime(token_expires_str, expires_format)
            except TypeError:
                token_expires = datetime.fromtimestamp(time.mktime(time.strptime(token_expires_str, expires_format)))
            if (datetime.now() >= token_expires):
                self.delete_auth_token()
                xbmc.log('ESPN3: Token expired')
                return ''
            return auth_token_contents
        else:
            return ''

    def save_auth_token(self, auth_token):
        auth_token_file = self.get_auth_token_file()
        device_file = open(auth_token_file,'w')
        device_file.write(auth_token)
        device_file.close()

    def delete_auth_token(self):
        fname = self.get_auth_token_file()
        if os.path.isfile(fname):
            os.remove(fname)

    def get_provider(self):
        fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
        if os.path.isfile(fname):
            provider_file = open(fname,'r')
            last_provider = provider_file.readline()
            provider_file.close()
            return last_provider
        else:
            return ''

    def save_provider(self):
        fname = os.path.join(ADDON_PATH_PROFILE, 'provider.info')
        provider_file = open(fname,'w')
        provider_file.write(selfAddon.getSetting('provider'))
        provider_file.close()

    def save_cookies(self, cj):
        fix_cookie_expires(cj)
        cj.save(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True, ignore_expires=True )

    def get_form_action(self, soup):
        return soup.find('form').get('action')

    def get_origin(self, url):
        origin = urlparse.urlparse(url)
        origin = '%s://%s' % (origin.scheme, origin.netloc)
        return origin

    def resolve_relative_url(self, relative_url, url):
        relative_parsed = urlparse.urlparse(relative_url)
        if relative_parsed.scheme == '':
            origin = urlparse.urlparse(url)
            origin = '%s://%s' % (origin.scheme, origin.netloc)
            return '%s%s' % (origin, relative_url)
        return relative_url

    def check_redirect(self, content):
        content_soup = BeautifulSoup(content, 'html.parser')
        meta = content_soup.find('meta', {'http-equiv' : 'refresh'})
        if meta is not None:
            url = meta.get('content')
            url = url[(url.index('url=') + 4):]
            xbmc.log('ESPN3 http-equiv to %s' % url)
            return url
        return None

    def handle_url(self, opener, url, body  = None):
        resp = opener.open(url, body)
        if isinstance(resp, dict) and 'action' in resp and resp['action'] == 'skip_redirect':
            return ('skip redirect to %s' % (resp['location']), url)
        if resp.info().get('Content-Encoding') == 'gzip':
            buf = StringIO(resp.read())
            f = gzip.GzipFile(fileobj=buf)
            content = f.read()
        else:
            content = resp.read()
        url = resp.geturl()
        resp.close()
        redirect = self.check_redirect(content)
        if redirect is not None:
            return self.handle_url(opener, redirect)
        return (content, url)

    def GET_IDP_DATA(self):
        params = urllib.urlencode(
                                  {'domain_name' : 'adobe.com',
                                   'noflash' : 'true',
                                   'no_iframe' : 'true',
                                   'mso_id' : self.mso_provider.get_mso_id(),
                                   'requestor_id' : self.requestor.get_requestor_id(),
                                   'redirect_url' : 'adobepass://android.app'})

        idp_url = urlparse.urlunsplit(['https',
                            'sp.auth.adobe.com',
                            'adobe-services/1.0/authenticate',
                            params, ''])
        xbmc.log('ESPN3: Using IDP %s' % idp_url)
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), IgnoreHTTPRedirectHandler())
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_ANDROID)]

        (content, url) = self.handle_url(opener, idp_url)


        idp_soup = BeautifulSoup(content, 'html.parser')
        idp_action = self.get_form_action(idp_soup)
        idp_action = self.resolve_relative_url(idp_action, url)
        xbmc.log('ESPN3: IDP Action %s ' % idp_action)

        need_idp_request = 'https://sp.auth.adobe.com' in url

        # Some use a post form, others use an http-equiv
        saml_request = ''
        relay_state = ''
        if need_idp_request:
            for control in idp_soup.find_all('input'):
                xbmc.log('ESPN3: Looking at control %s' % control.get('name'))
                if control.get('name') == 'SAMLRequest':
                    saml_request = control.get('value')
                if control.get('name') == 'RelayState':
                    relay_state = control.get('value')

            origin = self.get_origin(idp_url)
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Referer", idp_url),
                            ("Origin", origin),
                            ("User-Agent", UA_PC)]
            body_contents = dict()
            for control in idp_soup.find_all('input'):
                body_contents[control.get('name')] = control.get('value')
            body = urllib.urlencode(body_contents);

            (content, url) = self.handle_url(opener, idp_action, body)
            xbmc.log('ESPN3: Ended up at url %s' % url)

        content_soup = BeautifulSoup(content, 'html.parser')
        content_action = self.get_form_action(content_soup)
        content_action = self.resolve_relative_url(content_action, url)
        body_contents = dict()
        for control in content_soup.find_all('input'):
            body_contents[control.get('name')] = control.get('value')
            xbmc.log('ESPN3: Populating control %s %s %s' % (control.get('name'), control.get('type'), control.get('value')))
            if control.get('type') == 'text':
                body_contents[control.get('name')] = self.user_details.get_username()
            if control.get('type') == 'password':
                body_contents[control.get('name')] = self.user_details.get_password()
            if control.get('name') == 'SAMLRequest' and saml_request != '':
                xbmc.log('ESPN3: Set saml request to %s' % saml_request)
                body_contents[control.get('name')] = saml_request
            if control.get('name') == 'RelayState' and relay_state != '':
                xbmc.log('ESPN3: Set relay state to %s' % relay_state)
                body_contents[control.get('name')] = relay_state

        for control in content_soup.find_all('select'):
            body_contents[control.get('name')] = control.get('value')

        for control in content_soup.find_all('button'):
            body_contents[control.get('name')] = control.get('value')

        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Referer", url),
                            ("Origin", self.get_origin(url)),
                            ("User-Agent", UA_PC)]
        body = urllib.urlencode(body_contents);

        # Post to provider to log in
        (content, url) = self.handle_url(opener, content_action, body)
        # Due to cookies sometimes the user does not need to log in and it goes
        # Right to adobe
        if 'skip redirect' not in content:
            adobe_soup = BeautifulSoup(content, 'html.parser')
            adobe_action = self.get_form_action(adobe_soup)
            adobe_action = self.resolve_relative_url(adobe_action, url)
            xbmc.log('ESPN3: Final Adobe url: %s' % adobe_action)
            if adobe_action == content_action or 'sp.auth.adobe.com' not in adobe_action:
                # Some error, assume invalid username and password
                msg = "Please verify that your username and password are correct"
                dialog = xbmcgui.Dialog()
                dialog.ok('Login Failed', msg)
                return False

            # Send final saml response to adobe
            origin = self.get_origin(idp_url)
            opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Referer", url),
                            ("Origin", self.get_origin(url)),
                            ("User-Agent", UA_PC)]
            body_contents = dict()
            for control in adobe_soup.find_all('input'):
                body_contents[control.get('name')] = control.get('value')
            body = urllib.urlencode(body_contents);

            (content, url) = self.handle_url(opener, adobe_action, body)

        self.save_cookies(cj)
        return True

    def GET_MEDIA_TOKEN(self):
        last_provider = self.get_provider()
        auth_token = self.get_auth_token()
        xbmc.log("Does the auth token file exist? " + auth_token)
        xbmc.log("Does the last provider match the current provider? " + str(last_provider == self.mso_provider.get_mso_name()))
        xbmc.log("Who was the last provider? " +str(last_provider))

        resource_id = self.requestor.get_resource_id()
        signed_requestor_id = self.requestor.get_signed_requestor_id()

        #auth token is not present run login or provider has changed
        if auth_token is '' or (last_provider != self.mso_provider.get_mso_name()):
            self.delete_auth_token()
            xbmc.log('ESPN3: Logging into provider')
            success = self.GET_IDP_DATA()

            if not success:
                return

            self.POST_SESSION_DEVICE(signed_requestor_id)


        authz = self.POST_AUTHORIZE_DEVICE(resource_id,signed_requestor_id)


        if 'Authorization failed' in authz or authz == '':
            msg = "Failed to authorize"
            dialog = xbmcgui.Dialog()
            dialog.ok('Authorization Failed', msg)
            self.delete_auth_token()
        else:
            media_token = self.POST_SHORT_AUTHORIZED(signed_requestor_id,authz)
            self.save_provider()
            return media_token

    def POST_SESSION_DEVICE(self,signed_requestor_id):
        ###################################################################
        # Create a Session for Device
        ###################################################################
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("User-Agent",  UA_ANDROID)]

        data = urllib.urlencode({'requestor_id' : self.requestor.get_requestor_id(),
                                 '_method' : 'GET',
                                 'signed_requestor_id' : signed_requestor_id,
                                 'device_id' : DEVICE_ID
                                })


        url = 'https://sp.auth.adobe.com/adobe-services/1.0/sessionDevice'

        (content, url) = self.handle_url(opener, url, data)

        xbmc.log('ESPN3: POST SESSION DEVICE')
        xbmc.log('ESPN3: body: %s' % data)
        xbmc.log('ESPN3: content: %s' % content)

        content_tree = ET.fromstring(content)
        authz = content_tree.find('.//authnToken').text
        xbmc.log('ESPN3: authz ' + authz)
        self.save_cookies(cj)

        self.save_auth_token(authz)


    def POST_AUTHORIZE_DEVICE(self,resource_id,signed_requestor_id):
        ###################################################################
        # Authorize Device
        ###################################################################
        auth_token = self.get_auth_token()

        xbmc.log('Auth Token: %s' % auth_token)

        if auth_token is None or auth_token == '':
            return ''


        url = 'https://sp.auth.adobe.com//adobe-services/1.0/authorizeDevice'
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [ ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                            ("Accept-Language", "en-us"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("User-Agent",  UA_ANDROID)]

        data = urllib.urlencode({'requestor_id' : self.requestor.get_requestor_id(),
                                 'resource_id' : resource_id,
                                 'signed_requestor_id' : signed_requestor_id,
                                 'mso_id' : self.mso_provider.get_mso_id(),
                                 'authentication_token' : auth_token,
                                 'device_id' : DEVICE_ID,
                                 'userMeta' : '1'
                                })

        (content, url) = self.handle_url(opener, url, data)

        content_tree = ET.fromstring(content)
        authz = content_tree.find('.//authzToken').text
        xbmc.log('ESPN3: authz ' + authz)
        self.save_cookies(cj)

        return authz


    def POST_SHORT_AUTHORIZED(self,signed_requestor_id,authz):
        ###################################################################
        # Short Authorize Device
        ###################################################################
        auth_token = self.get_auth_token()

        # Keep soup because the auth_token isn't proper xml
        soup = BeautifulSoup(auth_token, 'html.parser')
        session_guid = soup.find('simpletokenauthenticationguid').text

        url = 'https://sp.auth.adobe.com//adobe-services/1.0/deviceShortAuthorize'
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        opener.addheaders = [ ("Accept", "*/*"),
                            ("Accept-Encoding", "gzip, deflate"),
                            ("Accept-Language", "en-us"),
                            ("Content-Type", "application/x-www-form-urlencoded"),
                            ("Proxy-Connection", "keep-alive"),
                            ("Connection", "keep-alive"),
                            ("User-Agent", UA_ADOBE_PASS)]


        data = urllib.urlencode({'requestor_id' : self.requestor.get_requestor_id(),
                                 'signed_requestor_id' : signed_requestor_id,
                                 'mso_id' : self.mso_provider.get_mso_id(),
                                 'session_guid' : session_guid,
                                 'hashed_guid' : 'false',
                                 'authz_token' : authz,
                                 'device_id' : DEVICE_ID
                                })

        resp = opener.open(url, data)
        media_token = resp.read()
        resp.close()
        xbmc.log('ESPN3: media_token ' + media_token)

        return media_token
