#!/usr/bin/env python

# (c) 2013, Jesse Keating <jesse.keating@rackspace.com,
#           Paul Durivage <paul.durivage@rackspace.com>,
#           Matt Martz <matt@sivel.net>
#
# This file is part of Ansible.
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

"""
Rackspace Cloud Inventory

Authors:
    Jesse Keating <jesse.keating@rackspace.com,
    Paul Durivage <paul.durivage@rackspace.com>,
    Matt Martz <matt@sivel.net>


Description:
    Generates inventory that Ansible can understand by making API request to
    Rackspace Public Cloud API

    When run against a specific host, this script returns variables similar to:
        rax_os-ext-sts_task_state
        rax_addresses
        rax_links
        rax_image
        rax_os-ext-sts_vm_state
        rax_flavor
        rax_id
        rax_rax-bandwidth_bandwidth
        rax_user_id
        rax_os-dcf_diskconfig
        rax_accessipv4
        rax_accessipv6
        rax_progress
        rax_os-ext-sts_power_state
        rax_metadata
        rax_status
        rax_updated
        rax_hostid
        rax_name
        rax_created
        rax_tenant_id
        rax_loaded

Notes:
    RAX_CREDS_FILE is an optional environment variable that points to a
    pyrax-compatible credentials file.

    If RAX_CREDS_FILE is not supplied, rax.py will look for a credentials file
    at ~/.rackspace_cloud_credentials.  It uses the Rackspace Python SDK, and
    therefore requires a file formatted per the SDK's specifications. See
    https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md
    #authenticating

    RAX_REGION is an optional environment variable to narrow inventory search
    scope.  RAX_REGION, if used, needs a value like ORD, DFW, SYD (a Rackspace
    datacenter) and optionally accepts a comma-separated list.

    RAX_ENV is an environment variable that will use an environment as
    configured in ~/.pyrax.cfg, see
    https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md

    RAX_META_PREFIX is an environment variable that changes the prefix used
    for meta key/value groups. For compatibility with ec2.py set to
    RAX_META_PREFIX=tag

    RAX_ACCESS_NETWORK is an environment variable that will tell the inventory
    script to use a specific server network to determine the ansible_ssh_host
    value. If no address is found, ansible_ssh_host will not be set.

    RAX_ACCESS_IP_VERSION is an environment variable related to
    RAX_ACCESS_NETWORK that will attempt to determine the ansible_ssh_host
    value for either IPv4 or IPv6. If no address is found, ansible_ssh_host
    will not be set. Acceptable values are: 4 or 6. Values other than 4 or 6
    will be ignored, and 4 will be used.

Examples:
    List server instances
    $ RAX_CREDS_FILE=~/.raxpub rax.py --list

    List servers in ORD datacenter only
    $ RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD rax.py --list

    List servers in ORD and DFW datacenters
    $ RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD,DFW rax.py --list

    Get server details for server named "server.example.com"
    $ RAX_CREDS_FILE=~/.raxpub rax.py --host server.example.com

    Use the instance private IP to connect (instead of public IP)
    $ RAX_CREDS_FILE=~/.raxpub RAX_PRIVATE_IP=yes rax.py --list
"""

import os
import re
import sys
import argparse
import warnings
import collections

from types import NoneType

try:
    import json
except ImportError:
    import simplejson as json

try:
    import pyrax
except ImportError:
    print('pyrax is required for this module')
    sys.exit(1)

NON_CALLABLES = (basestring, bool, dict, int, list, NoneType)


def rax_slugify(value):
    return 'rax_%s' % (re.sub('[^\w-]', '_', value).lower().lstrip('_'))


def to_dict(obj):
    instance = {}
    for key in dir(obj):
        value = getattr(obj, key)
        if isinstance(value, NON_CALLABLES) and not key.startswith('_'):
            key = rax_slugify(key)
            instance[key] = value

    return instance


def host(regions, hostname):
    hostvars = {}

    for region in regions:
        # Connect to the region
        cs = pyrax.connect_to_cloudservers(region=region)
        for server in cs.servers.list():
            if server.name == hostname:
                for key, value in to_dict(server).items():
                    hostvars[key] = value

                # And finally, add an IP address
                hostvars['ansible_ssh_host'] = server.accessIPv4
    print(json.dumps(hostvars, sort_keys=True, indent=4))


