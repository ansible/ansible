# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    inventory: cache_host
    short_description: add a host to inventory and cache it
    description: add a host to inventory and cache it
    extends_documentation_fragment:
      - inventory_cache
    options:
      plugin:
        required: true
        description: name of the plugin (cache_host)
'''

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable
import random


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'cache_host'

    def verify_file(self, path):
        if not path.endswith(('cache_host.yml', 'cache_host.yaml',)):
            return False
        return super(InventoryModule, self).verify_file(path)

    def parse(self, inventory, loader, path, cache=None):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)

        cache_key = self.get_cache_key(path)
        # user has enabled cache and the cache is not being flushed
        read_cache = self.get_option('cache') and cache
        # user has enabled cache and the cache is being flushed
        update_cache = self.get_option('cache') and not cache

        host = None
        if read_cache:
            try:
                host = self._cache[cache_key]
            except KeyError:
                # cache expired
                update_cache = True

        if host is None:
            host = 'testhost{0}'.format(random.randint(0, 50))

        self.inventory.add_host(host, 'all')

        if update_cache:
            self._cache[cache_key] = host
