# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import mask_secrets
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        register_as_secret = self._task.args['register_as_secret']
        no_log_option = self._task.args['no_log_option']

        if mask_secrets(f"pre {register_as_secret} post") != f'pre {register_as_secret} post':
            raise Exception("a module-registered secret was already registered on the controller before this task ran")
        if mask_secrets(f"pre {no_log_option} post") != f'pre {no_log_option} post':
            raise Exception("a no_log option value was already registered on the controller before this task ran")

        module_result = self._execute_module(
            module_name='discover_secret',
            module_args={
                'incoming': self._task.args['incoming'],
                'register_as_secret': register_as_secret,
                'no_log_option': no_log_option,
            },
            task_vars=task_vars,
        )

        if mask_secrets(f"pre {register_as_secret} post") != 'pre $REDACTED$ post':
            raise Exception("a module-registered secret was not masked during result processing")
        if mask_secrets(f"pre {no_log_option} post") != 'pre $REDACTED$ post':
            raise Exception("a no_log option value was not registered as a secret")

        result.update(module_result)
        return result
