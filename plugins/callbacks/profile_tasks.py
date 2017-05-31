# (C) 2015, Tom Paine, <github@aioue.net>
# (C) 2014, Jharrod LaFon, @JharrodLaFon
# (C) 2012-2013, Michael DeHaan, <michael.dehaan@gmail.com>
#
# This file is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# File is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# See <http://www.gnu.org/licenses/> for a copy of the
# GNU General Public License

# Provides per-task timing, ongoing playbook elapsed time and
# ordered list of top 20 longest running tasks at end

import time

from ansible.callbacks import display


# define start time
t0 = tn = time.time()


def secondsToStr(t):
    # http://bytes.com/topic/python/answers/635958-handy-short-cut-formatting-elapsed-time-floating-point-seconds
    rediv = lambda ll, b: list(divmod(ll[0], b)) + ll[1:]
    return "%d:%02d:%02d.%03d" % tuple(reduce(rediv, [[t * 1000, ], 1000, 60, 60]))


def filled(msg, fchar="*"):
    if len(msg) == 0:
        width = 79
    else:
        msg = "%s " % msg
        width = 79 - len(msg)
    if width < 3:
        width = 3
    filler = fchar * width
    return "%s%s " % (msg, filler)


def timestamp(self):
    if self.current is not None:
        self.stats[self.current] = time.time() - self.stats[self.current]


def tasktime():
    global tn
    time_current = time.strftime('%A %d %B %Y  %H:%M:%S %z')
    time_elapsed = secondsToStr(time.time() - tn)
    time_total_elapsed = secondsToStr(time.time() - t0)
    display(filled('%s (%s)%s%s' % (time_current, time_elapsed, ' ' * 7, time_total_elapsed)))
    tn = time.time()


class CallbackModule(object):

    def __init__(self):
        self.stats = {}
        self.current = None

    def playbook_on_task_start(self, name, is_conditional):
        """
        Logs the start of each task
        """
        tasktime()
        timestamp(self)

        # Record the start time of the current task
        self.current = name
        self.stats[self.current] = time.time()

    def playbook_on_setup(self):
        tasktime()

    def playbook_on_stats(self, stats):
        tasktime()
        display(filled("", fchar="="))

        timestamp(self)

        # Sort the tasks by their running time
        results = sorted(
            self.stats.items(),
            key=lambda value: value[1],
            reverse=True,
        )

        # Just keep the top 20
        results = results[:20]

        # Print the timings
        for name, elapsed in results:
            print(
                "{0:-<70}{1:->9}".format(
                    '{0} '.format(name),
                    ' {0:.02f}s'.format(elapsed),
                )
            )
        print ''
