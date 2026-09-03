# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.utils.display import Display

display = Display()


def filter_test(value):
    secrets = ['FilterSecret1', 'FilterSecret2', 'FilterSecret3']

    register_secret(secrets[0])
    display.display(f"SCN filter_register: {secrets[0]}")

    register_secrets(secrets)
    display.display(f"SCN filter_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

    if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
        raise Exception("mask_secrets did not redact all the registered secrets")

    return value


class FilterModule:
    def filters(self):
        return {'filter_test': filter_test}
