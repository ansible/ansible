# (C) 2016, Joel, http://github.com/jjshoe 
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import collections
import os
import time

from ansible.plugins.callback import CallbackBase

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
        self.stats[self.current]['time'] = time.time() - self.stats[self.current]['time']


def tasktime():
    global tn
    time_current = time.strftime('%A %d %B %Y  %H:%M:%S %z')
    time_elapsed = secondsToStr(time.time() - tn)
    time_total_elapsed = secondsToStr(time.time() - t0)
    tn = time.time()
    return filled('%s (%s)%s%s' % (time_current, time_elapsed, ' ' * 7, time_total_elapsed))


class CallbackModule(CallbackBase):
    """
    This callback module provides per-task timing, ongoing playbook elapsed time
    and ordered list of top 20 longest running tasks at end.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'profile_tasks'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        self.stats = collections.OrderedDict()
        self.current = None
        self.sort_order = os.getenv('PROFILE_TASKS_SORT_ORDER', True)
        self.task_output_limit = os.getenv('PROFILE_TASKS_TASK_OUTPUT_LIMIT', 20)

        if self.sort_order == 'ascending':
            self.sort_order = False;

        if self.task_output_limit == 'all':
            self.task_output_limit = None
        else:
            self.task_output_limit = int(self.task_output_limit) 

        super(CallbackModule, self).__init__()

    def _record_task(self, task):
        """
        Logs the start of each task
        """
        self._display.display(tasktime())
        timestamp(self)

        # Record the start time of the current task
        self.current = task._uuid
        self.stats[self.current] = {'time': time.time(), 'name': task.get_name()}
        if self._display.verbosity >= 2:
            self.stats[self.current][ 'path'] = task.get_path()

    def v2_playbook_on_task_start(self, task, is_conditional):
        self._record_task(task)

    def v2_playbook_on_handler_task_start(self, task):
        self._record_task(task)

    def playbook_on_setup(self):
        self._display.display(tasktime())

    def playbook_on_stats(self, stats):
        self._display.display(tasktime())
        self._display.display(filled("", fchar="="))

        timestamp(self)

        results = self.stats.items() 

        # Sort the tasks by the specified sort
        if self.sort_order != 'none':
            results = sorted(
                self.stats.iteritems(),
                key=lambda x:x[1]['time'],
                reverse=self.sort_order,
            )

        # Display the number of tasks specified or the default of 20 
        results = results[:self.task_output_limit]

        # Print the timings
        for uuid, result in results:
            msg = ''
            msg="{0:-<70}{1:->9}".format('{0} '.format(result['name']),' {0:.02f}s'.format(result['time']))
            if 'path' in result:
                msg += "\n{0:-<79}".format( '{0} '.format(result['path']))
            self._display.display(msg)
