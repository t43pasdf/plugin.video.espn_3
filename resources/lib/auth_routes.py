import Queue
import logging
import threading
import time
import urllib2

import adobe_activate_api
import espnplus
from plugin_routing import *
from resources.lib.addon_util import *
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
        ok = dialog.yesno(translation(30310),
                          translation(30320),
                          translation(30330) % regcode,
                          translation(30340),
                          translation(30360),
                          translation(30350))
        if ok:
            try:
                adobe_activate_api.authenticate(regcode)
                dialog.ok(translation(30310), translation(30370))
                set_setting('LoggedInToTvProvider', True)
                return True
            except urllib2.HTTPError as e:
                dialog.ok(translation(30037), translation(30420) % e)
                set_setting('LoggedInToTvProvider', False)
                return False


@plugin.route('/view-tv-provider-details')
def view_tv_provider_details():
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(30380),
              translation(30390) % adobe_activate_api.get_authentication_expires(),
              translation(30700) % (player_config.get_dma(), player_config.get_timezone()))

@plugin.route('/logout-tv-provider')
def logout_tv_provider():
    dialog = xbmcgui.Dialog()
    ok = dialog.yesno(translation(30381),
                      translation(30382))
    if ok:
        adobe_activate_api.deauthorize()
        set_setting('LoggedInToTvProvider', False)

@plugin.route('/login-espn-plus')
def login_espn_plus():
    if not espnplus.have_valid_login_id_token():
        logging.debug('Requesting login id token')
        semaphore = threading.Semaphore(0)
        result_queue = Queue.Queue()

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
            progress_dialog.update(times / max_times, get_string(40110), license_plate,
                                   get_string(40120) % (minutes, seconds))
            if canceled or acquired:
                break
            times = times + 1
        ws.close()
        progress_dialog.close()

        token = None
        try:
            token = result_queue.get(block=True, timeout=1)
        except Queue.Empty as e:
            logging.error('No result from websocket %s', e)

        if token is not None and 'id_token' in token:
            logging.debug('Received token %s' % token)
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
    dialog.ok(translation(40000), translation(40101))
    set_setting('LoggedInToEspnPlus', True)
    return True

@plugin.route('/view-espn-plus-details')
def view_espn_plus_details():
    account_details = espnplus.get_bam_account_details()
    product_details = account_details['attributes']['email'] + ' - ' + account_details['activeProfile']['profileName'] + '\n'
    sub_details = espnplus.get_bam_sub_details()
    for sub in sub_details:
        if sub['isActive']:
            product_name = ''
            for product in sub['products']:
                product_name = product_name + ' ' + product['name']
            product_details = product_details + product_name + ' ' + sub['expirationDate'] + '\n'
    dialog = xbmcgui.Dialog()
    dialog.ok(translation(40260), product_details)

@plugin.route('/logout-espn-plus')
def logout_espn_plus():
    set_setting('LoggedInToEspnPlus', False)
    espnplus.config.reset_settings()
