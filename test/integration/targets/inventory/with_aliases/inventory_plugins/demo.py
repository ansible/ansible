from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: demo
    short_description: demo
    options:
      upcase:
        description: imports hosts as all cap hostnames
        type: bool
        aliases: ["UPCASE"]
    description:
      - demo
'''


from ansible.plugins.inventory import BaseInventoryPlugin


class InventoryModule(BaseInventoryPlugin):
    NAME = 'demo'

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path)
        self._read_config_data(path)
        upcase = self.get_option('upcase')
        if upcase:
            self.inventory.add_host('TESTHOST.EXAMPLE.COM')
        else:
            self.inventory.add_host('testhost.example.com')
