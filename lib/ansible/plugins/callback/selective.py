# (c) Fastly, inc 2016
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    callback: selective
    callback_type: stdout
    requirements:
      - set as main display callback
    short_description: only print certain tasks
    version_added: "2.4"
    description:
      - This callback only prints tasks that have been tagged with `print_action` or that have failed.
        This allows operators to focus on the tasks that provide value only.
      - Tasks that are not printed are placed with a '.'.
      - If you increase verbosity all tasks are printed.
    options:
      nocolor:
        default: False
        description: This setting allows suppressing colorizing output
        env:
          - name: ANSIBLE_NOCOLOR
          - name: ANSIBLE_SELECTIVE_DONT_COLORIZE
        ini:
          - section: defaults
            key: nocolor
        type: boolean
"""

EXAMPLES = """
  - debug: msg="This will not be printed"
  - debug: msg="But this will"
    tags: [print_action]
"""

import difflib

from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.module_utils._text import to_text
from ansible.utils.color import codeCodes

DONT_COLORIZE = False
COLORS = {
    'normal': '\033[0m',
    'ok': '\033[{0}m'.format(codeCodes[C.COLOR_OK]),
    'bold': '\033[1m',
    'not_so_bold': '\033[1m\033[34m',
    'changed': '\033[{0}m'.format(codeCodes[C.COLOR_CHANGED]),
    'failed': '\033[{0}m'.format(codeCodes[C.COLOR_ERROR]),
    'endc': '\033[0m',
    'skipped': '\033[{0}m'.format(codeCodes[C.COLOR_SKIP]),
}


def dict_diff(prv, nxt):
    """Return a dict of keys that differ with another config object."""
    keys = set(prv.keys() + nxt.keys())
    result = {}
    for k in keys:
        if prv.get(k) != nxt.get(k):
            result[k] = (prv.get(k), nxt.get(k))
    return result


def colorize(msg, color):
    """Given a string add necessary codes to format the string."""
    if DONT_COLORIZE:
        return msg
    else:
        return '{0}{1}{2}'.format(COLORS[color], msg, COLORS['endc'])


class CallbackModule(CallbackBase):
    """selective.py callback plugin."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'selective'

    def __init__(self, display=None):
        """selective.py callback plugin."""
        super(CallbackModule, self).__init__(display)
        self.last_skipped = False
        self.last_task_name = None
        self.printed_last_task = False

    def set_options(self, task_keys=None, var_options=None, direct=None):

        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        global DONT_COLORIZE
        DONT_COLORIZE = self.get_option('nocolor')

    def _print_task(self, task_name=None):
        if task_name is None:
            task_name = self.last_task_name

        if not self.printed_last_task:
            self.printed_last_task = True
            line_length = 120
            if self.last_skipped:
                print()
            msg = colorize("# {0} {1}".format(task_name,
                                              '*' * (line_length - len(task_name))), 'bold')
            print(msg)

    def _indent_text(self, text, indent_level):
        lines = text.splitlines()
        result_lines = []
        for l in lines:
            result_lines.append("{0}{1}".format(' ' * indent_level, l))
        return '\n'.join(result_lines)

    def _print_diff(self, diff, indent_level):
        if isinstance(diff, dict):
            try:
                diff = '\n'.join(difflib.unified_diff(diff['before'].splitlines(),
                                                      diff['after'].splitlines(),
                                                      fromfile=diff.get('before_header',
                                                                        'new_file'),
                                                      tofile=diff['after_header']))
            except AttributeError:
                diff = dict_diff(diff['before'], diff['after'])
        if diff:
            diff = colorize(str(diff), 'changed')
            print(self._indent_text(diff, indent_level + 4))

    def _print_host_or_item(self, host_or_item, changed, msg, diff, is_host, error, stdout, stderr):
        if is_host:
            indent_level = 0
            name = colorize(host_or_item.name, 'not_so_bold')
        else:
            indent_level = 4
            if isinstance(host_or_item, dict):
                if 'key' in host_or_item.keys():
                    host_or_item = host_or_item['key']
            name = colorize(to_text(host_or_item), 'bold')

        if error:
            color = 'failed'
            change_string = colorize('FAILED!!!', color)
        else:
            color = 'changed' if changed else 'ok'
            change_string = colorize("changed={0}".format(changed), color)

        msg = colorize(msg, color)

        line_length = 120
        spaces = ' ' * (40 - len(name) - indent_level)
        line = "{0}  * {1}{2}- {3}".format(' ' * indent_level, name, spaces, change_string)

        if len(msg) < 50:
            line += ' -- {0}'.format(msg)
            print("{0} {1}---------".format(line, '-' * (line_length - len(line))))
        else:
            print("{0} {1}".format(line, '-' * (line_length - len(line))))
            print(self._indent_text(msg, indent_level + 4))

        if diff:
            self._print_diff(diff, indent_level)
        if stdout:
            stdout = colorize(stdout, 'failed')
            print(self._indent_text(stdout, indent_level + 4))
        if stderr:
            stderr = colorize(stderr, 'failed')
            print(self._indent_text(stderr, indent_level + 4))

    def v2_playbook_on_play_start(self, play):
        """Run on start of the play."""
        pass

    def v2_playbook_on_task_start(self, task, **kwargs):
        """Run when a task starts."""
        self.last_task_name = task.get_name()
        self.printed_last_task = False

    def _print_task_result(self, result, error=False, **kwargs):
        """Run when a task finishes correctly."""

        if 'print_action' in result._task.tags or error or self._display.verbosity > 1:
            self._print_task()
            self.last_skipped = False
            msg = to_text(result._result.get('msg', '')) or\
                to_text(result._result.get('reason', ''))

            stderr = [result._result.get('exception', None),
                      result._result.get('module_stderr', None)]
            stderr = "\n".join([e for e in stderr if e]).strip()

            self._print_host_or_item(result._host,
                                     result._result.get('changed', False),
                                     msg,
                                     result._result.get('diff', None),
                                     is_host=True,
                                     error=error,
                                     stdout=result._result.get('module_stdout', None),
                                     stderr=stderr.strip(),
                                     )
            if 'results' in result._result:
                for r in result._result['results']:
                    failed = 'failed' in r and r['failed']

                    stderr = [r.get('exception', None), r.get('module_stderr', None)]
                    stderr = "\n".join([e for e in stderr if e]).strip()

                    self._print_host_or_item(r['item'],
                                             r.get('changed', False),
                                             to_text(r.get('msg', '')),
                                             r.get('diff', None),
                                             is_host=False,
                                             error=failed,
                                             stdout=r.get('module_stdout', None),
                                             stderr=stderr.strip(),
                                             )
        else:
            self.last_skipped = True
            print('.', end="")

    def v2_playbook_on_stats(self, stats):
        """Display info about playbook statistics."""
        print()
        self.printed_last_task = False
        self._print_task('STATS')

        hosts = sorted(stats.processed.keys())
        for host in hosts:
            s = stats.summarize(host)

            if s['failures'] or s['unreachable']:
                color = 'failed'
            elif s['changed']:
                color = 'changed'
            else:
                color = 'ok'

            msg = '{0}    : ok={1}\tchanged={2}\tfailed={3}\tunreachable={4}\trescued={5}\tignored={6}'.format(
                host, s['ok'], s['changed'], s['failures'], s['unreachable'], s['rescued'], s['ignored'])
            print(colorize(msg, color))

    def v2_runner_on_skipped(self, result, **kwargs):
        """Run when a task is skipped."""
        if self._display.verbosity > 1:
            self._print_task()
            self.last_skipped = False

            line_length = 120
            spaces = ' ' * (31 - len(result._host.name) - 4)

            line = "  * {0}{1}- {2}".format(colorize(result._host.name, 'not_so_bold'),
                                            spaces,
                                            colorize("skipped", 'skipped'),)

            reason = result._result.get('skipped_reason', '') or \
                result._result.get('skip_reason', '')
            if len(reason) < 50:
                line += ' -- {0}'.format(reason)
                print("{0} {1}---------".format(line, '-' * (line_length - len(line))))
            else:
                print("{0} {1}".format(line, '-' * (line_length - len(line))))
                print(self._indent_text(reason, 8))
                print(reason)

    def v2_runner_on_ok(self, result, **kwargs):
        self._print_task_result(result, error=False, **kwargs)

    def v2_runner_on_failed(self, result, **kwargs):
        self._print_task_result(result, error=True, **kwargs)

    def v2_runner_on_unreachable(self, result, **kwargs):
        self._print_task_result(result, error=True, **kwargs)

    v2_playbook_on_handler_task_start = v2_playbook_on_task_start
