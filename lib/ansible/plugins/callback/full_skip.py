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


class CallbackModule(CallbackModule_default):

    '''
    This is the default callback interface, which simply prints messages
    to stdout when new callback events are received.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'full_skip'

    def v2_runner_on_skipped(self, result):
        self.outlines = []

    def v2_playbook_item_on_skipped(self, result):
        self.outlines = []

    def v2_runner_item_on_skipped(self, result):
        self.outlines = []

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
        self.outlines = []
