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

try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.error import HTTPError

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty

import logging
import threading
import time

import xbmcgui

from resources.lib import adobe_activate_api, espnplus, player_config, util
from resources.lib.plugin_routing import plugin
from resources.lib.kodiutils import get_string, set_setting


@plugin.route('/login-tv-provider')
def login_tv_provider():
    logging.debug('Authenticate Device')
    if adobe_activate_api.is_authenticated():
        logging.debug('Device already authenticated, skipping authentication')
        dialog = xbmcgui.Dialog()
        dialog.ok(get_string(30037), get_string(30301))
        set_setting('LoggedInToTvProvider', True)
        return True
    else:
        regcode = adobe_activate_api.get_regcode()
        dialog = xbmcgui.Dialog()
        ok = dialog.yesno(get_string(30310),
                          get_string(30320),
                          get_string(30330) % regcode,
                          get_string(30340),
                          get_string(30360),
                          get_string(30350))
        if ok:
            try:
                adobe_activate_api.authenticate(regcode)
                dialog.ok(get_string(30310), get_string(30370))
                set_setting('LoggedInToTvProvider', True)
                return True
            except HTTPError as e:
                dialog.ok(get_string(30037), get_string(30420) % e)
                set_setting('LoggedInToTvProvider', False)
                return False


@plugin.route('/view-tv-provider-details')
def view_tv_provider_details():
    dialog = xbmcgui.Dialog()
    dialog.ok(get_string(30380),
              get_string(30390) % adobe_activate_api.get_authentication_expires(),
              get_string(30700) % (player_config.get_dma(), player_config.get_timezone()))


@plugin.route('/logout-tv-provider')
def logout_tv_provider():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(get_string(30381),
                      get_string(30382))
    if ok:
        adobe_activate_api.deauthorize()
        set_setting('LoggedInToTvProvider', False)


@plugin.route('/login-espn-plus')
def login_espn_plus():
    if not espnplus.have_valid_login_id_token():
        logging.debug('Requesting login id token')
        semaphore = threading.Semaphore(0)
        result_queue = Queue()

        license_plate, ws = espnplus.perform_license_plate_auth_flow(semaphore, result_queue)
        progress_dialog = xbmcgui.DialogProgress()
        progress_dialog.create(get_string(40100), get_string(40110), license_plate)
        espnplus.start_websocket_thread(ws)
        times = 0
        sleep_time = 1
        max_time = 180
        max_times = max_time / sleep_time
        # wait a maximum of 3 minutes
        while times < max_times:
            time.sleep(sleep_time)
            canceled = progress_dialog.iscanceled()
            acquired = semaphore.acquire(blocking=False)
            logging.debug('Canceled: %s Acquired: %s' % (canceled, acquired))
            seconds_left = max_time - times * sleep_time
            minutes, seconds = divmod(seconds_left, 60)
            percent = int(times / max_times)
            progress_dialog.update(percent, get_string(40110), license_plate,
                                   get_string(40120) % (minutes, seconds))
            if canceled or acquired:
                break
            times = times + 1
        ws.close()
        progress_dialog.close()

        token = None
        try:
            token = result_queue.get(block=True, timeout=1)
        except Empty as e:
            logging.error('No result from websocket %s', e)

        if token is not None and 'id_token' in token:
            espnplus.handle_license_plate_token(token)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(get_string(30037), get_string(40130))
            set_setting('LoggedInToEspnPlus', False)
            return False

    if not espnplus.has_valid_bam_account_access_token():
        espnplus.request_bam_account_access_token()

    logging.debug('Bam token %s' % espnplus.get_bam_account_access_token())
    dialog = xbmcgui.Dialog()
    dialog.ok(get_string(40000), get_string(40101))
    set_setting('LoggedInToEspnPlus', True)
    return True


@plugin.route('/view-espn-plus-details')
def view_espn_plus_details():
    account_details = espnplus.get_bam_account_details()
    email = util.get_nested_value(account_details, ['attributes', 'email'], 'Unknown Email')
    profile_name = util.get_nested_value(account_details, ['activeProfile', 'profileName'], 'Unknown Profile Name')
    product_details = email + ' - ' + profile_name + '\n'
    sub_details = espnplus.get_bam_sub_details()
    for sub in sub_details:
        if sub['isActive']:
            product_name = ''
            for product in sub['products']:
                product_name = product_name + ' ' + product['name']
            product_details = product_details + product_name + ' ' + sub['expirationDate'] + '\n'
    dialog = xbmcgui.Dialog()
    dialog.ok(get_string(40260), product_details)


@plugin.route('/logout-espn-plus')
def logout_espn_plus():
    set_setting('LoggedInToEspnPlus', False)
    espnplus.config.reset_settings()
