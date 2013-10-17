#!/usr/bin/env python

# (c) 2013, Jesse Keating <jesse.keating@rackspace.com>
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

DOCUMENTATION = '''
---
inventory: rax
short_description: Rackspace Public Cloud external inventory script
description:
  - Generates inventory that Ansible can understand by making API request to Rackspace Public Cloud API
  - |
    When run against a specific host, this script returns the following variables:
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

    where some item can have nested structure.
  - credentials are set in a credentials file
version_added: None
options:
  creds_file:
    description:
     - File to find the Rackspace Public Cloud credentials in
    required: true
    default: null
  region:
    description:
     - An optional value to narrow inventory scope, i.e. DFW, ORD, IAD, LON
     required: false
     default: null
authors:
  - Jesse Keating <jesse.keating@rackspace.com>
  - Paul Durivage <paul.durivage@rackspace.com>
notes:
  - One environment variable needs to be set: RAX_CREDS_FILE.
  - RAX_CREDS_FILE points to a credentials file appropriate for pyrax.
  - See https://github.com/rackspace/pyrax/blob/master/docs/getting_started.md#authenticating
  - RAX_REGION is an optional environment variable to narrow inventory search scope
  - RAX_REGION, if used, needs a value like ORD, DFW, SYD (a Rackspace datacenter) and optionally accepts a comma-separated list
requirements: [ "pyrax" ]
examples:
    - description: List server instances
      code: RAX_CREDS_FILE=~/.raxpub rax.py --list
    - description: List servers in ORD datacenter only
      code: RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD rax.py --list
    - description: List servers in ORD and DFW datacenters
      code: RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD,DFW rax.py --list
    - description: Get server details for server named "server.example.com"
      code: RAX_CREDS_FILE=~/.raxpub rax.py --host server.example.com
'''

import sys
import re
import os
import argparse
import collections

try:
    import json
except:
    import simplejson as json

try:
    import pyrax
except ImportError:
    print('pyrax required for this module')
    sys.exit(1)


def host(hostname):
    hostvars = {}

    for region in pyrax.regions:
        # Connect to the region
        cs = pyrax.connect_to_cloudservers(region=region)
        for server in cs.servers.list():
            if server.name == hostname:
                keys = [key for key in vars(server) if key not in ('manager', '_info')]
                for key in keys:
                    # Extract value
                    value = getattr(server, key)

                    # Generate sanitized key
                    key = 'rax_' + (re.sub("[^A-Za-z0-9\-]", "_", key)
                                      .lower()
                                      .lstrip("_"))
                    hostvars[key] = value

                # And finally, add an IP address
                hostvars['ansible_ssh_host'] = server.accessIPv4
    print(json.dumps(hostvars, sort_keys=True, indent=4))


def _list(region):
    groups = collections.defaultdict(list)
    hostvars = collections.defaultdict(dict)

    if region and region.upper() in pyrax.regions:
        pyrax.regions = (region.upper() for region in region.split(','))


    # Go through all the regions looking for servers
    for region in pyrax.regions:
        # Connect to the region
        cs = pyrax.connect_to_cloudservers(region=region)
        for server in cs.servers.list():
            # Create a group on region
            groups[region].append(server.name)

            # Anything we can discern from the hostname?
            try:
                subdom = server.name.split('.')[0]
            except IndexError:
                pass
            else:
                for name in ('web', 'db', 'sql', 'lb', 'app'):
                    if name in subdom:
                        groups[name].append(server.name)

            # Check if group metadata key in servers' metadata
            try:
                group = server.metadata['group']
            except KeyError:
                pass
            else:
                # Create group if not exist and add the server
                groups[group].append(server.name)

            # Add host metadata
            keys = [key for key in vars(server) if key not in ('manager', '_info')]
            for key in keys:
                # Extract value
                value = getattr(server, key)

                # Generate sanitized key
                key = 'rax_' + (re.sub("[^A-Za-z0-9\-]", "_", key)
                                  .lower()
                                  .lstrip('_'))
                hostvars[server.name][key] = value

            # And finally, add an IP address
            hostvars[server.name]['ansible_ssh_host'] = server.accessIPv4

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
    try:
        creds_file = os.environ['RAX_CREDS_FILE']
        region = os.getenv('RAX_REGION')
    except KeyError, e:
        sys.stderr.write('Unable to load environment '
                         'variable %s\n' % e.message)
        sys.exit(1)

    pyrax.set_setting('identity_type', 'rackspace')

    try:
        pyrax.set_credential_file(os.path.expanduser(creds_file))
    except Exception, e:
        sys.stderr.write("%s: %s\n" % (e, e.message))
        sys.exit(1)

    return region


def main():
    args = parse_args()
    region = setup()
    if args.list:
        _list(region)
    elif args.host:
        host(args.host)
    sys.exit(0)

if __name__ == '__main__':
    main()
