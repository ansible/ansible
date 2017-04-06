# Copyright 2016 RedHat, inc
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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from ansible import constants as C
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.inventory.expand_hosts import detect_range
from ansible.inventory.expand_hosts import expand_hostname_range
from ansible.parsing.utils.addresses import parse_address
from ansible.compat.six import string_types

class InventoryParser(object):
    """
    Takes a YAML-format inventory file and builds a list of groups and subgroups
    with their associated hosts and variable settings.
    """

    def __init__(self, loader, groups, filename=C.DEFAULT_HOST_LIST):
        self._loader = loader
        self.filename = filename

        # Start with an empty host list and whatever groups we're passed in
        # (which should include the default 'all' and 'ungrouped' groups).

        self.hosts = {}
        self.patterns = {}
        self.groups = groups

        # Read in the hosts, groups, and variables defined in the
        # inventory file.
        data = loader.load_from_file(filename)

        self._parse(data)

    def _parse(self, data):
        '''
        Populates self.groups from the given array of lines. Raises an error on
        any parse failure.
        '''

        self._compile_patterns()

        # We expect top level keys to correspond to groups, iterate over them
        # to get host, vars and subgroups (which we iterate over recursivelly)
        for group_name in data.keys():
            self._parse_groups(group_name, data[group_name])

        # Finally, add all top-level groups as children of 'all'.
        # We exclude ungrouped here because it was already added as a child of
        # 'all' at the time it was created.
        for group in self.groups.values():
            if group.depth == 0 and group.name not in ('all', 'ungrouped'):
                self.groups['all'].add_child_group(group)

    def _parse_groups(self, group, group_data):

        if group not in self.groups:
            self.groups[group] = Group(name=group)

        if isinstance(group_data, dict):
            #make sure they are dicts
            for section in ['vars', 'children', 'hosts']:
                if section in group_data and isinstance(group_data[section], string_types):
                    group_data[section] = { group_data[section]: None}

            if 'vars' in group_data:
                for var in group_data['vars']:
                    if var != 'ansible_group_priority':
                        self.groups[group].set_variable(var, group_data['vars'][var])
                    else:
                        self.groups[group].set_priority(group_data['vars'][var])

            if 'children' in group_data:
                for subgroup in group_data['children']:
                    self._parse_groups(subgroup, group_data['children'][subgroup])
                    self.groups[group].add_child_group(self.groups[subgroup])

            if 'hosts' in group_data:
                for host_pattern in group_data['hosts']:
                    hosts = self._parse_host(host_pattern, group_data['hosts'][host_pattern])
                    for h in hosts:
                        self.groups[group].add_host(h)


    def _parse_host(self, host_pattern, host_data):
        '''
        Each host key can be a pattern, try to process it and add variables as needed
        '''
        (hostnames, port) = self._expand_hostpattern(host_pattern)
        hosts = self._Hosts(hostnames, port)

        if isinstance(host_data, dict):
            for k in host_data:
                for h in hosts:
                    h.set_variable(k, host_data[k])
                    if k in ['ansible_host', 'ansible_ssh_host']:
                        h.address = host_data[k]
        return hosts

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

    def _Hosts(self, hostnames, port):
        '''
        Takes a list of hostnames and a port (which may be None) and returns a
        list of Hosts (without recreating anything in self.hosts).
        '''

        hosts = []

        # Note that we decide whether or not to create a Host based solely on
        # the (non-)existence of its hostname in self.hosts. This means that one
        # cannot add both "foo:22" and "foo:23" to the inventory.

        for hn in hostnames:
            if hn not in self.hosts:
                self.hosts[hn] = Host(name=hn, port=port)
            hosts.append(self.hosts[hn])

        return hosts

    def get_host_variables(self, host):
        return {}

    def _compile_patterns(self):
        '''
        Compiles the regular expressions required to parse the inventory and stores them in self.patterns.
        '''
        self.patterns['groupname'] = re.compile( r'''^[A-Za-z_][A-Za-z0-9_]*$''')
