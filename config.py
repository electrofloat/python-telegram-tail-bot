'''
Copyright (c) 2022 Pim van Pelt
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import logging
import yaml
import time
from datetime import datetime

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pttb.config')
logger.addHandler(NullHandler())

class Config():
    config = "/etc/pttb/pttb.yaml"
    yaml = None

    def _validate_config():
        if not 'telegram' in Config.yaml:
            logger.error("Missing telegram entry in %s" % Config.config)
            return False
        if not 'token' in Config.yaml['telegram']:
            logger.error("Missing telegram.token entry in %s" % Config.config)
            return False
        if not 'chat-id' in Config.yaml['telegram']:
            logger.error("Missing telegram.chat-id entry in %s" % Config.config)
            return False
        if not 'triggers' in Config.yaml:
            Config.yaml['triggers'] = []
        if not 'silences' in Config.yaml:
            Config.yaml['silences'] = []

        for trigger in Config.yaml['triggers']:
            if not isinstance(trigger['regexp'], str) or not isinstance(trigger['message'], str) or not isinstance(trigger['duration'], str):
                logger.error("Trigger member is not string; trigger='{}'".format(trigger))
                return False
            if not Config.validate_duration(trigger['duration']):
                logger.error("Trigger member is not a valid duration; duration='{}'".format(trigger['duration']))
                return False

        for silence in Config.yaml['silences']:
            if not isinstance(silence['idx'], int) or not isinstance(silence['duration'], str):
                logger.error("idx is not a number or duration is not a string; silence='{}'".format(silence))
                return False
            if not Config.validate_duration(silence['duration']):
                logger.error("Silence member is not a valid duration; duration='{}'".format(silence['duration']))
                return False

        return True

    def get_duration_in_sec(duration):
        postfix = duration[-1]
        multiplier = 1
        if postfix == 'm':
            multiplier = 60
        elif postfix == 'h':
            multiplier = 60 * 60
        elif postfix == 'd':
            multiplier = 60 * 60 * 24
        elif postfix == 'w':
            multiplier = 60 * 60 * 24 * 7

        return int(duration[:-1] * multiplier)

    def validate_duration(duration):
        postfixes = ['s', 'm', 'h', 'd', 'w']
        if len(duration) < 2:
            logger.error("Duration must be at least 2 characters long")
            return False

        if duration[-1] not in postfixes:
            logger.error("Duration postfix must be: s, m, h, d, w")
            return False

        if not duration[:-1].isnumeric():
            logger.error("Duration must be a number")
            return False

        return True

    def read():
        logger.debug("Reading config from %s" % Config.config)
        try:
          with open(Config.config, "r") as f:
              Config.yaml = yaml.load(f, Loader = yaml.FullLoader)
              logger.debug("Config: %s" % Config.yaml)
        except:
            logger.error("Couldn't read config from %s" % Config.config)
            return False

        return Config._validate_config()

    def write():
        logger.debug("Writing config to %s" % Config.config)
        try:
            with open(Config.config, "w") as f:
                yaml.dump(Config.yaml, f, default_flow_style = False, encoding = 'utf-8', allow_unicode = True)
        except:
            return False

        return True

    def token_get():
        try:
            return Config.yaml['telegram']['token']
        except:
            return ""

    def chatid_get():
        try:
            return int(Config.yaml['telegram']['chat-id'])
        except:
            return 0

    def trigger_list():
        return Config.yaml['triggers']

    def trigger_exists(regexp):
        idx=0
        for t in Config.yaml['triggers']:
            if t['regexp'] == regexp:
                logger.warning("trigger '%s' exists at idx %d" % (regexp, idx))
                return True
            idx += 1
        return False

    def trigger_add(regexp, duration="10s", message=""):
        if Config.trigger_exists(regexp):
            msg = "trigger '%s' already exists" % regexp
            logger.warning(msg)
            return [False, msg]

        Config.yaml['triggers'].append({"regexp": regexp, "duration": duration, "message": message })
        ret = True
        if not Config.write():
            msg = "Error writing config to %s" % Config.config
            logger.error(msg)
            ret = False
        else:
            msg = "added trigger '%s' duration %s message '%s'" % (regexp, duration, message)
            logger.debug(msg)

        return [ret, msg]

    def trigger_del(idx):
        if idx < 0 or idx >= len(Config.yaml['triggers']):
          msg = "trigger idx out of bounds (0..%d)" % (len(Config.yaml['triggers'])-1)
          logger.warning(msg)
          return [False, msg]

        del Config.yaml['triggers'][idx]
        ret = True
        if not Config.write():
            msg = "Error writing config to %s" % Config.config
            logger.error(msg)
            ret = False
        else:
            msg = "removed trigger index %d" % idx
            logger.debug(msg)

        return [ret, msg]

    def silence_list():
        return Config.yaml['silences']

    def silence_exists(index):
        idx=0
        for t in Config.yaml['silences']:
            if t['idx'] == index:
                logger.warning("silence for trigger '%d' exists at idx %d" % (index, idx))
                return True
            idx += 1
        return False

    def silence_add(idx, duration="3600s", message=""):
        logger.debug("Adding silence for trigger '%d' duration '%s'" % (idx, duration))
        if Config.silence_exists(idx):
            msg = "silence for trigger '%d' already exists" % idx
            logger.warning(msg)
            return [False, msg]

        #expiry = time.time() + duration
        Config.yaml['silences'].append({"idx": idx, "duration": duration})
        #expiry_str = datetime.utcfromtimestamp(expiry).strftime('%Y-%m-%d %H:%M:%S UTC')
        msg = "added silence for trigger '%d' duration '%s'" % (idx, duration)
        return [True, msg]

    def silence_del(idx):
        if idx < 0 or idx >= len(Config.yaml['silences']):
          msg = "silence idx out of bounds (0..%d)" % (len(Config.yaml['silences'])-1)
          logger.warning(msg)
          return [False, msg]

        del Config.yaml['silences'][idx]
        msg = "removed silence index %d" % idx
        logger.debug(msg)
        return [True, msg]
