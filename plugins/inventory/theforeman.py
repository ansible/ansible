#!/usr/bin/env python
# Copyright 2014 Franck Cuny <franckcuny@gmail.com>
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

'''
Foreman external inventory script
=================================

Generates inventory that Ansible can understand by making API requests
to Foreman.

Information about the Foreman's instance can be stored in the ``foreman.ini`` file.
A ``base_url``, ``username`` and ``password`` need to be provided. The path to an
alternate configuration file can be provided by exporting the ``FOREMAN_INI_PATH``
variable.

When run against a specific host, this script returns the following variables
based on the data obtained from Foreman:
 - id
 - ip
 - name
 - environment
 - os
 - model
 - compute_resource
 - domain
 - architecture
 - created
 - updated
 - status
 - ansible_ssh_host

When run in --list mode, instances are grouped by the following categories:
 - group

Examples:
  Execute uname on all instances in the dev group
  $ ansible -i theforeman.py dev -m shell -a \"/bin/uname -a\"

Author: Franck Cuny <franckcuny@gmail.com>
Version: 0.0.1
'''

import sys
import os
import re
import argparse
import ConfigParser
import collections

try:
    import json
except ImportError:
    import simplejson as json

try:
    from foreman.client import Foreman
    from requests.exceptions import ConnectionError
except ImportError, e:
    print ('python-foreman required for this module')
    print e
    sys.exit(1)


class ForemanInventory(object):
    """Foreman Inventory"""

    def _empty_inventory(self):
        """Empty inventory"""
        return {'_meta': {'hostvars': {}}}

    def _empty_cache(self):
        """Empty cache"""
        keys = ['operatingsystem', 'hostgroup', 'environment', 'model', 'compute_resource', 'domain', 'subnet', 'architecture', 'host']
        return {k:{} for k in keys}

    def __init__(self):
        """Main execution path"""

        self.inventory = self._empty_inventory()
        self._cache = self._empty_cache()

        self.base_url = None
        self.username = None
        self.password = None

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        if self.base_url is None or self.username is None or self.password is None:
            print '''Could not find values for Foreman base_url, username or password.
They must be specified via ini file.'''
            sys.exit(1)

        try:
            self.client = Foreman(self.base_url, (self.username, self.password))
        except ConnectionError, e:
            print '''It looks like Foreman's API is unreachable.'''
            print e
            sys.exit(1)

        if self.args.host:
            data_to_print = self.get_host_info(self.args.host)
        elif self.args.list:
            data_to_print = self.get_inventory()
        else:
            data_to_print = {}

        print(json.dumps(data_to_print, sort_keys=True, indent=4))

    def get_host_info(self, host_id):
        """Get information about an host"""
        host_desc = {}

        meta = self._get_object_from_id('host', host_id)
        if meta is None:
            return host_desc

        host_desc = {
            'id': meta.get('id'),
            'ip': meta.get('ip'),
            'name': meta.get('name'),
            'environment': meta.get('environment').get('environment').get('name').lower(),
            'os': self._get_os_from_id(meta.get('operatingsystem_id')),
            'model': self._get_model_from_id(meta.get('model_id')),
            'compute_resource': self._get_compute_resource_from_id(meta.get('compute_resource_id')),
            'domain': self._get_domain_from_id(meta.get('domain_id')),
            'subnet': self._get_subnet_from_id(meta.get('subnet_id')),
            'architecture': self._get_architecture_from_id(meta.get('architecture_id')),
            'created': meta.get('created_at'),
            'updated': meta.get('updated_at'),
            'status': meta.get('status'),
            # to ssh from ansible
            'ansible_ssh_host': meta.get('ip'),
        }

        return host_desc

    def get_inventory(self):
        """Get all the host from the inventory"""
        groups = collections.defaultdict(list)
        hosts  = []

        page = 1
        while True:
            resp = self.client.index_hosts(page=page)
            if len(resp) < 1:
                break
            page  += 1
            hosts += resp

        if len(hosts) < 1:
            return groups

        for host in hosts:
            host_group = self._get_hostgroup_from_id(host.get('host').get('hostgroup_id'))
            server_name = host.get('host').get('name')
            groups[host_group].append(server_name)

        return groups

    def read_settings(self):
        """Read the settings from the foreman.ini file"""
        config = ConfigParser.SafeConfigParser()
        foreman_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'foreman.ini')
        foreman_ini_path = os.environ.get('FOREMAN_INI_PATH', foreman_default_ini_path)
        config.read(foreman_ini_path)
        self.base_url = config.get('foreman', 'base_url')
        self.username = config.get('foreman', 'username')
        self.password = config.get('foreman', 'password')

    def parse_cli_args(self):
        """Command line argument processing"""
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Foreman')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def _get_os_from_id(self, os_id):
        """Get operating system name"""
        os_obj = self._get_object_from_id('operatingsystem', os_id)
        if os_obj is None:
            return os_obj

        os_name = "{0}-{1}".format(os_obj.get('name'), os_obj.get('major'))
        return os_name

    def _get_hostgroup_from_id(self, host_id):
        """Get hostgroup name"""
        group = self._get_object_from_id('hostgroup', host_id)
        if group is None:
            return group

        group_name = (re.sub("[^A-Za-z0-9\-]", "-", group.get('name')).lower())
        return group_name

    def _get_environment_from_id(self, env_id):
        """Get environment name"""
        environment = self._get_object_from_id('environment', env_id)
        if environment is None:
            return environment

        return environment.get('name').lower()

    def _get_model_from_id(self, model_id):
        """Get model from an ID"""
        model = self._get_object_from_id('model', model_id)
        if model is None:
            return model

        return model.get('name')

    def _get_compute_resource_from_id(self, resource_id):
        """Get compute resource from id"""
        compute_resource =  self._get_object_from_id('compute_resource', resource_id)
        if compute_resource is None:
            return compute_resource

        return compute_resource.get('name')

    def _get_domain_from_id(self, domain_id):
        """Get domain from id"""
        domain = self._get_object_from_id('domain', domain_id)
        if domain is None:
            return domain
        return domain.get('name')

    def _get_subnet_from_id(self, subnet_id):
        """Get subnet from id"""
        subnet = self._get_object_from_id('subnet', subnet_id)
        if subnet is None:
            return subnet

        return subnet.get('name')

    def _get_architecture_from_id(self, arch_id):
        """Get architecture from id"""
        arch = self._get_object_from_id('architecture', arch_id)
        if arch is None:
            return None

        return arch.get('name')

    def _get_object_from_id(self, obj_type, obj_id):
        """Get an object from it's ID"""
        if obj_id is None:
            return None

        obj = self._cache.get(obj_type).get(obj_id, None)

        if obj is None:
            method_name = "show_{0}s".format(obj_type)
            func = getattr(self.client, method_name)
            obj = func(obj_id)
            self._cache[obj_type][obj_id] = obj

        return obj.get(obj_type)


ForemanInventory()
