# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.plugins.action import ActionBase

import sys

# reference our own module from sys.modules while it's being loaded to ensure the importer behaves properly
try:
    mod = sys.modules[__name__]
except KeyError:
    raise Exception(f'module {__name__} is not accessible via sys.modules, likely a pluginloader bug')


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        result['changed'] = False
        result['msg'] = 'self-referential action loaded and ran successfully'
        return result
