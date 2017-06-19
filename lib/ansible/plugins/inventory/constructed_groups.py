# Copyright 2017 RedHat, inc
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#############################################
'''
DOCUMENTATION:
    name: constructed_groups
    plugin_type: inventory
    version_added: "2.4"
    short_description: Uses Jinja2 expressions to construct groups.
    description:
        - Uses a YAML configuration file to identify group and the Jinja2 expressions that qualify a host for membership.
        - Only variables already in inventory are available for expressions (no facts).
        - Failed expressions will be ignored (assumes vars were missing).
EXAMPLES:
# inventory.config file in YAML format
plugin: constructed_groups
groups:
    # simple name matching
    webservers: inventory_hostname.startswith('web')

    # using ec2 'tags' (assumes aws inventory)
    development: "'devel' in (ec2_tags|list)"

    # using other host properties populated in inventory
    private_only: not (public_dns_name is defined or ip_address is defined)

    # complex group membership
    multi_group: (group_names|intersection(['alpha', 'beta', 'omega']))|length >= 2
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os

from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.template import Templar
from ansible.module_utils._text import to_native
from ansible.utils.vars import combine_vars


class InventoryModule(BaseInventoryPlugin):
    """ constructs groups using Jinaj2 template expressions """

    NAME = 'constructed_groups'

    def __init__(self):

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)

            if not ext or ext == '.config':
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=False):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path)

        try:
            data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError("Unable to parse %s: %s" % (to_native(path), to_native(e)))

        if not data or data.get('plugin') != self.NAME:
            raise AnsibleParserError("%s is empty or not a constructed groups config file" % (to_native(path)))

        try:
            templar = Templar(loader=loader)

            # Go over hosts (less var copies)
            for host in inventory.hosts:

                # get available variables to templar
                hostvars = host.get_vars()
                if host.name in inventory.cache:  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, inventory.cache[host.name])
                templar.set_available_variables(hostvars)

                # process each 'group entry'
                for group_name, expression in data.get('groups', {}):
                    conditional = u"{%% if %s %%} True {%% else %%} False {%% endif %%}" % expression
                    result = templar.template(conditional)
                    if result and bool(result):
                        # ensure group exists
                        inventory.add_group(group_name)
                        # add host to group
                        inventory.add_child(group_name, host.name)
        except Exception as e:
            raise AnsibleParserError("failed to parse %s: %s " % (to_native(path), to_native(e)))
