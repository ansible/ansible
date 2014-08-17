#!/usr/bin/env python

# (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
# (c) 2013, Jesse Keating <jesse.keating@rackspace.com>
# (c) 2014, Hewlett-Packard Development Company, L.P.
#
# This file is part of Ansible,
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

import sys
import re
import os
import ConfigParser
import argparse
import collections
from novaclient.v1_1 import client as nova_client
from novaclient import exceptions
from types import NoneType

try:
    import json
except:
    import simplejson as json

from ansible.module_utils.openstack import *

NOVA_CONFIG_FILES = [
    os.getcwd() + "/nova.ini",
    os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/nova.ini")),
    "/etc/ansible/nova.ini"
]

NON_CALLABLES = (basestring, bool, dict, int, list, NoneType)


class OpenStackCloud(object):

    flavor_cache = None
    image_cache = dict()

    def __init__(self, name, username, password, project_id, auth_url,
                 region_name, service_type, insecure):

        self.name = name
        self.username = username
        self.password = password
        self.project_id = project_id
        self.auth_url = auth_url
        self.region_name = region_name
        self.service_type = service_type
        self.insecure = insecure

    def get_name(self):
        return self.name

    def get_region(self):
        return self.region_name

    def get_flavor_name(self, flavor_id):
        if not self.flavor_cache:
            self.flavor_cache = dict([(flavor.id, flavor.name) for flavor in self.client.flavors.list()])
        return self.flavor_cache.get(flavor_id, None)

    def connect(self):
        # Make the connection
        self.client = nova_client.Client(
            self.username,
            self.password,
            self.project_id,
            self.auth_url,
            region_name=self.region_name,
            service_type=self.service_type,
            insecure=self.insecure
        )

        try:
            self.client.authenticate()
        except exceptions.Unauthorized, e:
            print("Invalid OpenStack Nova credentials.: %s" %
                  e.message)
            sys.exit(1)
        except exceptions.AuthorizationFailure, e:
            print("Unable to authorize user: %s" % e.message)
            sys.exit(1)

        if self.client is None:
            print("Failed to instantiate nova client. This "
                  "could mean that your credentials are wrong.")
            sys.exit(1)

        return self.client

    def list_servers(self):
        return self.client.servers.list()

    def get_image_name(self, image_id):
        if image_id not in self.image_cache:
            try:
                self.image_cache[image_id] = self.client.images.get(image_id)
            except exceptions.NotFound:
                self.image_cache[image_id] = None
        return self.image_cache[image_id]


def nova_load_config_file(NOVA_DEFAULTS):
    p = ConfigParser.SafeConfigParser(NOVA_DEFAULTS)

    for path in NOVA_CONFIG_FILES:
        if os.path.exists(path):
            p.read(path)
            return p
    return p


