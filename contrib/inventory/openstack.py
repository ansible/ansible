#!/usr/bin/env python

# Copyright (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
# Copyright (c) 2013, Jesse Keating <jesse.keating@rackspace.com>
# Copyright (c) 2015, Hewlett-Packard Development Company, L.P.
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

# The OpenStack Inventory module uses os-client-config for configuration.
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
import shade.inventory

CONFIG_FILES = ['/etc/ansible/openstack.yaml']


def get_groups_from_server(server_vars):
    groups = []

    region = server_vars['region']
    cloud = server_vars['cloud']
    metadata = server_vars.get('metadata', {})

    # Create a group for the cloud
    groups.append(cloud)

    # Create a group on region
    groups.append(region)

    # And one by cloud_region
    groups.append("%s_%s" % (cloud, region))

    # Check if group metadata key in servers' metadata
    if 'group' in metadata:
        groups.append(metadata['group'])

    for extra_group in metadata.get('groups', '').split(','):
        if extra_group:
            groups.append(extra_group)

    groups.append('instance-%s' % server_vars['id'])
    groups.append(server_vars['name'])

    for key in ('flavor', 'image'):
        if 'name' in server_vars[key]:
            groups.append('%s-%s' % (key, server_vars[key]['name']))

    for key, value in iter(metadata.items()):
        groups.append('meta-%s_%s' % (key, value))

    az = server_vars.get('az', None)
    if az:
        # Make groups for az, region_az and cloud_region_az
        groups.append(az)
        groups.append('%s_%s' % (region, az))
        groups.append('%s_%s_%s' % (cloud, region, az))
    return groups


def get_host_groups(inventory):
    (cache_file, cache_expiration_time) = get_cache_settings()
    if is_cache_stale(cache_file, cache_expiration_time):
        groups = to_json(get_host_groups_from_cloud(inventory))
        open(cache_file, 'w').write(groups)
    else:
        groups = open(cache_file, 'r').read()
    return groups


def get_host_groups_from_cloud(inventory):
    groups = collections.defaultdict(list)
    hostvars = {}
    for server in inventory.list_hosts():

        if 'interface_ip' not in server:
            continue
        for group in get_groups_from_server(server):
            groups[group].append(server['id'])
        hostvars[server['id']] = dict(
            ansible_ssh_host=server['interface_ip'],
            openstack=server,
        )
    groups['_meta'] = {'hostvars': hostvars}
    return groups


def is_cache_stale(cache_file, cache_expiration_time):
    ''' Determines if cache file has expired, or if it is still valid '''
    if os.path.isfile(cache_file):
        mod_time = os.path.getmtime(cache_file)
        current_time = time.time()
        if (mod_time + cache_expiration_time) > current_time:
            return False
    return True


def get_cache_settings():
    config = os_client_config.config.OpenStackConfig(
        config_files=os_client_config.config.CONFIG_FILES + CONFIG_FILES)
    # For inventory-wide caching
    cache_expiration_time = config.get_cache_expiration_time()
    cache_path = config.get_cache_path()
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    cache_file = os.path.join(cache_path, 'ansible-inventory.cache')
    return (cache_file, cache_expiration_time)


def to_json(in_dict):
    return json.dumps(in_dict, sort_keys=True, indent=2)


def parse_args():
    parser = argparse.ArgumentParser(description='OpenStack Inventory Module')
    parser.add_argument('--private',
                        action='store_true',
                        help='Use private address for ansible host')
    parser.add_argument('--refresh', action='store_true',
                        help='Refresh cached information')
    parser.add_argument('--debug', action='store_true', default=False,
                        help='Enable debug output')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific host')

    return parser.parse_args()


def main():
    args = parse_args()
    try:
        config_files = os_client_config.config.CONFIG_FILES + CONFIG_FILES
        shade.simple_logging(debug=args.debug)
        inventory = shade.inventory.OpenStackInventory(
            refresh=args.refresh,
            config_files=config_files,
            private=args.private,
        )

        if args.list:
            output = get_host_groups(inventory)
        elif args.host:
            output = to_json(inventory.get_host(args.host))
        print(output)
    except shade.OpenStackCloudException as e:
        sys.stderr.write('%s\n' % e.message)
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
