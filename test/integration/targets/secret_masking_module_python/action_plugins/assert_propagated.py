# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import mask_secrets
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Confirm that secrets registered by a module propagated to the controller.

    A module registers a runtime secret inside its own process; that value must be sent back to
    the controller (via ``_ansible_new_secrets``) so the controller masks it as well. This action
    masks the supplied values on the controller and fails if any of them survives unredacted.
    """

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        for secret in self._task.args['secrets']:
            if mask_secrets(f"pre {secret} post") != 'pre $REDACTED$ post':
                raise Exception("a secret registered by the module did not propagate to the controller")

        result['changed'] = False
        return result
