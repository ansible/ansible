# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: constructed
    plugin_type: inventory
    version_added: "2.4"
    short_description: Uses Jinja2 to construct vars and groups based on existing inventory.
    description:
        - Uses a YAML configuration file with a valid YAML or ``.config`` extension to define var expressions and group conditionals
        - The Jinja2 conditionals that qualify a host for membership.
        - The JInja2 exprpessions are calculated and assigned to the variables
        - Only variables already available from previous inventories can be used for templating.
        - Failed expressions will be ignored (assumes vars were missing).
    extends_documentation_fragment:
      - constructed
'''

EXAMPLES = '''
    # inventory.config file in YAML format
    plugin: comstructed
    compose:
        var_sum: var1 + var2
    groups:
        # simple name matching
        webservers: inventory_hostname.startswith('web')

        # using ec2 'tags' (assumes aws inventory)
        development: "'devel' in (ec2_tags|list)"

        # using other host properties populated in inventory
        private_only: not (public_dns_name is defined or ip_address is defined)

        # complex group membership
        multi_group: (group_names|intersection(['alpha', 'beta', 'omega']))|length >= 2

    keyed_groups:
        # this creates a group per distro (distro_CentOS, distro_Debian) and assigns the hosts that have matching values to it
        - prefix: distro
          key: ansible_distribution

        # this creates a group per ec2 architecture and assign hosts to the matching ones (arch_x86_64, arch_sparc, etc)
        - prefix: arch
          key: ec2_architecture
'''

import os

from collections import MutableMapping

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.module_utils._text import to_native
from ansible.utils.vars import combine_vars


class InventoryModule(BaseInventoryPlugin):
    """ constructs groups and vars using Jinaj2 template expressions """

    NAME = 'constructed'

    def __init__(self):

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)

            if not ext or ext in ['.config'] + C.YAML_FILENAME_EXTENSIONS:
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=False):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path, cache=True)

        try:
            data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError("Unable to parse %s: %s" % (to_native(path), to_native(e)))

        if not data:
            raise AnsibleParserError("%s is empty" % (to_native(path)))
        elif not isinstance(data, MutableMapping):
            raise AnsibleParserError('inventory source has invalid structure, it should be a dictionary, got: %s' % type(data))
        elif data.get('plugin') != self.NAME:
            raise AnsibleParserError("%s is not a constructed groups config file, plugin entry must be 'constructed'" % (to_native(path)))

        strict = data.get('strict', False)
        try:
            # Go over hosts (less var copies)
            for host in inventory.hosts:

                # get available variables to templar
                hostvars = inventory.hosts[host].get_vars()
                if host in inventory.cache:  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, inventory.cache[host])

                # create composite vars
                self._set_composite_vars(data.get('compose'), hostvars, host, strict=strict)

                # constructed groups based on conditionals
                self._add_host_to_composed_groups(data.get('groups'), hostvars, host, strict=strict)

                # constructed groups based variable values
                self._add_host_to_keyed_groups(data.get('keyed_groups'), hostvars, host, strict=strict)

        except Exception as e:
            raise AnsibleParserError("failed to parse %s: %s " % (to_native(path), to_native(e)))
