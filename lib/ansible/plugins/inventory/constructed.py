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
        - Uses a YAML configuration file with a valid YAML or C(.config) extension to define var expressions and group conditionals
        - The Jinja2 conditionals that qualify a host for membership.
        - The JInja2 exprpessions are calculated and assigned to the variables
        - Only variables already available from previous inventories or the fact cache can be used for templating.
        - When I(strict) is False, failed expressions will be ignored (assumes vars were missing).
    options:
        plugin:
            description: token that ensures this is a source file for the 'constructed' plugin.
            required: True
            choices: ['constructed']
    extends_documentation_fragment:
      - constructed
'''

EXAMPLES = r'''
    # inventory.config file in YAML format
    plugin: constructed
    strict: False
    compose:
        var_sum: var1 + var2

        # this variable will only be set if I have a persistent fact cache enabled (and have non expired facts)
        # `strict: False` will skip this instead of producing an error if it is missing facts.
        server_type: "ansible_hostname | regex_replace ('(.{6})(.{2}).*', '\\2')"
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
        # this creates a group per distro (distro_CentOS, distro_Debian) and assigns the hosts that have matching values to it,
        # using the default separator "_"
        - prefix: distro
          key: ansible_distribution

        # this creates a group per ec2 architecture and assign hosts to the matching ones (arch_x86_64, arch_sparc, etc)
        - prefix: arch
          key: ec2_architecture
'''

import os

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.inventory.helpers import get_group_vars
from ansible.plugins.cache import FactCache
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.module_utils._text import to_native
from ansible.utils.vars import combine_vars


class InventoryModule(BaseInventoryPlugin, Constructable):
    """ constructs groups and vars using Jinaj2 template expressions """

    NAME = 'constructed'

    def __init__(self):

        super(InventoryModule, self).__init__()

        self._cache = FactCache()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)

            if not ext or ext in ['.config'] + C.YAML_FILENAME_EXTENSIONS:
                valid = True

        return valid

    def parse(self, inventory, loader, path, cache=False):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        self._read_config_data(path)

        strict = self.get_option('strict')
        fact_cache = FactCache()
        try:
            # Go over hosts (less var copies)
            for host in inventory.hosts:

                # get available variables to templar
                hostvars = combine_vars(get_group_vars(inventory.hosts[host].get_groups()), inventory.hosts[host].get_vars())
                if host in fact_cache:  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, fact_cache[host])

                # create composite vars
                self._set_composite_vars(self.get_option('compose'), hostvars, host, strict=strict)

                # refetch host vars in case new ones have been created above
                hostvars = combine_vars(get_group_vars(inventory.hosts[host].get_groups()), inventory.hosts[host].get_vars())
                if host in self._cache:  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, self._cache[host])

                # constructed groups based on conditionals
                self._add_host_to_composed_groups(self.get_option('groups'), hostvars, host, strict=strict)

                # constructed groups based variable values
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), hostvars, host, strict=strict)

        except Exception as e:
            raise AnsibleParserError("failed to parse %s: %s " % (to_native(path), to_native(e)))
