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
        rax__loaded

    where some item can have nested structure.
  - credentials are set in a credentials file
version_added: None
options:
  creds_file:
    description:
     - File to find the Rackspace Public Cloud credentials in
    required: true
    default: null
  region_name:
    description:
      - Region name to use in request
    required: false
    default: DFW
author: Jesse Keating
notes:
  - Two environment variables need to be set, RAX_CREDS and RAX_REGION.
  - RAX_CREDS points to a credentials file appropriate for pyrax
  - RAX_REGION defines a Rackspace Public Cloud region (DFW, ORD, LON, ...)
requirements: [ "pyrax" ]
examples:
    - description: List server instances
      code: RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD rax.py --list
    - description: List server instance properties
      code: RAX_CREDS_FILE=~/.raxpub RAX_REGION=ORD rax.py --host <HOST_IP>
'''

import sys
import re
import os
import argparse

try:
    import json
except:
    import simplejson as json

try:
    import pyrax
except ImportError:
    print('pyrax required for this module')
    sys.exit(1)

# Setup the parser
parser = argparse.ArgumentParser(description='List active instances',
                            epilog='List by itself will list all the active \
                            instances. Listing a specific instance will show \
                            all the details about the instance.')

parser.add_argument('--list', action='store_true', default=True,
                            help='List active servers')
parser.add_argument('--host',
                    help='List details about the specific host (IP address)')

args = parser.parse_args()

# setup the auth
try:
    creds_file = os.environ['RAX_CREDS_FILE']
    region = os.environ['RAX_REGION']
except KeyError, e:
    sys.stderr.write('Unable to load %s\n' % e.message)
    sys.exit(1)

pyrax.set_setting('identity_type', 'rackspace')

try:
    pyrax.set_credential_file(os.path.expanduser(creds_file),
                              region=region)
except Exception, e:
    sys.stderr.write("%s: %s\n" % (e, e.message))
    sys.exit(1)

# Execute the right stuff
if not args.host:
    groups = {}

    # Cycle on servers
    for server in pyrax.cloudservers.list():
        # Define group (or set to empty string)
        try:
            group = server.metadata['group']
        except KeyError:
            group = 'undefined'

        # Create group if not exist and add the server
        groups.setdefault(group, []).append(server.accessIPv4)

    # Return server list
    print(json.dumps(groups))
    sys.exit(0)

# Get the deets for the instance asked for
results = {}
# This should be only one, but loop anyway
for server in pyrax.cloudservers.list():
    if server.accessIPv4 == args.host:
        for key in [key for key in vars(server) if
                    key not in ('manager', '_info')]:
            # Extract value
            value = getattr(server, key)
    
            # Generate sanitized key
            key = 'rax_' + re.sub("[^A-Za-z0-9\-]", "_", key).lower()
            results[key] = value

print(json.dumps(results))
sys.exit(0)
