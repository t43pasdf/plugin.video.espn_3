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
