# (c) 2016, Dag Wieers <dag@wieers.com>
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
from ansible.utils.color import colorize, hostcolor
from collections import OrderedDict

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

import sys

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
#  + Rewrite the output during processing
#    - We use the cursor to indicate where in the task we are.
#      Output after the prompt is the output of the previous task.
#    - If we would clear the line at the start of a task, there would often
#      be no information at all, so we leave it until it gets updated
#
#  + Use the same color-conventions of Ansible
#
#  + Ensure the verbose output (-v) is also dense.
#    Remove information that is not essential (eg. timestamps, status)


# TODO:
#
#  + Properly test for terminal capabilities, and fall back to default
#  + Modify Ansible mechanism so we don't need to use sys.stdout directly
#  + Find an elegant solution for progress bar line wrapping

# When using -vv or higher, simply do the default action

# FIXME: Importing constants as C simply does not work, beats me :-/
#from ansible import constants as C
class C:
    COLOR_HIGHLIGHT   = 'white'
    COLOR_VERBOSE     = 'blue'
    COLOR_WARN        = 'bright purple'
    COLOR_ERROR       = 'red'
    COLOR_DEBUG       = 'dark gray'
    COLOR_DEPRECATE   = 'purple'
    COLOR_SKIP        = 'cyan'
    COLOR_UNREACHABLE = 'bright red'
    COLOR_OK          = 'green'
    COLOR_CHANGED     = 'yellow'


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


colors = dict(
    ok = ansi.darkgreen,
    changed = ansi.darkyellow,
    skipped = ansi.darkcyan,
    ignored = ansi.cyanbg + ansi.red,
    failed = ansi.darkred,
    unreachable = ansi.red,
)

states = ( 'skipped', 'ok', 'changed', 'failed', 'unreachable' )

