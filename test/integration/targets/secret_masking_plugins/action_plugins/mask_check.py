# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import mask_secrets, register_secret
from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()


class ActionModule(ActionBase):
    """Verify that secrets registered by a previous task persisted on the controller.

    A post-fork plugin registers a secret inside its own worker; that value must be propagated
    back to the controller so a subsequent task (running in a brand new worker forked from the
    controller) also masks it. This action masks the supplied values and fails if any of them
    survives unredacted.
    """

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        label = self._task.args['label']
        secrets = self._task.args['secrets']

        for secret in secrets:
            if mask_secrets(f"pre {secret} post") != 'pre $REDACTED$ post':
                raise Exception("a secret registered in a previous task did not persist on the controller")

        # registration is append-only: adding a new secret here must not clear the persisted ones
        new_secret = f"MaskCheck{label.capitalize()}Secret"
        register_secret(new_secret)

        if mask_secrets(f"pre {new_secret} post") != 'pre $REDACTED$ post':
            raise Exception("a newly registered secret was not masked")

        for secret in secrets:
            if mask_secrets(f"pre {secret} post") != 'pre $REDACTED$ post':
                raise Exception("registering a new secret cleared a previously persisted secret")

        display.display(f"MARKER {label}_persist: ok")

        result['changed'] = False
        return result
