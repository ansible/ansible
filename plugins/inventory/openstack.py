#!/usr/bin/env python

# Copyright (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
# Copyright (c) 2013, Jesse Keating <jesse.keating@rackspace.com>
# Copyright (c) 2014, Hewlett-Packard Development Company, L.P.
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

# The OpenStack Inventory module uses os-client-config for configuation.
# https://github.com/stackforge/os-client-config
# This means it will either:
#  - Respect normal OS_* environment variables like other OpenStack tools
#  - Read values from a clouds.yaml file.
# If you want to configure via clouds.yaml, you can put the file in:
#  - Current directory
#  - ~/.config/openstack/clouds.yaml
#  - /etc/openstack/clouds.yaml
#  - /etc/ansible/openstack.yml
# The clouds.yaml file can contain entries for multiple clouds and multiple
# regions of those clouds. If it does, this inventory module will connect to
# all of them and present them as one contiguous inventory.
#
# See the adjacent openstack.yml file for an example config file

import argparse
import collections
import os
import sys
import time

try:
    import json
except:
    import simplejson as json

import os_client_config
import shade


class OpenStackInventory(object):

    def __init__(self, private=False, refresh=False):
        self.openstack_config = os_client_config.config.OpenStackConfig(
            os_client_config.config.CONFIG_FILES.append(
                '/etc/ansible/openstack.yml'),
            private)
        self.clouds = shade.openstack_clouds(self.openstack_config)
        self.refresh = refresh

        self.cache_max_age = self.openstack_config.get_cache_max_age()
        cache_path = self.openstack_config.get_cache_path()

        # Cache related
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        self.cache_file = os.path.join(cache_path, "ansible-inventory.cache")

    def is_cache_stale(self):
        ''' Determines if cache file has expired, or if it is still valid '''
        if os.path.isfile(self.cache_file):
            mod_time = os.path.getmtime(self.cache_file)
            current_time = time.time()
            if (mod_time + self.cache_max_age) > current_time:
                return False
        return True

    def get_host_groups(self):
        if self.refresh or self.is_cache_stale():
            groups = self.get_host_groups_from_cloud()
            self.write_cache(groups)
        else:
            return json.load(open(self.cache_file, 'r'))
        return groups

    def write_cache(self, groups):
        with open(self.cache_file, 'w') as cache_file:
            cache_file.write(self.json_format_dict(groups))

    def get_host_groups_from_cloud(self):
        groups = collections.defaultdict(list)
        hostvars = collections.defaultdict(dict)

        for cloud in self.clouds:

            # Cycle on servers
            for server in cloud.list_servers():

                meta = cloud.get_server_meta(server)

                if 'interface_ip' not in meta['server_vars']:
                    # skip this host if it doesn't have a network address
                    continue

                server_vars = meta['server_vars']
                hostvars[server.name][
                    'ansible_ssh_host'] = server_vars['interface_ip']
                hostvars[server.name]['openstack'] = server_vars

                for group in meta['groups']:
                    groups[group].append(server.name)

        if hostvars:
            groups['_meta'] = {'hostvars': hostvars}
        return groups

    def json_format_dict(self, data):
        return json.dumps(data, sort_keys=True, indent=2)

    def list_instances(self):
        groups = self.get_host_groups()
        # Return server list
        print(self.json_format_dict(groups))

    def get_host(self, hostname):
        groups = self.get_host_groups()
        hostvars = groups['_meta']['hostvars']
        if hostname in hostvars:
            print(self.json_format_dict(hostvars[hostname]))


def parse_args():
    parser = argparse.ArgumentParser(description='OpenStack Inventory Module')
    parser.add_argument('--private',
                        action='store_true',
                        help='Use private address for ansible host')
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh cached information')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific host')
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        inventory = OpenStackInventory(args.private, args.refresh)
        if args.list:
            inventory.list_instances()
        elif args.host:
            inventory.get_host(args.host)
    except shade.OpenStackCloudException as e:
        print(e.message)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
