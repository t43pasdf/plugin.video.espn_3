OLD_LISTING_MODE = 'OLD_LISTING_MODE'
LIVE_EVENTS_MODE = 'LIVE_EVENTS'
PLAY_MODE = 'PLAY'
PLAY_ITEM_MODE = 'PLAY_ITEM'
PLAY_TV_MODE = 'PLAY_TV'

UPCOMING_MODE = 'UPCOMING'
AUTHENTICATE_MODE = 'AUTHENTICATE'
AUTHENTICATION_DETAILS_MODE = 'AUTHENTICATION_DETAILS'


NETWORK_ID = 'NETWORK_ID'
EVENT_ID = 'EVENT_ID'
SIMULCAST_AIRING_ID = 'SIMULCAST_AIRING_ID'
SESSION_URL = 'SESSION_URL'
DESKTOP_STREAM_SOURCE = 'DESKTOP_STREAM_SOURCE'
NETWORK_NAME = 'NETWORK_NAME'
EVENT_NAME = 'EVENT_NAME'
EVENT_GUID = 'EVENT_GUID'
ADOBE_RSS = 'ADOBE_RSS'
EVENT_PARENTAL_RATING = 'EVENT_PARENTAL_RATING'
SHELF_ID = 'SHELF_ID'
SHOWCASE_URL = 'SHOWCASE_URL'
SHOWCASE_NAV_ID = 'SHOWCASE_NAV_ID'
PLAYBACK_URL = 'PLAYBACK_URL'
REFRESH_LIVE_MODE = 'REFRESH_LIVE_MODE'
CHANNEL_RESOURCE_ID = 'CHANNEL_RESOURCE_ID'

ESPN_URL = 'ESPN_URL'
MODE = 'MODE'
SPORT = 'SPORT'

BAM_NS = '{http://services.bamnetworks.com/media/types/2.1}'

# Taken from https://espn.go.com/watchespn/player/config
ESPN3_ID = 'n360'
SECPLUS_ID = 'n323'
ACC_EXTRA_ID = 'n321'

CHANNEL_SETTINGS = {
    'ShowEspn1': 'espn1',
    'ShowEspn2': 'espn2',
    'ShowEspn3': 'espn3',
    'ShowEspnu': 'espnu',
    'ShowEspnews': 'espnews',
    'ShowEspnDeportes': 'espndeportes',
    'ShowSec': 'sec',
    'ShowSecPlus': 'secplus',
    'ShowLonghorn': 'longhorn',
    'ShowBuzzerBeater': 'buzzerbeater',
    'ShowAccExtra': 'accextra',
    'ShowGoalLine': 'goalline',
    'ShowAcc': 'acc',
}
NETWORK_ID_TO_NETWORK_NAME = {
    'espn1': 30990,
    'espn2': 30991,
    'espn3': 30992,
    'espnu': 30993,
    'espnews': 30994,
    'espndeportes': 30995,
    'sec': 30996,
    'longhorn': 30998,
    'accextra': 30989,
    'goalline': 30988,
    'secplus': 30997,
    'acc': 31000,
    'espn_dtc': 31100,
}

NETWORK_ID_SORT_ORDER = [
    'espn1',
    'espn2',
    'espnu',
    'espnews',
    'espndeportes',
    'sec',
    'acc',
    'longhorn',
    'goalline',
]

GROUPED_NETWORK_IDS = [
    'espn3',
    'accextra',
    'secplus',
    'espn_dtc'
]

ID = 'id'
URL = 'url'

TV_OS_HOME = 'http://watch.product.api.espn.com/api/product/v1/tvos/watchespn/home'
TV_OS_CHANNELS = 'http://watch.product.api.espn.com/api/product/v1/tvos/watchespn/channels'
TV_OS_SPORTS = 'http://watch.product.api.espn.com/api/product/v1/tvos/watchespn/sports'

APPLE_TV_FEATURED = 'http://espn.go.com/watchespn/appletv/featured'
APPLE_TV_SPORTS = 'http://espn.go.com/watchespn/appletv/sports'
APPLE_TV_CHANNELS = 'http://espn.go.com/watchespn/appletv/channels'

WATCH_API_V1_TRENDING = 'http://watch.api.espn.com/v1/trending'

WATCH_API_V3_WEB_HOME = 'https://watch.product.api.espn.com/api/product/v3/watchespn/web/home'
