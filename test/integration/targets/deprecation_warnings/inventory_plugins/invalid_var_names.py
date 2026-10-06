from __future__ import annotations

DOCUMENTATION = '''
    name: invalid_var_names
    short_description: inventory plugin setting variables with invalid names
    description:
        - Sets host and group variables with invalid names, directly through the inventory API.
        - Used to assert the deprecation warning reported to inventory plugin authors.
    options:
        plugin:
            description: the name of this plugin
            required: true
            choices: ['invalid_var_names']
'''

EXAMPLES = '''
# Example command line: ansible-inventory --list -i invalid_var_names.yml

plugin: invalid_var_names
'''

from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):

    NAME = 'invalid_var_names'

    def verify_file(self, path):
        return super(InventoryModule, self).verify_file(path) and path.endswith('invalid_var_names.yml')

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)
        self._read_config_data(path)

        self.inventory.add_group('plugin_group')
        self.inventory.add_host('h5', group='plugin_group')

        self.inventory.set_variable('h5', 'ansible_connection', 'local')
        self.inventory.set_variable('h5', 'good_plugin_var', 'valid name')
        self.inventory.set_variable('h5', 'var-plugin-bad', 'name with a dash')

        self.inventory.set_variable('plugin_group', 'group-var-plugin-bad', 'name with a dash')