class CallbackModule_dense(CallbackModule_default):

    '''
    This is the dense callback interface, where screen estate is still valued.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'dense'


    def __init__(self):

        # From CallbackModule
        self._display = display

        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()

        self.hosts = OrderedDict()
        self.keep = False
        self.shown_title = False
        self.count = dict(play=0, handler=0, task=0)
        self.type = 'foo'

        # Start immediately on the first line
        sys.stdout.write(ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()
 
    def _add_host(self, result, status):
        name = result._host.get_name()

        # Add a new status in case a failed task is ignored
        if status == 'failed' and result._task.ignore_errors:
            status = 'ignored'

        # Check if we have to update an existing state (when looping over items)
        if name not in self.hosts:
            self.hosts[name] = dict(state=status)
        elif states.index(self.hosts[name]['state']) < states.index(status):
            self.hosts[name]['state'] = status

        # Store delegated hostname, if needed
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            self.hosts[name]['delegate'] = delegated_vars['ansible_host']

        # Print progress bar
        self._display_progress(result)

        # Ensure that tasks with changes/failures stay on-screen
        if status in ['changed', 'failed', 'unreachable']:
            self.keep = True

            if self._display.verbosity == 1:
                # Print task title, if needed
                self._display_task_banner()
                self._display_results(result, status)

    def _clean_results(self, result):
        # Remove non-essential atributes
        removed_attributes = ('changed', 'delta', 'end', 'failed', 'failed_when_result', 'invocation', 'start', 'stdout_lines')
        for attr in removed_attributes:
            if attr in result:
                del(result[attr])

        # Remove empty attributes (list, dict, str)
        for attr in result.copy():
            if type(result[attr]) in (list, dict, basestring, unicode):
                if not result[attr]:
                    del(result[attr])

        if 'cmd' in result:
            result['cmd'] = ' '.join(result['cmd'])

    def _handle_exceptions(self, result):
        if 'exception' in result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result['exception']

            # finally, remove the exception from the result so it's not shown every time
            del result['exception']
            return msg

    def _display_progress(self, result=None):
        # Always rewrite the complete line
        sys.stdout.write(ansi.restore + ansi.clearline + ansi.underline)
        sys.stdout.write('%s %d:' % (self.type, self.count[self.type]))
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

        # Print out each host in its own status-color
        for name in self.hosts:
            sys.stdout.write(' ')
            if self.hosts[name].get('delegate', None):
                sys.stdout.write(self.hosts[name]['delegate'] + '>')
            sys.stdout.write(colors[self.hosts[name]['state']] + name + ansi.reset)
            sys.stdout.flush()

    def _display_task_banner(self):
        if not self.shown_title:
            self.shown_title = True
            sys.stdout.write(ansi.restore + ansi.clearline)
            sys.stdout.write(ansi.underline + '%s %d: %s' % (self.type, self.count[self.type], self.task.get_name().strip()))
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
            sys.stdout.flush()
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)

    def _display_results(self, result, status):
        dump = ''
        self._clean_results(result._result)

        if result._task.action == 'include':
            return
        elif status == 'ok':
            return
        elif status == 'changed':
            color = C.COLOR_CHANGED
        elif status == 'ignored':
            color = C.COLOR_SKIPPED
            dump = self._handle_exceptions(result._result)
        elif status == 'failed':
            color = C.COLOR_ERROR
            dump = self._handle_exceptions(result._result)
        elif status == 'unreachable':
            color = C.COLOR_UNREACHABLE
            dump = result._result['msg']

        if not dump:
            dump = self._dump_results(result._result)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if delegated_vars:
            msg = "%s: %s>%s: %s" % (status, result._host.get_name(), delegated_vars['ansible_host'], dump)
        else:
            msg = "%s: %s: %s" % (status, result._host.get_name(), dump)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:
            self._display.display(msg, color=color)

        if status == 'changed':
            self._handle_warnings(result._result)

    def v2_playbook_on_play_start(self, play):
        if self._display.verbosity > 1:
            self.super_ref.v2_playbook_on_play_start(play)
            return

        # Reset at the start of each play
        self.count.update(dict(handler=0, task=0))
        self.count['play'] += 1
        self.play = play

        # Leave the previous task on screen (as it has changes/errors)
        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline + ansi.bold)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline + ansi.bold)

        # Write the next play on screen IN UPPERCASE, and make it permanent
        name = play.get_name().strip()
        if not name:
            name = 'unnamed'
        sys.stdout.write('PLAY %d: %s' % (self.count['play'], name.upper()))
        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

    def v2_playbook_on_task_start(self, task, is_conditional):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline + ansi.underline)
        else:
            sys.stdout.write(ansi.restore + ansi.underline)

        # Reset at the start of each task
        self.keep = False
        self.shown_title = False
        self.hosts = OrderedDict()
        self.task = task
        self.type = 'task'

        # Enumerate task if not setup (task names are too long for dense output)
        if task.get_name() != 'setup':
            self.count['task'] += 1

        # Write the next task on screen (behind the prompt is the previous output)
        sys.stdout.write('%s %d.' % (self.type, self.count[self.type]))
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

    def v2_playbook_on_handler_task_start(self, task):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline + ansi.underline)
        else:
            sys.stdout.write(ansi.restore + ansi.reset + ansi.underline)

        # Reset at the start of each handler
        self.keep = False
        self.shown_title = False
        self.hosts = OrderedDict()
        self.task = task
        self.type = 'handler'

        # Enumerate handler if not setup (handler names may be too long for dense output)
        if task.get_name() != 'setup':
            self.count[self.type] += 1

        # Write the next task on screen (behind the prompt is the previous output)
        sys.stdout.write('%s %d.' % (self.type, self.count[self.type]))
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

    def v2_playbook_on_cleanup_task_start(self, task):
        # TBD
        sys.stdout.write('cleanup.')
        sys.stdout.write(ansi.reset)
        sys.stdout.flush()

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._add_host(result, 'failed')

    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            self._add_host(result, 'changed')
        else:
            self._add_host(result, 'ok')

    def v2_runner_on_skipped(self, result):
        self._add_host(result, 'skipped')

    def v2_runner_on_unreachable(self, result):
        self._add_host(result, 'unreachable')

    def v2_runner_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        if result._result.get('changed', False):
            self._add_host(result, 'changed')
        else:
            self._add_host(result, 'ok')

    def v2_playbook_item_on_failed(self, result):
        self._add_host(result, 'failed')

    def v2_playbook_item_on_skipped(self, result):
        self._add_host(result, 'skipped')

    def v2_playbook_on_no_hosts_remaining(self):
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline)

        # Reset keep
        self.keep = False

        sys.stdout.write(ansi.white + ansi.redbg + 'NO MORE HOSTS LEFT' + ansi.reset)
        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

    def v2_playbook_on_stats(self, stats):
        # In normal mode screen output should be sufficient
        if self._display.verbosity == 0:
            return

        if self.keep:
            sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.clearline + ansi.bold)
        else:
            sys.stdout.write(ansi.restore + ansi.clearline + ansi.bold)

        sys.stdout.write('SUMMARY')

        sys.stdout.write(ansi.restore + '\n' + ansi.save + ansi.reset + ansi.clearline)
        sys.stdout.flush()

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self._display.display(u"%s : %s %s %s %s" % (
                hostcolor(h, t),
                colorize(u'ok', t['ok'], C.COLOR_OK),
                colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

if display.verbosity >= 2:
    CallbackModule = CallbackModule_default
else:
    CallbackModule = CallbackModule_dense