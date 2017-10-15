# (c) 2017 whitequark <whitequark@whitequark.org>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: full_skip
    type: stdout
    short_description: suppresses tasks if all hosts skipped
    description:
      - Use this plugin when you don't want to see any output for tasks that did not
        actually run any commands.
    version_added: "2.4"
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout in configuation
'''

from ansible.plugins.callback.default import CallbackModule as CallbackModule_default


def _filter(level, meth):
    fn = getattr(CallbackModule_default, meth)

    def wrapped(self, *args, **kwargs):
        if self._display.verbosity >= level:
            self.flush()
            fn(self, *args, **kwargs)

    return wrapped


def _flush(meth):
    return _filter(0, meth)


def _quash(meth):
    return _filter(1, meth)


def _annul(meth):
    fn = getattr(CallbackModule_default, meth)

    def wrapped(self, *args, **kwargs):
        self._task = None
        fn(self, *args, **kwargs)

    return wrapped


class CallbackModule(CallbackModule_default):

    '''
    This is a callback interface that is identical to the default interface
    except that it does not print any messages about skipped tasks.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'full_skip'

    def __init__(self):
        self._task = None
        super(CallbackModule, self).__init__()

    def flush(self):
        if self._task is not None:
            self._print_task_banner(self._task)
        self._task = None

    def v2_playbook_on_task_start(self, task, is_conditional):
        if self._play.strategy != 'free':
            self._task = task

    v2_playbook_on_include = _flush('v2_playbook_on_include')
    v2_playbook_on_stats = _annul('v2_playbook_on_stats')

    v2_runner_on_ok = _flush('v2_runner_on_ok')
    v2_runner_on_failed = _flush('v2_runner_on_failed')
    v2_runner_on_unreachable = _flush('v2_runner_on_unreachable')
    v2_runner_on_skipped = _quash('v2_runner_on_skipped')

    v2_runner_item_on_ok = _flush('v2_runner_item_on_ok')
    v2_runner_item_on_failed = _flush('v2_runner_item_on_failed')
    v2_runner_item_on_skipped = _quash('v2_runner_item_on_skipped')

    v2_playbook_on_cleanup_task_start = _annul('v2_playbook_on_cleanup_task_start')
    v2_playbook_on_handler_task_start = _annul('v2_playbook_on_handler_task_start')

    v2_playbook_on_no_hosts_matched = _flush('v2_playbook_on_no_hosts_matched')
    v2_playbook_on_no_hosts_remaining = _annul('v2_playbook_on_no_hosts_remaining')
