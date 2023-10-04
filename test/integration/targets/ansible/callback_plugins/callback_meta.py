# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.plugins.callback import CallbackBase
import os


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'callback_meta'

    def __init__(self, *args, **kwargs):
        super(CallbackModule, self).__init__(*args, **kwargs)
        self.wants_implicit_tasks = os.environ.get('CB_WANTS_IMPLICIT', False)

    def v2_playbook_on_task_start(self, task, is_conditional):
        if task.implicit:
            self._display.display('saw implicit task')
        self._display.display(task.get_name())
