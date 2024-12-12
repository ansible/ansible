from __future__ import annotations

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'testinv'

    def verify_file(self, path):
        # any file will do AND be ignored
        return True

    def parse(self, inventory, loader, path, cache=None):
        pass
