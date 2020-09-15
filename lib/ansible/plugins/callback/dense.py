# (c) 2016, Dag Wieers <dag@wieers.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
callback: dense
type: stdout
short_description: minimal stdout output
extends_documentation_fragment:
- default_callback
description:
- When in verbose mode it will act the same as the default callback
author:
- Dag Wieers (@dagwieers)
version_added: "2.3"
requirements:
- set as stdout in configuation
'''

HAS_OD = False
try:
    from collections import OrderedDict
    HAS_OD = True
except ImportError:
    pass

from ansible.module_utils.six import binary_type, text_type
from ansible.module_utils.common._collections_compat import MutableMapping, MutableSequence
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.utils.color import colorize, hostcolor
from ansible.utils.display import Display

import sys

display = Display()


# Design goals:
#
#  + On screen there should only be relevant stuff
#    - How far are we ? (during run, last line)
#    - What issues occurred
#    - What changes occurred
#    - Diff output (in diff-mode)
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


# FIXME: Importing constants as C simply does not work, beats me :-/
# from ansible import constants as C
class C:
    COLOR_HIGHLIGHT = 'white'
    COLOR_VERBOSE = 'blue'
    COLOR_WARN = 'bright purple'
    COLOR_ERROR = 'red'
    COLOR_DEBUG = 'dark gray'
    COLOR_DEPRECATE = 'purple'
    COLOR_SKIP = 'cyan'
    COLOR_UNREACHABLE = 'bright red'
    COLOR_OK = 'green'
    COLOR_CHANGED = 'yellow'


# Taken from Dstat
class vt100:
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
#    clearline = '\033[K'
    clearline = '\033[2K'
    save = '\033[s'
    restore = '\033[u'
    save_all = '\0337'
    restore_all = '\0338'
    linewrap = '\033[7h'
    nolinewrap = '\033[7l'

    up = '\033[1A'
    down = '\033[1B'
    right = '\033[1C'
    left = '\033[1D'


colors = dict(
    ok=vt100.darkgreen,
    changed=vt100.darkyellow,
    skipped=vt100.darkcyan,
    ignored=vt100.cyanbg + vt100.red,
    failed=vt100.darkred,
    unreachable=vt100.red,
)

states = ('skipped', 'ok', 'changed', 'failed', 'unreachable')


class CallbackModule(CallbackModule_default):

    '''
    This is the dense callback interface, where screen estate is still valued.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'dense'

    def __init__(self):

        # From CallbackModule
        self._display = display

        if HAS_OD:

            self.disabled = False
            self.super_ref = super(CallbackModule, self)
            self.super_ref.__init__()

            # Attributes to remove from results for more density
            self.removed_attributes = (
                #                'changed',
                'delta',
                #                'diff',
                'end',
                'failed',
                'failed_when_result',
                'invocation',
                'start',
                'stdout_lines',
            )

            # Initiate data structures
            self.hosts = OrderedDict()
            self.keep = False
            self.shown_title = False
            self.count = dict(play=0, handler=0, task=0)
            self.type = 'foo'

            # Start immediately on the first line
            sys.stdout.write(vt100.reset + vt100.save + vt100.clearline)
            sys.stdout.flush()
        else:
            display.warning("The 'dense' callback plugin requires OrderedDict which is not available in this version of python, disabling.")
            self.disabled = True

    def __del__(self):
        sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)

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

#        # Ensure that tasks with changes/failures stay on-screen, and during diff-mode
#        if status in ['changed', 'failed', 'unreachable'] or (result.get('_diff_mode', False) and result._resultget('diff', False)):
        # Ensure that tasks with changes/failures stay on-screen
        if status in ['changed', 'failed', 'unreachable']:
            self.keep = True

            if self._display.verbosity == 1:
                # Print task title, if needed
                self._display_task_banner()
                self._display_results(result, status)

    def _clean_results(self, result):
        # Remove non-essential atributes
        for attr in self.removed_attributes:
            if attr in result:
                del(result[attr])

        # Remove empty attributes (list, dict, str)
        for attr in result.copy():
            if isinstance(result[attr], (MutableSequence, MutableMapping, binary_type, text_type)):
                if not result[attr]:
                    del(result[attr])

    def _handle_exceptions(self, result):
        if 'exception' in result:
            # Remove the exception from the result so it's not shown every time
            del result['exception']

            if self._display.verbosity == 1:
                return "An exception occurred during task execution. To see the full traceback, use -vvv."

    def _display_progress(self, result=None):
        # Always rewrite the complete line
        sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline + vt100.nolinewrap + vt100.underline)
        sys.stdout.write('%s %d:' % (self.type, self.count[self.type]))
        sys.stdout.write(vt100.reset)
        sys.stdout.flush()

        # Print out each host in its own status-color
        for name in self.hosts:
            sys.stdout.write(' ')
            if self.hosts[name].get('delegate', None):
                sys.stdout.write(self.hosts[name]['delegate'] + '>')
            sys.stdout.write(colors[self.hosts[name]['state']] + name + vt100.reset)
            sys.stdout.flush()

#        if result._result.get('diff', False):
#            sys.stdout.write('\n' + vt100.linewrap)
        sys.stdout.write(vt100.linewrap)

