# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: inventory_test
    short_description: register secrets and prove Display egress redacts them immediately
    description:
        - Test helper that registers secrets via the public C(ansible.module_utils.secrets) API
          and proves a subsequent C(Display) egress redacts them without any propagation delay.
    options:
      plugin:
        description: token that ensures this is a source file for the C(inventory_test) plugin.
        required: true
        choices: ['inventory_test']
"""

from ansible.module_utils.secrets import register_secret, register_secrets, mask_secrets
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.utils.display import Display

display = Display()


class InventoryModule(BaseInventoryPlugin):

    NAME = 'inventory_test'

    def verify_file(self, path):
        return super().verify_file(path) and path.endswith(('inventory_test.yml', 'inventory_test.yaml'))

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path)
        self._read_config_data(path)

        secrets = ['InventorySecret1', 'InventorySecret2', 'InventorySecret3']

        register_secret(secrets[0])
        display.display(f"MARKER inventory_register: {secrets[0]}")

        register_secrets(secrets)
        display.display(f"MARKER inventory_registers: {secrets[0]} {secrets[1]} {secrets[2]}")

        if mask_secrets(f"{secrets[0]} {secrets[1]} {secrets[2]}") != '$REDACTED$ $REDACTED$ $REDACTED$':
            raise Exception("mask_secrets did not redact all the registered secrets")

        inventory.add_host('testhost', group='all')
