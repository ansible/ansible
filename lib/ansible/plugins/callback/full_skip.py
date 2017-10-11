# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: full_skip
    type: stdout
    short_description: suppreses tasks if all hosts skipped
    description:
      - Use this plugin when you dont care about any output for tasks that were completly skipped
    version_added: "2.4"
    extends_documentation_fragment:
      - default_callback
    requirements:
      - set as stdout in configuation
'''

from ansible import constants as C
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default
from ansible.playbook.task_include import TaskInclude


class CallbackModule(CallbackModule_default):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'full_skip'

    def __init__(self):
        self.outlines = []
        self.itemlines = []
        super(CallbackModule, self).__init__()

    def v2_runner_on_skipped(self, result):
        self.outlines = []

    def v2_playbook_item_on_skipped(self, result):
        self.outlines = []

    def v2_runner_item_on_skipped(self, result):
        self.outlines = []

    def v2_runner_item_on_ok(self, result):
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        if isinstance(result._task, TaskInclude):
            return
        elif result._result.get('changed', False):
            msg = 'changed'
            color = C.COLOR_CHANGED
        else:
            msg = 'ok'
            color = C.COLOR_OK

        if delegated_vars:
            msg += ": [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += ": [%s]" % result._host.get_name()

        msg += " => (item=%s)" % (self._get_item(result._result),)

        msg2 = ""
        if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
            msg += " => %s" % self._dump_results(result._result)

        self.itemlines.append((msg, color))

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.display()
        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.outlines = []
        self.outlines.append("TASK [%s]" % task.get_name().strip())
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self.outlines.append("task path: %s" % path)

    def v2_playbook_item_on_ok(self, result):
        self.display()
        super(CallbackModule, self).v2_playbook_item_on_ok(result)

    def v2_runner_on_ok(self, result):
        self.display()
        super(CallbackModule, self).v2_runner_on_ok(result)

    def display(self):
        if len(self.outlines) == 0:
            return
        (first, rest) = self.outlines[0], self.outlines[1:]
        self._display.banner(first)
        for line in rest:
            self._display.display(line)
        for itemline in self.itemlines:
            self._display.display(itemline[0], color=itemline[1])
        self.outlines = []
        self.itemlines = []
