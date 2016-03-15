# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

import sys
import time


# Design goals:
#
#  + On screen there should only be relevant stuff
#    - How far are we ? (during run, last line)
#    - What issues did we have
#    - What changes have occured
#    - Diff output
#
#  + If verbosity increases, act as default output
#    So that users can easily switch to default for troubleshooting
#
#  + Leave previous task output on screen
#    - If we would clear the line at the start of a task, there would often
#      be no information at all
#
#    - We use the cursor to indicate where in the task we are.
#      Output after the prompt is the output of the previous task
#
#    - Use the same color-conventions of Ansible


# TODO:
#
#  + Ensure all other output is properly displayed
#  + Properly test for terminal capabilities, and fall back to default
#  + Modify Ansible mechanism so we don't need to use sys.stdout directly
#  + Check verbosity 1, display task details on change/failure !
#  + Check verbosity 2, use default callback for everything


# Taken from Dstat
class ansi:
    black = '\033[0;30m'
    darkred = '\033[0;31m'
    darkgreen = '\033[0;32m'
    darkyellow = '\033[0;33m'
    darkblue = '\033[0;34m'
    darkmagenta = '\033[0;35m'
    darkcyan = '\033[0;36m'
    gray = '\033[0;37m'

    darkgray = '\033[1;30m'
    red = '\033[1;31m'
    green = '\033[1;32m'
    yellow = '\033[1;33m'
    blue = '\033[1;34m'
    magenta = '\033[1;35m'
    cyan = '\033[1;36m'
    white = '\033[1;37m'

    blackbg = '\033[40m'
    redbg = '\033[41m'
    greenbg = '\033[42m'
    yellowbg = '\033[43m'
    bluebg = '\033[44m'
    magentabg = '\033[45m'
    cyanbg = '\033[46m'
    whitebg = '\033[47m'

    reset = '\033[0;0m'
    bold = '\033[1m'
    reverse = '\033[2m'
    underline = '\033[4m'

    clear = '\033[2J'
#   clearline = '\033[K'
    clearline = '\033[2K'
#   save = '\033[s'
#   restore = '\033[u'
    save = '\0337'
    restore = '\0338'
    linewrap = '\033[7h'
    nolinewrap = '\033[7l'

    up = '\033[1A'
    down = '\033[1B'
    right = '\033[1C'
    left = '\033[1D'

    default = '\033[0;0m'


class CallbackModule(CallbackModule_default):

    '''
    This is the dense callback interface, which tries to save screen estate.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'dense'

    hosts = []
    keep = False
#    task = ''
    tasknr = 0

    def __init__(self):
        sys.stdout.write(ansi.save + ansi.clearline)
        sys.stdout.flush()
 
    def _add_host(self, name, status):
        # Ensure that tasks with changes/failures stay on-screen
        if not self.keep and status in ['changed', 'failed', 'unreachable']:
            self.keep = True
        self.hosts.append((name, status))
        self._print_status()

    def _print_status(self):
        # Always rewrite the complete line
        sys.stdout.write(ansi.restore)
        sys.stdout.write(ansi.clearline)
        sys.stdout.write('- task %d:  ' % self.tasknr)
        sys.stdout.flush()

        # Print out each host with its own status-color
        for name, status in self.hosts:
            if status == 'ok':
                color = ansi.darkgreen
            elif status == 'changed':
                color = ansi.yellow
            elif status == 'skipped':
                color = ansi.darkcyan
            elif status == 'failed':
                color = ansi.darkred
            elif status == 'unreachable':
                color = ansi.white + ansi.redbg
#        if self.hosts and self.hosts[-1][1] in ['changed', 'failed']:
#            sys.stdout.write('<-' + ansi.restore + '\n' + ansi.save)
            sys.stdout.write(color + name + ansi.default + ' ')
            sys.stdout.flush()

        # Place cursor at start of the line
        sys.stdout.write(ansi.default)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._add_host(result._host.get_name(), 'failed')

    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            self._add_host(result._host.get_name(), 'changed')
        else:
            self._add_host(result._host.get_name(), 'ok')

    def v2_runner_on_skipped(self, result):
        self._add_host(result._host.get_name(), 'skipped')

    def v2_runner_on_unreachable(self, result):
        self._add_host(result._host.get_name(), 'unreachable')

    def v2_playbook_item_on_skipped(self, result):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        # TBD
        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)

        sys.stdout.write(ansi.white + ansi.redbg + 'NO MORE HOSTS LEFT' + ansi.default)
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

    def v2_playbook_on_task_start(self, task, is_conditional):
        # Leave the previous task on screen (as it has changes/errors)
        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline)
        # Reset counters at the start of each new task
        self.keep = False
        self.hosts = []
        # Enumerate task (task names are too long for dense output)
        self.tasknr += 1
#        self.task = task.get_name().strip()
        # Write the next task on screen (behind the prompt is the previous output)
        sys.stdout.write(ansi.restore)
        sys.stdout.write('- task %d|' % self.tasknr)
        sys.stdout.flush()

    def v2_playbook_on_play_start(self, play):
        self.tasknr = 0
        # Leave the previous task on screen (as it has changes/errors)
        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)
        name = play.get_name().strip()
        if name:
            sys.stdout.write('PLAY [%s]' % name)
        else:
            sys.stdout.write('PLAY')
        # Always leave the PLAY output on screen
        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline)
        sys.stdout.flush()