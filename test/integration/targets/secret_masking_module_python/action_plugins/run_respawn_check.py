# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import mask_secrets
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Run a module that respawns itself and confirm outgoing secrets reach the controller.

    A module registers a runtime secret from inside its respawned child process. The respawned
    child owns the result JSON, so its ``_ansible_new_secrets`` must still flow back so the
    controller registers the value once the module is done.
    """

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        register_as_secret = self._task.args['register_as_secret']

        if mask_secrets(f"pre {register_as_secret} post") != f'pre {register_as_secret} post':
            raise Exception("the outgoing secret was already registered on the controller before the respawn module ran")

        module_result = self._execute_module(
            module_name='respawn_secret',
            module_args={
                'incoming': self._task.args['incoming'],
                'register_as_secret': register_as_secret,
            },
            task_vars=task_vars,
        )

        # a secret registered inside the RESPAWNED child must have propagated to the controller
        if mask_secrets(f"pre {register_as_secret} post") != 'pre $REDACTED$ post':
            raise Exception("a secret registered in the respawned module did not propagate to the controller")

        result.update(module_result)
        return result
