# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
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
"""

from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin, Cacheable):

    NAME = 'testns.content_adj.statichost'

    def verify_file(self, path):
        pass

    def parse(self, inventory, loader, path, cache=None):

        pass
