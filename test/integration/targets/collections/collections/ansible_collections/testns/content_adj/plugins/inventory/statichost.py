# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    inventory: statichost
    short_description: Add a single host
    description: Add a single host
    extends_documentation_fragment:
      - inventory_cache
    options:
      plugin:
        description: plugin name (must be statichost)
        required: true
      hostname:
        description: Toggle display of stderr even when script was successful
        required: True
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'testns.content_adj.statichost'

    def __init__(self):

        super(InventoryModule, self).__init__()

        self._hosts = set()

    def verify_file(self, path):
        ''' Verify if file is usable by this plugin, base does minimal accessibility check '''

        if not path.endswith('.statichost.yml') and not path.endswith('.statichost.yaml'):
            return False
        return super(InventoryModule, self).verify_file(path)

    def parse(self, inventory, loader, path, cache=None):

        super(InventoryModule, self).parse(inventory, loader, path)

        # Initialize and validate options
        self._read_config_data(path)

        # Exercise cache
        cache_key = self.get_cache_key(path)
        attempt_to_read_cache = self.get_option('cache') and cache
        cache_needs_update = self.get_option('cache') and not cache
        if attempt_to_read_cache:
            try:
                host_to_add = self._cache[cache_key]
            except KeyError:
                cache_needs_update = True
        if not attempt_to_read_cache or cache_needs_update:
            host_to_add = self.get_option('hostname')

        # this is where the magic happens
        self.inventory.add_host(host_to_add, 'all')
        self._cache[cache_key] = host_to_add

        # self.inventory.add_group()...
        # self.inventory.add_child()...
        # self.inventory.set_variable()..
