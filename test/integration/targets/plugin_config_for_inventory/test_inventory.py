from __future__ import annotations


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
        cache:
            description: cache
            type: bool
            default: false
            required: False
        cache_plugin:
            description: cache plugin
            type: str
            default: none
            required: False
        cache_timeout:
            description: test cache parameter
            type: integer
            default: 7
            required: False
        cache_connection:
            description: cache connection
            type: str
            default: /tmp/foo
            required: False
        cache_prefix:
            description: cache prefix
            type: str
            default: prefix_
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
        config_data = self._read_config_data(path=path)
        self._consume_options(config_data)

        departments = self.get_option('departments')

        group = 'test_group'
        host = 'test_host'

        self.inventory.add_group(group)
        self.inventory.add_host(group=group, host=host)
        self.inventory.set_variable(host, 'departments', departments)

        # Ensure the timeout we're given gets sent to the cache plugin
        if self.get_option('cache'):
            given_timeout = self.get_option('cache_timeout')
            cache_timeout = self._cache._plugin.get_option('_timeout')
            self.inventory.set_variable(host, 'given_timeout', given_timeout)
            self.inventory.set_variable(host, 'cache_timeout', cache_timeout)
