import mechanize
import urlparse
import urllib
import os
import xbmc
from datetime import datetime

from globals import *
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

import cookielib

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

    def GET_IDP_DATA(self):
        params = urllib.urlencode(
                                  {'domain_name' : 'adobe.com',
                                   'noflash' : 'true',
                                   'no_iframe' : 'true',
                                   'mso_id' : self.mso_provider.get_mso_id(),
                                   'requestor_id' : self.requestor.get_requestor_id(),
                                   'redirect_url' : 'adobepass://android.app',
                                   'client_type' : 'android',
                                   'client_version' : '1.7.3'})
        idp_url = urlparse.urlunsplit(['https',
                            'sp.auth.adobe.com',
                            'adobe-services/1.0/authenticate/saml',
                            params, ''])

        factory = mechanize.RobustFactory()
        br = mechanize.Browser(factory=factory)
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj);
        br.set_debug_http(False)
        br.set_debug_responses(False)
        br.set_handle_robots(False)
        xbmc.log('ESPN3: IDP %s' % idp_url)
        br.open(idp_url)
        #response = br.open(idp_url)
        #forms = mechanize.ParseResponseEx(response)
        #response.close()

        br.select_form(nr = 0)

        # Detect redirect form (DirectTV)
        for control in br.form.controls:
            if control.type == 'hidden' and control.name == 'SAMLRequest':
                br.submit()
                br.select_form(nr = 0)

        for control in br.form.controls:
            if control.type == 'text':
                br.form[control.name] = self.user_details.get_username();
            if control.type == 'password':
                br.form[control.name] = self.user_details.get_password();
        br.set_handle_refresh(False)
        br.submit()
        br.select_form(nr = 0)
        self.save_cookies(cj)
        saml = ''
        relay_state = '';
        for control in br.form.controls:
            if control.name == 'SAMLResponse':
                saml = control.value
            if control.name == 'RelayState':
                relay_state = control.value
        xbmc.log('ESPN3 getting adobe response')
        return (saml, relay_state)

    def GET_MEDIA_TOKEN(self):
        expired_cookies = True
        try:
            cj = cookielib.LWPCookieJar()
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

            for cookie in cj:
                if cookie.name == 'BIGipServerAdobe_Pass_Prod':
                    xbmc.log('ESPN3 cookie.name %s' % cookie.name)
                    xbmc.log('ESPN3 cookie.expires %s' % cookie.expires)
                    xbmc.log('ESPN3 cookie.is_expired %s' % cookie.is_expired())
                    expired_cookies = cookie.is_expired()
        except:
            pass

        last_provider = self.get_provider()
        auth_token = self.get_auth_token()
        xbmc.log("Did cookies expire? " + str(expired_cookies))
        xbmc.log("Does the auth token file exist? " + auth_token)
        xbmc.log("Does the last provider match the current provider? " + str(last_provider == self.mso_provider.get_mso_name()))
        xbmc.log("Who was the last provider? " +str(last_provider))

        resource_id = self.requestor.get_resource_id()
        signed_requestor_id = self.requestor.get_signed_requestor_id()

        #If cookies are expired or auth token is not present run login or provider has changed
        if expired_cookies or auth_token is '' or (last_provider != self.mso_provider.get_mso_name()):
            self.delete_auth_token()
            xbmc.log('ESPN3: Logging into provider')
            saml_response, relay_state = self.GET_IDP_DATA()

            if saml_response == '' and relay_state == '':
                msg = "Please verify that your username and password are correct"
                dialog = xbmcgui.Dialog()
                ok = dialog.ok('Login Failed', msg)
                return
            elif saml_response == 'captcha':
                msg = "Login requires captcha. Please try again later"
                dialog = xbmcgui.Dialog()
                ok = dialog.ok('Captcha Found', msg)
                return

            self.POST_ASSERTION_CONSUMER_SERVICE(saml_response,relay_state)
            self.POST_SESSION_DEVICE(signed_requestor_id)


        authz = self.POST_AUTHORIZE_DEVICE(resource_id,signed_requestor_id)


        if 'Authorization failed' in authz or authz == '':
            msg = "Failed to authorize"
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('Authorization Failed', msg)
            self.delete_auth_token()
        else:
            media_token = self.POST_SHORT_AUTHORIZED(signed_requestor_id,authz)
            self.save_provider()
            return media_token

    def POST_ASSERTION_CONSUMER_SERVICE(self,saml_response,relay_state):
        ###################################################################
        # SAML Assertion Consumer
        ###################################################################
        url = 'https://sp.auth.adobe.com/sp/saml/SAMLAssertionConsumer'

        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)

        cookies = ''
        for cookie in cj:
            #if (cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "client_type" or cookie.name == "client_version" or cookie.name == "JSESSIONID" or cookie.name == "redirect_url") and cookie.domain == "sp.auth.adobe.com":
            if cookie.domain == "sp.auth.adobe.com":
                cookies = cookies + cookie.name + "=" + cookie.value + "; "


        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                            "Accept-Encoding": "gzip, deflate",
                            "Accept-Language": "en-us",
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Proxy-Connection": "keep-alive",
                            "Connection": "keep-alive",
                            "Origin": ORIGIN,
                            "Referer": REFERER,
                            "Cookie": cookies,
                            "User-Agent": UA_IPHONE}


        body = urllib.urlencode({'SAMLResponse' : saml_response,
                                 'RelayState' : relay_state
                                 })


        response, content = http.request(url, 'POST', headers=headers, body=body)
        xbmc.log('ESPN3: POST_ASSERTION_CONSUMER_SERVICE')
        xbmc.log('ESPN3: headers: %s' % headers)
        xbmc.log('ESPN3: body: %s' % body)
        xbmc.log('ESPN3: response: %s' % response)
        xbmc.log('ESPN3: content: %s' % content)
        self.save_cookies(cj)

    def POST_SESSION_DEVICE(self,signed_requestor_id):
        ###################################################################
        # Create a Session for Device
        ###################################################################
        cj = cookielib.LWPCookieJar()
        cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
        cookies = ''
        for cookie in cj:
            #Possibly two JSESSION cookies being passed, may need to fix
            #if cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "client_type" or cookie.name == "client_version" or cookie.name == "JSESSIONID" or cookie.name == "redirect_url":
            if (cookie.name == "BIGipServerAdobe_Pass_Prod" or cookie.name == "JSESSIONID") and cookie.path == "/":
                cookies = cookies + cookie.name + "=" + cookie.value + "; "



        url = 'https://sp.auth.adobe.com//adobe-services/1.0/sessionDevice'
        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True
        data = urllib.urlencode({'requestor_id' : self.requestor.get_requestor_id(),
                                 '_method' : 'GET',
                                 'signed_requestor_id' : signed_requestor_id,
                                 'device_id' : DEVICE_ID
                                })

        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Connection": "keep-alive",
                    "Content-Length" : str(len(data)),
                    "Cookie": cookies,
                    "User-Agent": UA_IPHONE}

        response, content = http.request(url, 'POST', headers=headers, body=data)
        xbmc.log('ESPN3: POST SESSION DEVICE')
        xbmc.log('ESPN3: headers: %s ' % headers)
        xbmc.log('ESPN3: body: %s' % data)
        xbmc.log('ESPN3: response: %s' % response)
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
        http = httplib2.Http()
        http.disable_ssl_certificate_validation=True

        headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Proxy-Connection": "keep-alive",
                    "Connection": "keep-alive",
                    "User-Agent":  UA_ANDROID}


        data = urllib.urlencode({'requestor_id' : self.requestor.get_requestor_id(),
                                 'resource_id' : resource_id,
                                 'signed_requestor_id' : signed_requestor_id,
                                 'mso_id' : self.mso_provider.get_mso_id(),
                                 'authentication_token' : auth_token,
                                 'device_id' : DEVICE_ID,
                                 'userMeta' : '1'
                                })

        xbmc.log('data: %s ' % data)
        response, content = http.request(url, 'POST', headers=headers, body=data)

        xbmc.log('content: %s ' % content)
        xbmc.log('response: %s ' % response)

        try:
            xbmc.log("REFRESHED COOKIE")
            adobe_pass = response['set-cookie']
            xbmc.log('ESPN3: adobe_pass ' + adobe_pass)
            cj = cookielib.LWPCookieJar(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'))
            cj.load(os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp'),ignore_discard=True)
            #BIGipServerAdobe_Pass_Prod=526669578.20480.0000; expires=Fri, 19-Jun-2015 19:58:42 GMT; path=/
            value = FIND(adobe_pass,'BIGipServerAdobe_Pass_Prod=',';')
            expires = FIND(adobe_pass,'expires=',' GMT;')
            #date_time = '29.08.2011 11:05:02'
            #pattern = '%d.%m.%Y %H:%M:%S'
            #Fri, 19-Jun-2015 19:58:42
            pattern = '%a, %d-%b-%Y %H:%M:%S'
            xbmc.log('ESPN3: expires ' + expires)
            expires_epoch = int(time.mktime(time.strptime(expires, pattern)))
            xbmc.log('ESPN3: expires_epoch ' + expires_epoch)
            ck = cookielib.Cookie(version=0, name='BIGipServerAdobe_Pass_Prod', value=value, port=None, port_specified=False, domain='sp.auth.adobe.com', domain_specified=True, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=expires_epoch, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
            cj.set_cookie(ck)
            self.save_cookies(cj)

        except:
            pass
        content_tree = ET.fromstring(content)
        authz = content_tree.find('.//authzToken').text
        xbmc.log('ESPN3: authz ' + authz)

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
