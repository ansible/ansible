from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = '''
    name: test_inventory
    plugin_type: inventory
    authors:
      - Pierre-Louis Bonicoli (@pilou-)
    short_description: test inventory
    description:
        - test inventory (fetch parameters using config API)
    options:
        departments:
            description: test parameter
            type: list
            default:
                - seine-et-marne
                - haute-garonne
            required: False
'''

EXAMPLES = '''
# Example command line: ansible-inventory --list -i test_inventory.yml

plugin: test_inventory
departments:
  - paris
'''

from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'test_inventory'

    def verify_file(self, path):
        return True

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path=path)

        departments = self.get_option('departments')

        group = 'test_group'
        host = 'test_host'

        self.inventory.add_group(group)
        self.inventory.add_host(group=group, host=host)
        self.inventory.set_variable(host, 'departments', departments)
