# Copyright (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: test_inventory
    version_added: "2.11"
    short_description: Inventory plugin to exercise test setting and getting the cache
    description: Inventory plugin to exercise test setting and getting the cache
    options:
        plugin:
            description: token that ensures this is a source file for the test_inventory plugin.
            required: True
            choices: ['test_inventory']
    extends_documentation_fragment:
      - inventory_cache
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'test_inventory'

    def parse(self, inventory, loader, path, cache=False):
        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        self._read_config_data(path)

        inventory_cache_option = self.get_option('cache')
        cache_key = self.get_cache_key(path)

        read_cache = cache and inventory_cache_option
        refresh_cache = not cache and inventory_cache_option

        if read_cache:
            try:
                results = self._cache[cache_key]
            except KeyError:
                # cache expired
                refresh_cache = True

        if refresh_cache or not inventory_cache_option:
            results = {'testhost': {'hostvars': {'ansible_connection': 'local', 'testvar': 'value'}}}

        for hostname in results.keys():
            self.inventory.add_host(hostname, group='all')
            for variable_name, variable_value in results[hostname]['hostvars'].items():
                self.inventory.set_variable(hostname, variable_name, variable_value)

        if refresh_cache:
            self._cache[cache_key] = results