class OpenStackInventory(object):

    def __init__(self, private=False):
        self.clouds = []
        self.private = private

        OS_USERNAME = os.environ.get('OS_USERNAME', 'admin')
        NOVA_DEFAULTS = {
            'username': OS_USERNAME,
            'password': os.environ.get('OS_PASSWORD', ''),
            'project_id': os.environ.get('OS_TENANT_NAME', os.environ.get('OS_PROJECT_ID', OS_USERNAME)),
            'auth_url': os.environ.get('OS_AUTH_URL', 'https://127.0.0.1:35357/v2.0/'),
            'region_name': os.environ.get('OS_REGION_NAME', ''),
            'service_type': 'compute',
            'insecure': 'false',
        }

        # use a config file if it exists where expected
        config = nova_load_config_file(NOVA_DEFAULTS)

        if not config.sections():
            # Add a default section so that our defaults always work
            config.add_section('openstack')

        for cloud in config.sections():
            nova_client_params = dict(name=cloud)
            nova_client_params['username'] = config.get(cloud, 'username')
            nova_client_params['password'] = config.get(cloud, 'password')
            nova_client_params['project_id'] = config.get(cloud, 'project_id')
            nova_client_params['auth_url'] = config.get(cloud, 'auth_url')
            nova_client_params['region_name'] = config.get(cloud, 'region_name')
            nova_client_params['service_type'] = config.get(cloud, 'service_type')
            nova_client_params['insecure'] = config.getboolean(cloud, 'insecure')
            # Provide backwards compat for older nova.ini files
            if nova_client_params['password'] == '':
                nova_client_params['password'] = config.get(cloud, 'api_key')

            if (nova_client_params['username'] == "" and nova_client_params['password'] == ""):
                sys.exit(
                    'Unable to find auth information for cloud %s'
                    ' in config files %s or environment variables'
                    % ','.join(NOVA_CONFIG_FILES))
            for region in nova_client_params['region_name'].split(','):
                nova_client_params['region_name'] = region
                self.clouds.append(OpenStackCloud(**nova_client_params))

    def get_host_groups(self):
        groups = collections.defaultdict(list)
        hostvars = collections.defaultdict(dict)

        for cloud in self.clouds:
            cloud.connect()
            region = cloud.get_region()
            cloud_name = cloud.get_name()

            # Cycle on servers
            for server in cloud.list_servers():
                # loop through the networks for this instance, append fixed
                # and floating IPs in a list
                private = openstack_find_nova_addresses(getattr(server, 'addresses'), 'fixed', 'private')
                public = openstack_find_nova_addresses(getattr(server, 'addresses'), 'floating', 'public')

                # Create a group for the cloud
                groups[cloud_name].append(server.name)

                # Create a group on region
                groups[region].append(server.name)

                # And one by cloud_region
                groups["%s_%s" % (cloud_name, region)].append(server.name)

                # Check if group metadata key in servers' metadata
                group = server.metadata.get('group')
                if group:
                    groups[group].append(server.name)

                for extra_group in server.metadata.get('groups', '').split(','):
                    if extra_group:
                        groups[extra_group].append(server.name)

                for key, value in to_dict(server).items():
                    hostvars[server.name][key] = value

                az = hostvars[server.name].get('nova_os-ext-az_availability_zone')
                if az:
                    hostvars[server.name]['nova_az'] = az
                    # Make groups for az, region_az and cloud_region_az
                    groups[az].append(server.name)
                    groups['%s_%s' % (region, az)].append(server.name)
                    groups['%s_%s_%s' % (cloud_name, region, az)].append(server.name)

                hostvars[server.name]['nova_region'] = region
                hostvars[server.name]['openstack_cloud'] = cloud_name

                for key, value in server.metadata.iteritems():
                    prefix = os.getenv('OS_META_PREFIX', 'meta')
                    groups['%s_%s_%s' % (prefix, key, value)].append(server.name)

                if (self.private is True):
                    hostvars[server.name]['ansible_ssh_host'] = private[0]
                else:
                    hostvars[server.name]['ansible_ssh_host'] = public[0]

                groups['instance-%s' % server.id].append(server.name)
                
                groups['flavor-%s' % server.flavor['id']].append(server.name)
                flavor_name = cloud.get_flavor_name(server.flavor['id'])
                if flavor_name:
                    groups['flavor-%s' % flavor_name].append(server.name)

                groups['image-%s' % server.image['id']].append(server.name)
                image_name = cloud.get_image_name(server.image['id'])
                if image_name:
                    groups['image-%s' % image_name].append(server.name)

                # And finally, add an IP address
                if (self.private is True):
                    hostvars[server.name]['ansible_ssh_host'] = private[0]
                else:
                    hostvars[server.name]['ansible_ssh_host'] = public[0]

            if hostvars:
                groups['_meta'] = {'hostvars': hostvars}
        return groups

    def list_instances(self):
        groups = self.get_host_groups()
        # Return server list
        print(json.dumps(groups, sort_keys=True, indent=2))

    def get_host(hostname):
        groups = self.get_host_groups()
        hostvars = groups['_meta']['hostvars']
        if hostname in hostvars:
            print(json.dumps(hostvars[hostname], sort_keys=True, indent=4))


def to_dict(obj):
    instance = {}
    for key in dir(obj):
        value = getattr(obj, key)
        if (isinstance(value, NON_CALLABLES) and not key.startswith('_')):
            key = slugify('nova', key)
            instance[key] = value

    return instance


# TODO: this is something both various modules and plugins could use
def slugify(pre='', value=''):
    sep = ''
    if pre is not None and len(pre):
        sep = '_'
    return '%s%s%s' % (pre,
                       sep,
                       re.sub('[^\w-]', '_', value).lower().lstrip('_'))


def parse_args():
    parser = argparse.ArgumentParser(description='Nova Inventory Module')
    parser.add_argument('--private',
                        action='store_true',
                        help='Use private address for ansible host')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific host')
    return parser.parse_args()


def main():
    args = parse_args()
    inventory = OpenStackInventory(args.private)
    if args.list:
        inventory.list_instances()
    elif args.host:
        inventory.get_host(args.host)
    sys.exit(0)


if __name__ == '__main__':
    main()