#        self.keep = True

    def _display_task_banner(self):
        if not self.shown_title:
            self.shown_title = True
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline + vt100.underline)
            sys.stdout.write('%s %d: %s' % (self.type, self.count[self.type], self.task.get_name().strip()))
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
            sys.stdout.flush()
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline)
        self.keep = False

    def _display_results(self, result, status):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline)
        self.keep = False

        self._clean_results(result._result)

        dump = ''
        if result._task.action == 'include':
            return
        elif status == 'ok':
            return
        elif status == 'ignored':
            dump = self._handle_exceptions(result._result)
        elif status == 'failed':
            dump = self._handle_exceptions(result._result)
        elif status == 'unreachable':
            dump = result._result['msg']

        if not dump:
            dump = self._dump_results(result._result)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:
            sys.stdout.write(colors[status] + status + ': ')

            delegated_vars = result._result.get('_ansible_delegated_vars', None)
            if delegated_vars:
                sys.stdout.write(vt100.reset + result._host.get_name() + '>' + colors[status] + delegated_vars['ansible_host'])
            else:
                sys.stdout.write(result._host.get_name())

            sys.stdout.write(': ' + dump + '\n')
            sys.stdout.write(vt100.reset + vt100.save + vt100.clearline)
            sys.stdout.flush()

        if status == 'changed':
            self._handle_warnings(result._result)

    def v2_playbook_on_play_start(self, play):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline + vt100.bold)
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline + vt100.bold)

        # Reset at the start of each play
        self.keep = False
        self.count.update(dict(handler=0, task=0))
        self.count['play'] += 1
        self.play = play

        # Write the next play on screen IN UPPERCASE, and make it permanent
        name = play.get_name().strip()
        if not name:
            name = 'unnamed'
        sys.stdout.write('PLAY %d: %s' % (self.count['play'], name.upper()))
        sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        sys.stdout.flush()

    def v2_playbook_on_task_start(self, task, is_conditional):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline + vt100.underline)
        else:
            # Do not clear line, since we want to retain the previous output
            sys.stdout.write(vt100.restore + vt100.reset + vt100.underline)

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
        sys.stdout.write(vt100.reset)
        sys.stdout.flush()

    def v2_playbook_on_handler_task_start(self, task):
        # Leave the previous task on screen (as it has changes/errors)
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline + vt100.underline)
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline + vt100.underline)

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
        sys.stdout.write(vt100.reset)
        sys.stdout.flush()

    def v2_playbook_on_cleanup_task_start(self, task):
        # TBD
        sys.stdout.write('cleanup.')
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

    def v2_runner_on_file_diff(self, result, diff):
        sys.stdout.write(vt100.bold)
        self.super_ref.v2_runner_on_file_diff(result, diff)
        sys.stdout.write(vt100.reset)

    def v2_on_file_diff(self, result):
        sys.stdout.write(vt100.bold)
        self.super_ref.v2_on_file_diff(result)
        sys.stdout.write(vt100.reset)

    # Old definition in v2.0
    def v2_playbook_item_on_ok(self, result):
        self.v2_runner_item_on_ok(result)

    def v2_runner_item_on_ok(self, result):
        if result._result.get('changed', False):
            self._add_host(result, 'changed')
        else:
            self._add_host(result, 'ok')

    # Old definition in v2.0
    def v2_playbook_item_on_failed(self, result):
        self.v2_runner_item_on_failed(result)

    def v2_runner_item_on_failed(self, result):
        self._add_host(result, 'failed')

    # Old definition in v2.0
    def v2_playbook_item_on_skipped(self, result):
        self.v2_runner_item_on_skipped(result)

    def v2_runner_item_on_skipped(self, result):
        self._add_host(result, 'skipped')

    def v2_playbook_on_no_hosts_remaining(self):
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline)
        self.keep = False

        sys.stdout.write(vt100.white + vt100.redbg + 'NO MORE HOSTS LEFT')
        sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        sys.stdout.flush()

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_on_stats(self, stats):
        if self._display.verbosity == 0 and self.keep:
            sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        else:
            sys.stdout.write(vt100.restore + vt100.reset + vt100.clearline)

        # In normal mode screen output should be sufficient, summary is redundant
        if self._display.verbosity == 0:
            return

        sys.stdout.write(vt100.bold + vt100.underline)
        sys.stdout.write('SUMMARY')

        sys.stdout.write(vt100.restore + vt100.reset + '\n' + vt100.save + vt100.clearline)
        sys.stdout.flush()

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)
            self._display.display(
                u"%s : %s %s %s %s %s %s" % (
                    hostcolor(h, t),
                    colorize(u'ok', t['ok'], C.COLOR_OK),
                    colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                    colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                    colorize(u'failed', t['failures'], C.COLOR_ERROR),
                    colorize(u'rescued', t['rescued'], C.COLOR_OK),
                    colorize(u'ignored', t['ignored'], C.COLOR_WARN),
                ),
                screen_only=True
            )


# When using -vv or higher, simply do the default action
if display.verbosity >= 2 or not HAS_OD:
    CallbackModule = CallbackModule_default
