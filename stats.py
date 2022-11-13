import logging
import time
from datetime import datetime

class NullHandler(logging.Handler):
    def emit(self, record):
        pass
logger = logging.getLogger('pttb.stats')
logger.addHandler(NullHandler())

class Stats():
    starttime = None
    loglines_read_num = 0
    incidents_created_num = 0
    incidents_silenced_num = 0
    incidents_sent_num = 0

    @staticmethod
    def start():
        Stats.starttime = time.time()

    def loglines_read():
        Stats.loglines_read_num += 1

    def incidents_created():
        Stats.incidents_created_num += 1

    def incidents_silenced():
        Stats.incidents_silenced_num += 1

    def incidents_sent():
        Stats.incidents_sent_num += 1

    def get_stats():
        msg = "'starttime' : '{}'\n".format(datetime.fromtimestamp(Stats.starttime).strftime('%Y-%m-%d %H:%M:%S'))
        msg += "'loglines_read' : '{}'\n".format(Stats.loglines_read_num)
        msg += "'incidents_created' : '{}'\n".format(Stats.incidents_created_num)
        msg += "'incidents_silenced' : '{}'\n".format(Stats.incidents_silenced_num)
        msg += "'incidents_sent' : '{}'\n".format(Stats.incidents_sent_num)

        return msg
