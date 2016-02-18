# (c) 2015, Andrew Gaffney <andrew@agaffney.org>
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

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'actionable'

    def __init__(self):
        self.super_ref = super(CallbackModule, self)
        self.super_ref.__init__()
        self.last_task = None
        self.shown_title = False

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.last_task = task
        self.shown_title = False

    def display_task_banner(self):
        if not self.shown_title:
            self.super_ref.v2_playbook_on_task_start(self.last_task, None)
            self.shown_title = True

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.display_task_banner()
        self.super_ref.v2_runner_on_failed(result, ignore_errors)

    def v2_runner_on_ok(self, result):
        if result._result.get('changed', False):
            self.display_task_banner()
            self.super_ref.v2_runner_on_ok(result)
        else:
            pass

    def v2_runner_on_unreachable(self, result):
        self.display_task_banner()
        self.super_ref.v2_runner_on_unreachable(result)

    def v2_runner_on_skipped(self, result):
        pass

    def v2_playbook_on_include(self, included_file):
        pass

    def v2_playbook_item_on_ok(self, result):
        self.display_task_banner()
        self.super_ref.v2_playbook_item_on_ok(result)

    def v2_playbook_item_on_skipped(self, result):
        pass

    def v2_playbook_item_on_failed(self, result):
        self.display_task_banner()
        self.super_ref.v2_playbook_item_on_failed(result)

