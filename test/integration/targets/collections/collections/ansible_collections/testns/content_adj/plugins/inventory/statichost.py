# Copyright (c) 2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: statichost
    short_description: Add a single host
    options:
      plugin:
        description: plugin name (must be statichost)
        required: true
      hostname:
        description: Toggle display of stderr even when script was successful
        type: list
'''

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable


class InventoryModule(BaseInventoryPlugin):

    NAME = 'statichost'

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

        config_data = loader.load_from_file(path, cache=False)
        host_to_add = config_data.get('hostname')

        if not host_to_add:
            raise AnsibleParserError("hostname was not specified")

        # this is where the magic happens
        self.inventory.add_host(host_to_add, 'all')

        # self.inventory.add_group()...
        # self.inventory.add_child()...
        # self.inventory.set_variable()..
