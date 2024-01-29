# Copyright (c) 2022 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = '''
    name: vaulted_stuff
    options:
      secret:
        description: to test vault stuff
      eval_template:
        description: to test templated stuff
    extends_documentation_fragment:
      - constructed
'''

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable


class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = 'vaulted_stuff'

    def verify_file(self, path):
        return super(InventoryModule, self).verify_file(path) and path.endswith(('secrets.yml', 'secrets.yaml'))

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        # ensure we have extra vars
        self.templar.available_variables = self._vars

        # load and create all options
        config = self._read_config_data(path)

        # test vault
        secret = self.get_option('secret')
        if secret != 'ssssssh\n':
            raise AnsibleParserError("Didn't unvalt the secret")

        # test template
        tmp = self.get_option('eval_template')
        if tmp != 'yolo':
            raise AnsibleParserError("Didn't template the eval_template")
