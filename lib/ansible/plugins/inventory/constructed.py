# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    name: constructed
    version_added: "2.4"
    short_description: Uses Jinja2 to construct vars and groups based on existing inventory.
    description:
        - Uses a YAML configuration file with a valid YAML or C(.config) extension to define var expressions and group conditionals
        - The Jinja2 conditionals that qualify a host for membership.
        - The Jinja2 expressions are calculated and assigned to the variables
        - Only variables already available from previous inventories or the fact cache can be used for templating.
        - When O(strict) is False, failed expressions will be ignored (assumes vars were missing).
    options:
        plugin:
            description: token that ensures this is a source file for the 'constructed' plugin.
            required: True
            choices: ['ansible.builtin.constructed', 'constructed']
        use_vars_plugins:
            description:
                - Normally, for performance reasons, vars plugins get executed after the inventory sources complete the base inventory,
                  this option allows for getting vars related to hosts/groups from those plugins.
                - The host_group_vars (enabled by default) 'vars plugin' is the one responsible for reading host_vars/ and group_vars/ directories.
                - This will execute all vars plugins, even those that are not supposed to execute at the 'inventory' stage.
                  See vars plugins docs for details on 'stage'.
                - Implicit groups, such as 'all' or 'ungrouped', need to be explicitly defined in any previous inventory to apply the
                  corresponding group_vars
            required: false
            default: false
            type: boolean
            version_added: '2.11'
    extends_documentation_fragment:
      - constructed
"""

EXAMPLES = r"""
    # inventory.config file in YAML format
    plugin: ansible.builtin.constructed
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
        multi_group: (group_names | intersect(['alpha', 'beta', 'omega'])) | length >= 2

    keyed_groups:
        # this creates a group per distro (distro_CentOS, distro_Debian) and assigns the hosts that have matching values to it,
        # using the default separator "_"
        - prefix: distro
          key: ansible_distribution

        # the following examples assume the first inventory is from the `aws_ec2` plugin
        # this creates a group per ec2 architecture and assign hosts to the matching ones (arch_x86_64, arch_sparc, etc)
        - prefix: arch
          key: architecture

        # this creates a group per ec2 region like "us_west_1"
        - prefix: ""
          separator: ""
          key: placement.region

        # this creates a common parent group for all ec2 availability zones
        - key: placement.availability_zone
          parent_group: all_ec2_zones
"""

import os

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.inventory.helpers import get_group_vars
from ansible.plugins.inventory import BaseInventoryPlugin, Constructable
from ansible.plugins.loader import cache_loader
from ansible.utils.vars import combine_vars
from ansible.vars.plugins import get_vars_from_inventory_sources


class InventoryModule(BaseInventoryPlugin, Constructable):
    """ constructs groups and vars using Jinja2 template expressions """

    NAME = 'constructed'

    # implicit trust behavior is already added by the YAML parser invoked by the loader

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)

            if not ext or ext in ['.config'] + C.YAML_FILENAME_EXTENSIONS:
                valid = True

        return valid

    def get_all_host_vars(self, host, loader, sources):
        """ requires host object """
        return combine_vars(self.host_groupvars(host, loader, sources), self.host_vars(host, loader, sources))

    def host_groupvars(self, host, loader, sources):
        """ requires host object """
        gvars = get_group_vars(host.get_groups())

        if self.get_option('use_vars_plugins'):
            gvars = combine_vars(gvars, get_vars_from_inventory_sources(loader, sources, host.get_groups(), 'all'))

        return gvars

    def host_vars(self, host, loader, sources):
        """ requires host object """
        hvars = host.get_vars()

        if self.get_option('use_vars_plugins'):
            hvars = combine_vars(hvars, get_vars_from_inventory_sources(loader, sources, [host], 'all'))

        return hvars

    def parse(self, inventory, loader, path, cache=False):
        """ parses the inventory file """

        super(InventoryModule, self).parse(inventory, loader, path, cache=cache)

        self._read_config_data(path)

        sources = []
        try:
            sources = inventory.processed_sources
        except AttributeError:
            if self.get_option('use_vars_plugins'):
                raise

        strict = self.get_option('strict')

        cache = cache_loader.get(C.CACHE_PLUGIN)

        try:
            # Go over hosts (less var copies)
            for host in inventory.hosts:

                # get available variables to templar
                hostvars = self.get_all_host_vars(inventory.hosts[host], loader, sources)
                if cache.contains(host):  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, cache.get(host))

                # create composite vars
                self._set_composite_vars(self.get_option('compose'), hostvars, host, strict=strict)

                # refetch host vars in case new ones have been created above
                hostvars = self.get_all_host_vars(inventory.hosts[host], loader, sources)
                if cache.contains(host):  # adds facts if cache is active
                    hostvars = combine_vars(hostvars, cache.get(host))

                # constructed groups based on conditionals
                self._add_host_to_composed_groups(self.get_option('groups'), hostvars, host, strict=strict, fetch_hostvars=False)

                # constructed groups based variable values
                self._add_host_to_keyed_groups(self.get_option('keyed_groups'), hostvars, host, strict=strict, fetch_hostvars=False)

        except Exception as ex:
            raise AnsibleParserError(f"Failed to parse {path!r}.") from ex