def _list(regions):
    groups = collections.defaultdict(list)
    hostvars = collections.defaultdict(dict)
    images = {}

    network = os.getenv('RAX_ACCESS_NETWORK', 'public')
    try:
        ip_version = int(os.getenv('RAX_ACCESS_IP_VERSION', 4))
    except:
        ip_version = 4
    else:
        if ip_version not in [4, 6]:
            ip_version = 4

    # Go through all the regions looking for servers
    for region in regions:
        # Connect to the region
        cs = pyrax.connect_to_cloudservers(region=region)
        if isinstance(cs, NoneType):
            warnings.warn(
                'Connecting to Rackspace region "%s" has caused Pyrax to '
                'return a NoneType. Is this a valid region?' % region,
                RuntimeWarning)
            continue
        for server in cs.servers.list():
            # Create a group on region
            groups[region].append(server.name)

            # Check if group metadata key in servers' metadata
            group = server.metadata.get('group')
            if group:
                groups[group].append(server.name)

            for extra_group in server.metadata.get('groups', '').split(','):
                if extra_group:
                    groups[extra_group].append(server.name)

            # Add host metadata
            for key, value in to_dict(server).items():
                hostvars[server.name][key] = value

            hostvars[server.name]['rax_region'] = region

            for key, value in server.metadata.iteritems():
                prefix = os.getenv('RAX_META_PREFIX', 'meta')
                groups['%s_%s_%s' % (prefix, key, value)].append(server.name)

            groups['instance-%s' % server.id].append(server.name)
            groups['flavor-%s' % server.flavor['id']].append(server.name)
            try:
                imagegroup = 'image-%s' % images[server.image['id']]
                groups[imagegroup].append(server.name)
                groups['image-%s' % server.image['id']].append(server.name)
            except KeyError:
                try:
                    image = cs.images.get(server.image['id'])
                except cs.exceptions.NotFound:
                    groups['image-%s' % server.image['id']].append(server.name)
                else:
                    images[image.id] = image.human_id
                    groups['image-%s' % image.human_id].append(server.name)
                    groups['image-%s' % server.image['id']].append(server.name)

            # And finally, add an IP address
            ansible_ssh_host = None
            # use accessIPv[46] instead of looping address for 'public'
            if network == 'public':
                if ip_version == 6 and server.accessIPv6:
                    ansible_ssh_host = server.accessIPv6
                elif server.accessIPv4:
                    ansible_ssh_host = server.accessIPv4
            else:
                addresses = server.addresses.get(network, [])
                for address in addresses:
                    if address.get('version') == ip_version:
                        ansible_ssh_host = address.get('addr')
                        break
            if ansible_ssh_host:
                hostvars[server.name]['ansible_ssh_host'] = ansible_ssh_host

    if hostvars:
        groups['_meta'] = {'hostvars': hostvars}
    print(json.dumps(groups, sort_keys=True, indent=4))


def parse_args():
    parser = argparse.ArgumentParser(description='Ansible Rackspace Cloud '
                                                 'inventory module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specific host')
    return parser.parse_args()


def setup():
    default_creds_file = os.path.expanduser('~/.rackspace_cloud_credentials')

    env = os.getenv('RAX_ENV', None)
    if env:
        pyrax.set_environment(env)

    keyring_username = pyrax.get_setting('keyring_username')

    # Attempt to grab credentials from environment first
    try:
        creds_file = os.path.expanduser(os.environ['RAX_CREDS_FILE'])
    except KeyError, e:
        # But if that fails, use the default location of
        # ~/.rackspace_cloud_credentials
        if os.path.isfile(default_creds_file):
            creds_file = default_creds_file
        elif not keyring_username:
            sys.stderr.write('No value in environment variable %s and/or no '
                             'credentials file at %s\n'
                             % (e.message, default_creds_file))
            sys.exit(1)

    identity_type = pyrax.get_setting('identity_type')
    pyrax.set_setting('identity_type', identity_type or 'rackspace')

    region = pyrax.get_setting('region')

    try:
        if keyring_username:
            pyrax.keyring_auth(keyring_username, region=region)
        else:
            pyrax.set_credential_file(creds_file, region=region)
    except Exception, e:
        sys.stderr.write("%s: %s\n" % (e, e.message))
        sys.exit(1)

    regions = []
    if region:
        regions.append(region)
    else:
        for region in os.getenv('RAX_REGION', 'all').split(','):
            region = region.strip().upper()
            if region == 'ALL':
                regions = pyrax.regions
                break
            elif region not in pyrax.regions:
                sys.stderr.write('Unsupported region %s' % region)
                sys.exit(1)
            elif region not in regions:
                regions.append(region)

    return regions


def main():
    args = parse_args()
    regions = setup()
    if args.list:
        _list(regions)
    elif args.host:
        host(regions, args.host)
    sys.exit(0)


if __name__ == '__main__':
    main()
