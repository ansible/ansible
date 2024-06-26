# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: constructed_with_hostvars
    options:
      plugin:
        description: the load name of the plugin
    extends_documentation_fragment:
      - constructed
'''

from ansible.errors import AnsibleParserError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'constructed_with_hostvars'

    def verify_file(self, path):
        return super(InventoryModule, self).verify_file(path) and path.endswith(('constructed.yml', 'constructed.yaml'))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        config = self._read_config_data(path)

        strict = self.get_option('strict')
        try:
            for host in inventory.hosts:
                hostvars = {}

                # constructed groups based on conditionals
                self._add_host_to_composed_groups(self.get_option('groups'), hostvars, host, strict=strict, fetch_hostvars=True)

                # constructed groups based variable values
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), hostvars, host, strict=strict, fetch_hostvars=True)

        except Exception as e:
            raise AnsibleParserError("failed to parse %s: %s " % (to_native(path), to_native(e)), orig_exc=e)
