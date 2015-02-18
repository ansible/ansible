import os
import datetime
from datetime import datetime, timedelta


class CallbackModule(object):
    """
    This callback module tells you how long your plays ran for.
    """

    start_time = datetime.now()
    
    def __init__(self):
        start_time = datetime.now()
        print "Timer plugin is active."

    def days_hours_minutes_seconds(self, timedelta):
        minutes = (timedelta.seconds//60)%60
        r_seconds = timedelta.seconds - (minutes * 60)
        return timedelta.days, timedelta.seconds//3600, minutes, r_seconds

    def playbook_on_stats(self, stats):
        end_time = datetime.now()
        timedelta = end_time - self.start_time
        print "Playbook run took %s days, %s hours, %s minutes, %s seconds" % (self.days_hours_minutes_seconds(timedelta))


