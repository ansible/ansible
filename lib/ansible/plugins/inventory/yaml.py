# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    inventory: yaml
    version_added: "2.4"
    short_description: Uses a specifically YAML file as inventory source.
    description:
        - "YAML based inventory, starts with the 'all' group and has hosts/vars/children entries."
        - Host entries can have sub-entries defined, which will be treated as variables.
        - Vars entries are normal group vars.
        - "Children are 'child groups', which can also have their own vars/hosts/children and so on."
        - File MUST have a valid extension, defined in configuration
    notes:
        - It takes the place of the previously hardcoded YAML inventory.
        - To function it requires being whitelisted in configuration.
    options:
        yaml_extensions:
            description: list of 'valid' extensions for files containing YAML
            type: list
            default: ['.yaml', '.yml', '.json']
'''
EXAMPLES = '''
all: # keys must be unique, i.e. only one 'hosts' per group
    hosts:
        test1:
        test2:
            var1: value1
    vars:
        group_var1: value2
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
                last_var: MYVALUE
'''

import re
import os
from collections import MutableMapping

from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.parsing.utils.addresses import parse_address
from ansible.plugins.inventory import BaseFileInventoryPlugin, detect_range, expand_hostname_range


class InventoryModule(BaseFileInventoryPlugin):

    NAME = 'yaml'

    def __init__(self):

        super(InventoryModule, self).__init__()

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            file_name, ext = os.path.splitext(path)
            if not ext or ext in C.YAML_FILENAME_EXTENSIONS:
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        ''' parses the inventory file '''

        super(InventoryModule, self).parse(inventory, loader, path)

        try:
            data = self.loader.load_from_file(path)
        except Exception as e:
            raise AnsibleParserError(e)

        if not data:
            return False

        # We expect top level keys to correspond to groups, iterate over them
        # to get host, vars and subgroups (which we iterate over recursivelly)
        if isinstance(data, MutableMapping):
            for group_name in data:
                self._parse_group(group_name, data[group_name])
        else:
            raise AnsibleParserError("Invalid data from file, expected dictionary and got:\n\n%s" % to_native(data))

    def _parse_group(self, group, group_data):

        self.inventory.add_group(group)

        if isinstance(group_data, MutableMapping):
            # make sure they are dicts
            for section in ['vars', 'children', 'hosts']:
                if section in group_data and isinstance(group_data[section], string_types):
                    group_data[section] = {group_data[section]: None}

            if group_data.get('vars', False):
                for var in group_data['vars']:
                    self.inventory.set_variable(group, var, group_data['vars'][var])

            if group_data.get('children', False):
                for subgroup in group_data['children']:
                    self._parse_group(subgroup, group_data['children'][subgroup])
                    self.inventory.add_child(group, subgroup)

            if group_data.get('hosts', False):
                for host_pattern in group_data['hosts']:
                    hosts, port = self._parse_host(host_pattern)
                    self.populate_host_vars(hosts, group_data['hosts'][host_pattern] or {}, group, port)

    def _parse_host(self, host_pattern):
        '''
        Each host key can be a pattern, try to process it and add variables as needed
        '''
        (hostnames, port) = self._expand_hostpattern(host_pattern)

        return hostnames, port

    def _expand_hostpattern(self, hostpattern):
        '''
        Takes a single host pattern and returns a list of hostnames and an
        optional port number that applies to all of them.
        '''
        # Can the given hostpattern be parsed as a host with an optional port
        # specification?

        try:
            (pattern, port) = parse_address(hostpattern, allow_ranges=True)
        except:
            # not a recognizable host pattern
            pattern = hostpattern
            port = None

        # Once we have separated the pattern, we expand it into list of one or
        # more hostnames, depending on whether it contains any [x:y] ranges.

        if detect_range(pattern):
            hostnames = expand_hostname_range(pattern)
        else:
            hostnames = [pattern]

        return (hostnames, port)
