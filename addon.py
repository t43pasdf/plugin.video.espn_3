#!/usr/bin/python
#
#
# Written by Ksosez, BlueCop, Romans I XVI, locomot1f, MetalChris, awaters1 (https://github.com/awaters1)
# Released under GPL(v2)

import xbmcaddon
ADDON = xbmcaddon.Addon()

from resources.lib import kodilogging
kodilogging.config()

from resources.lib import plugin


# Keep this file to a minimum, as Kodi
# doesn't keep a compiled copy of this

plugin.run()


