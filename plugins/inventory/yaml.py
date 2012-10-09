#!/usr/bin/env python
# Support a YAML file hosts.yml as external inventory in Ansible

# Copyright (C) 2012  Jeroen Hoekx <jeroen@hoekx.be>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
File format:

- <hostname>

or

- host: <hostname>
  vars:
  - myvar: value
  - myvbr: vblue
  groups:
  - mygroup1
  - mygroup2

or

- group: <groupname>
  vars:
  - groupvar: value
  hosts:
  - myhost1
  - myhost2
  groups:
  - subgroup1
  - subgroup2

Any statement except the first definition is optional.
"""

import json
import os
import sys

from optparse import OptionParser

import yaml

class Host():
    def __init__(self, name):
        self.name = name
        self.groups = []
        self.vars = {}
    def __repr__(self):
        return "Host('%s')"%(self.name)

    def set_variable(self, key, value):
        self.vars[key] = value

    def get_variables(self):
        result = {}
        for group in self.groups:
            for k,v in group.get_variables().items():
                result[k] = v
        for k, v in self.vars.items():
            result[k] = v
        return result

    def add_group(self, group):
        if group not in self.groups:
            self.groups.append(group)

class Group():
    def __init__(self, name):
        self.name = name
        self.hosts = []
        self.vars = {}
        self.subgroups = []
        self.parents = []
    def __repr__(self):
        return "Group('%s')"%(self.name)

    def get_hosts(self):
        """ List all hosts in this group, including subgroups """
        result = [ host for host in self.hosts ]
        for group in self.subgroups:
            for host in group.get_hosts():
                if host not in result:
                    result.append(host)
        return result

    def add_host(self, host):
        if host not in self.hosts:
            self.hosts.append(host)
            host.add_group(self)

    def add_subgroup(self, group):
        if group not in self.subgroups:
            self.subgroups.append(group)
            group.add_parent(self)

    def add_parent(self, group):
        if group not in self.parents:
            self.parents.append(group)

    def set_variable(self, key, value):
        self.vars[key] = value

    def get_variables(self):
        result = {}
        for group in self.parents:
            result.update( group.get_variables() )
        result.update(self.vars)
        return result

def find_group(name, groups):
    for group in groups:
        if name == group.name:
            return group

def parse_vars(vars, obj):
    ### vars can be a list of dicts or a dictionary
    if type(vars) == dict:
        for k,v in vars.items():
            obj.set_variable(k, v)
    elif type(vars) == list:
        for var in vars:
            k,v = var.items()[0]
            obj.set_variable(k, v)

def parse_yaml(yaml_hosts):
    groups = []

    all_hosts = Group('all')

    ungrouped = Group('ungrouped')
    groups.append(ungrouped)

    ### groups first, so hosts can be added to 'ungrouped' if necessary
    subgroups = []
    for entry in yaml_hosts:
        if 'group' in entry and type(entry)==dict:
            group = find_group(entry['group'], groups)
            if not group:
                group = Group(entry['group'])
                groups.append(group)

            if 'vars' in entry:
                parse_vars(entry['vars'], group)

            if 'hosts' in entry:
                for host_name in entry['hosts']:
                    host = None
                    for test_host in all_hosts.get_hosts():
                        if test_host.name == host_name:
                            host = test_host
                            break
                    else:
                        host = Host(host_name)
                        all_hosts.add_host(host)
                    group.add_host(host)

            if 'groups' in entry:
                for subgroup in entry['groups']:
                    subgroups.append((group.name, subgroup))

    for name, sub_name in subgroups:
        group = find_group(name, groups)
        subgroup = find_group(sub_name, groups)
        group.add_subgroup(subgroup)

    for entry in yaml_hosts:
        ### a host is either a dict or a single line definition
        if type(entry) in [str, unicode]:
            for test_host in all_hosts.get_hosts():
                if test_host.name == entry:
                    break
            else:
                host = Host(entry)
                all_hosts.add_host(host)
                ungrouped.add_host(host)

        elif 'host' in entry:
            host = None
            no_group = False
            for test_host in all_hosts.get_hosts():
                ### all hosts contains only hosts already in groups
                if test_host.name == entry['host']:
                    host = test_host
                    break
            else:
                host = Host(entry['host'])
                all_hosts.add_host(host)
                no_group = True

            if 'vars' in entry:
                parse_vars(entry['vars'], host)

            if 'groups' in entry:
                for test_group in groups:
                    if test_group.name in entry['groups']:
                        test_group.add_host(host)
                        all_hosts.add_host(host)
                        no_group = False

            if no_group:
                ungrouped.add_host(host)

    return groups, all_hosts

parser = OptionParser()
parser.add_option('-l', '--list', default=False, dest="list_hosts", action="store_true")
parser.add_option('-H', '--host', default=None, dest="host")
parser.add_option('-e', '--extra-vars', default=None, dest="extra")
options, args = parser.parse_args()

base_dir = os.path.dirname(os.path.realpath(__file__))
hosts_file = os.path.join(base_dir, 'hosts.yml')

with open(hosts_file) as f:
    yaml_hosts = yaml.load( f.read() )

groups, all_hosts = parse_yaml(yaml_hosts)

if options.list_hosts == True:
    result = {}
    for group in groups:
        result[group.name] = [host.name for host in group.get_hosts()]
    print json.dumps(result)
    sys.exit(0)

if options.host is not None:
    result = {}
    host = None
    for test_host in all_hosts.get_hosts():
        if test_host.name == options.host:
            host = test_host
            break
    result = host.get_variables()
    if options.extra:
        k,v = options.extra.split("=")
        result[k] = v
    print json.dumps(result)
    sys.exit(0)

parser.print_help()
sys.exit(1)
