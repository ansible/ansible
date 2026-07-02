# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: constructed_with_hostvars
    options:
      plugin:
        description: the load name of the plugin
      plugin_expression:
        description: an expression that must be trusted whose default resolves to 2
        default: 1 + 1
    extends_documentation_fragment:
      - constructed
      - fragment_with_expression
"""

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible._internal import _testing


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'constructed_with_hostvars'

    def verify_file(self, path):
        return super(InventoryModule, self).verify_file(path) and path.endswith(('constructed.yml', 'constructed.yaml'))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        config = self._read_config_data(path)

        with _testing.hard_fail_context("ensure config defaults are trusted and runnable as expressions") as ctx:
            ctx.check(self._compose(self.get_option('plugin_expression'), variables={}) == 2)
            ctx.check(self._compose(self.get_option('fragment_expression'), variables={}) == 4)

        strict = self.get_option('strict')
        try:
            for host in inventory.hosts:
                hostvars = {}

                # constructed groups based on conditionals
                self._add_host_to_composed_groups(self.get_option('groups'), hostvars, host, strict=strict, fetch_hostvars=True)

                # constructed groups based variable values
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), hostvars, host, strict=strict, fetch_hostvars=True)

        except Exception as ex:
            raise AnsibleParserError(f"Failed to parse {path}.") from ex
