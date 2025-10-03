# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = """
    inventory: yaml
    version_added: "2.4"
    short_description: Uses a specific YAML file as an inventory source.
    description:
        - "YAML-based inventory, should start with the C(all) group and contain hosts/vars/children entries."
        - Host entries can have sub-entries defined, which will be treated as variables.
        - Vars entries are normal group vars.
        - "Children are 'child groups', which can also have their own vars/hosts/children and so on."
        - File MUST have a valid extension, defined in configuration.
    notes:
        - If you want to set vars for the C(all) group inside the inventory file, the C(all) group must be the first entry in the file.
        - Enabled in configuration by default.
    options:
      yaml_extensions:
        description: list of 'valid' extensions for files containing YAML
        type: list
        default: ['.yaml', '.yml', '.json']
        env:
          - name: ANSIBLE_YAML_FILENAME_EXT
          - name: ANSIBLE_INVENTORY_PLUGIN_EXTS
        ini:
          - key: yaml_valid_extensions
            section: defaults
          - section: inventory_plugin_yaml
            key: yaml_valid_extensions

"""
EXAMPLES = """
all: # keys must be unique, i.e. only one 'hosts' per group
    hosts:
        test1:
        test2:
            host_var: value
    vars:
        group_all_var: value
    children:   # key order does not matter, indentation does
        other_group:
            children:
                group_x:
                    hosts:
                        test5
            vars:
                g2_var2: value3
            hosts:
                test4:
                    ansible_host: 127.0.0.1
        last_group:
            hosts:
                test1 # same host as above, additional group membership
            vars:
                group_last_var: value
"""

import os

from collections.abc import MutableMapping

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.plugins.inventory import BaseFileInventoryPlugin

NoneType = type(None)


class InventoryModule(BaseFileInventoryPlugin):

    NAME = 'yaml'

    def __init__(self):

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)
            if not ext or ext in self.get_option('yaml_extensions'):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        """ parses the inventory file """

        super(InventoryModule, self).parse(inventory, loader, path)
        self.set_options()

        try:
            data = self.loader.load_from_file(path, cache='none')
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            raise AnsibleParserError('Parsed empty YAML file')
        elif not isinstance(data, MutableMapping):
            raise AnsibleParserError('YAML inventory has invalid structure, it should be a dictionary, got: %s' % type(data))
        elif data.get('plugin'):
            raise AnsibleParserError('Plugin configuration YAML file, not YAML inventory')

        # We expect top level keys to correspond to groups, iterate over them
        # to get host, vars and subgroups (which we iterate over recursively)
        if isinstance(data, MutableMapping):
            for group_name in data:
                self._parse_group(group_name, data[group_name])
        else:
            raise AnsibleParserError("Invalid data from file, expected dictionary and got:\n\n%s" % to_native(data))

    def _parse_group(self, group, group_data):

        if isinstance(group_data, (MutableMapping, NoneType)):

            try:
                self.inventory.add_group(group)
            except AnsibleError as e:
                raise AnsibleParserError("Unable to add group %s: %s" % (group, to_text(e)))

            if group_data is not None:
                # make sure they are dicts
                for section in ['vars', 'children', 'hosts']:
                    if section in group_data:
                        # convert strings to dicts as these are allowed
                        if isinstance(group_data[section], str):
                            group_data[section] = {group_data[section]: None}

                        if not isinstance(group_data[section], (MutableMapping, NoneType)):
                            raise AnsibleParserError('Invalid "%s" entry for "%s" group, requires a dictionary, found "%s" instead.' %
                                                     (section, group, type(group_data[section])))

                for key in group_data:

                    if not isinstance(group_data[key], (MutableMapping, NoneType)):
                        self.display.warning('Skipping key (%s) in group (%s) as it is not a mapping, it is a %s' % (key, group, type(group_data[key])))
                        continue

                    if isinstance(group_data[key], NoneType):
                        self.display.vvv('Skipping empty key (%s) in group (%s)' % (key, group))
                    elif key == 'vars':
                        for var in group_data[key]:
                            self.inventory.set_variable(group, var, group_data[key][var])
                    elif key == 'children':
                        for subgroup in group_data[key]:
                            self._parse_group(subgroup, group_data[key][subgroup])
                            self.inventory.add_child(group, subgroup)

                    elif key == 'hosts':
                        for host_pattern in group_data[key]:
                            hosts, port = self._parse_host(host_pattern)
                            self._populate_host_vars(hosts, group_data[key][host_pattern] or {}, group, port)
                    else:
                        self.display.warning('Skipping unexpected key (%s) in group (%s), only "vars", "children" and "hosts" are valid' % (key, group))

        else:
            self.display.warning("Skipping '%s' as this is not a valid group definition" % group)

    def _parse_host(self, host_pattern):
        """
        Each host key can be a pattern, try to process it and add variables as needed
        """
        (hostnames, port) = self._expand_hostpattern(host_pattern)

        return hostnames, port
