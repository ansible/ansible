import os
import datetime
from datetime import datetime, timedelta

from ansible.plugins.callback import CallbackBase

class CallbackModule(CallbackBase):
    """
    This callback module tells you how long your plays ran for.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'timer'

    def __init__(self, display):

        super(CallbackModule, self).__init__(display)

        self.start_time = datetime.now()

    def days_hours_minutes_seconds(self, timedelta):
        minutes = (timedelta.seconds//60)%60
        r_seconds = timedelta.seconds - (minutes * 60)
        return timedelta.days, timedelta.seconds//3600, minutes, r_seconds

    def playbook_on_stats(self, stats):
        self.v2_playbook_on_stats(stats)

    def v2_playbook_on_stats(self, stats):
        end_time = datetime.now()
        timedelta = end_time - self.start_time
        self._display.display("Playbook run took %s days, %s hours, %s minutes, %s seconds" % (self.days_hours_minutes_seconds(timedelta)))

