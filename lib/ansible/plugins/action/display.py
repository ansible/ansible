# Copyright (c) 2025, Ansible Project
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
from __future__ import annotations

from ansible.module_utils.common.text.converters import to_text
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

# Allowed display levels. Excludes 'error' per issue design.
DISPLAY_LEVELS = (
    'display',   # normal display
    'v', 'vv', 'vvv', 'vvvv', 'vvvvv', 'vvvvvv',  # verbosity levels
    'warning',
    'deprecated',
)


class ActionModule(ActionBase):
    """Emit a message via the Display subsystem at a chosen level."""

    TRANSFERS_FILES = False
    _requires_connection = False
    BYPASS_HOST_LOOP = True

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = {}

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec={
                'msg': {'type': 'str', 'required': True},
                'level': {'type': 'str', 'default': 'display', 'choices': DISPLAY_LEVELS},
            },
        )

        msg = to_text(self._templar.template(new_module_args['msg']))
        level = new_module_args['level']

        if level == 'display':
            display.display(msg)
        elif level == 'warning':
            display.warning(msg)
        elif level == 'deprecated':
            display.deprecated(msg, version='2.22')
        elif level == 'v':
            display.v(msg)
        elif level == 'vv':
            display.vv(msg)
        elif level == 'vvv':
            display.vvv(msg)
        elif level == 'vvvv':
            display.vvvv(msg)
        elif level == 'vvvvv':
            display.vvvvv(msg)
        elif level == 'vvvvvv':
            display.vvvvvv(msg)
        else:
            display.display(msg)

        result['msg'] = msg
        result['level'] = level
        # This action never changes state; always report changed: False
        result['changed'] = False
        return result
