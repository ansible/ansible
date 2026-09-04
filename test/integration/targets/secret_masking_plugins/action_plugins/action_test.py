# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        secrets = ['ActionSecret1', 'ActionSecret2', 'ActionSecret3']

        register_secret(secrets[0])
        display.display(f"MARKER action_register: {secrets[0]}")

        register_secrets(secrets)
        display.display(f"MARKER action_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

        if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
            raise Exception("mask_secrets did not redact all the registered secrets")

        display.warning(f"MARKER action_warning: {secrets[1]}")
        display.deprecated(f"MARKER action_deprecated: {secrets[2]}", version='9999.9')

        result['changed'] = False
        return result
