# (C) 2016, Joel, https://github.com/jjshoe
# (C) 2015, Tom Paine, <github@aioue.net>
# (C) 2014, Jharrod LaFon, @JharrodLaFon
# (C) 2012-2013, Michael DeHaan, <michael.dehaan@gmail.com>
# (C) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: profile_tasks
    type: aggregate
    short_description: adds time information to tasks
    version_added: "2.0"
    description:
      - Ansible callback plugin for timing individual tasks and overall execution time.
      - "Mashup of 2 excellent original works: https://github.com/jlafon/ansible-profile,
         https://github.com/junaid18183/ansible_home/blob/master/ansible_plugins/callback_plugins/timestamp.py.old"
      - "Format: C(<task start timestamp> (<length of previous task>) <current elapsed playbook execution time>)"
      - It also lists the top/bottom time consuming tasks in the summary (configurable)
      - Before 2.4 only the environment variables were available for configuration.
    requirements:
      - whitelisting in configuration - see examples section below for details.
    options:
      output_limit:
        description: Number of tasks to display in the summary
        default: 20
        env:
          - name: PROFILE_TASKS_TASK_OUTPUT_LIMIT
        ini:
          - section: callback_profile_tasks
            key: task_output_limit
      sort_order:
        description: Adjust the sorting output of summary tasks
        choices: ['descending', 'ascending', 'none']
        default: 'descending'
        env:
          - name: PROFILE_TASKS_SORT_ORDER
        ini:
          - section: callback_profile_tasks
            key: sort_order
'''

EXAMPLES = '''
example: >
  To enable, add this to your ansible.cfg file in the defaults block
    [defaults]
    callback_whitelist = profile_tasks
sample output: >
#
#    TASK: [ensure messaging security group exists] ********************************
#    Thursday 11 June 2017  22:50:53 +0100 (0:00:00.721)       0:00:05.322 *********
#    ok: [localhost]
#
#    TASK: [ensure db security group exists] ***************************************
#    Thursday 11 June 2017  22:50:54 +0100 (0:00:00.558)       0:00:05.880 *********
#    changed: [localhost]
#
'''

import collections
import time

from ansible.module_utils.six.moves import reduce
from ansible.plugins.callback import CallbackBase


# define start time
t0 = tn = time.time()


def secondsToStr(t):
    # http://bytes.com/topic/python/answers/635958-handy-short-cut-formatting-elapsed-time-floating-point-seconds
    def rediv(ll, b):
        return list(divmod(ll[0], b)) + ll[1:]

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

        self.sort_order = None
        self.task_output_limit = None

        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.sort_order = self.get_option('sort_order')
        if self.sort_order is not None:
            if self.sort_order == 'ascending':
                self.sort_order = False
            elif self.sort_order == 'descending':
                self.sort_order = True
            elif self.sort_order == 'none':
                self.sort_order = None

        self.task_output_limit = self.get_option('output_limit')
        if self.task_output_limit is not None:
            if self.task_output_limit == 'all':
                self.task_output_limit = None
            else:
                self.task_output_limit = int(self.task_output_limit)

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
            self.stats[self.current]['path'] = task.get_path()

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
        self.current = None

        results = list(self.stats.items())

        # Sort the tasks by the specified sort
        if self.sort_order is not None:
            results = sorted(
                self.stats.items(),
                key=lambda x: x[1]['time'],
                reverse=self.sort_order,
            )

        # Display the number of tasks specified or the default of 20
        results = list(results)[:self.task_output_limit]

        # Print the timings
        for uuid, result in results:
            msg = u"{0:-<{2}}{1:->9}".format(result['name'] + u' ', u' {0:.02f}s'.format(result['time']), self._display.columns - 9)
            if 'path' in result:
                msg += u"\n{0:-<{1}}".format(result['path'] + u' ', self._display.columns)
            self._display.display(msg)
