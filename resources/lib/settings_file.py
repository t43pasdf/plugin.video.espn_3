# Copyright 2019 https://github.com/kodi-addons
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import os
import json
import logging
from globals import ADDON_PATH_PROFILE

all_setting_objects = list()

class SettingsFile(object):

    def __init__(self, file_name):
        all_setting_objects.append(self)
        self.file_name = file_name
        self.settings = self.load_settings()

    def reset_settings(self):
        self.settings = dict()
        self.save_settings()

    def save_settings(self):
        settings_file = os.path.join(ADDON_PATH_PROFILE, self.file_name)
        with open(settings_file, 'w') as fp:
            json.dump(self.settings, fp, sort_keys=False, indent=4)

    def load_settings(self):
        settings_file = os.path.join(ADDON_PATH_PROFILE, self.file_name)
        if not os.path.isfile(settings_file):
            logging.debug('Resetting settings, unable to find file')
            self.reset_settings()
        with open(settings_file, 'r') as fp:
            return json.load(fp)

def save_settings():
    for settings in all_setting_objects:
        settings.save_settings()
