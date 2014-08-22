#!/usr/bin/env python

# (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
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
from novaclient.client import Client
from credentials import get_nova_credentials_v2
try:
    import json
except:
    import simplejson as json

from ansible.module_utils.openstack import *

###################################################
# executed with no parameters, return the list of
# all groups and hosts

credentials = get_nova_credentials_v2()
client = Client(**credentials)

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    groups = {}

    # Cycle on servers
    for server in client.servers.list():
        private = openstack_find_nova_addresses(getattr(server, 'addresses'), 'fixed', 'private')
        public = openstack_find_nova_addresses(getattr(server, 'addresses'), 'floating', 'public')

	# Define group (or set to empty string)
        group = server.metadata['group'] if server.metadata.has_key('group') else 'undefined'

        # Create group if not exist
        if group not in groups:
            groups[group] = []

        # Append group to list
	if server.accessIPv4:
                groups[group].append(server.accessIPv4)
		continue
	if public:
        	groups[group].append(''.join(public))
		continue
	if private:
        	groups[group].append(''.join(private))
		continue

    # Return server list
    print(json.dumps(groups, sort_keys=True, indent=2))
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    ips = []
    for instance in client.servers.list():
        private = openstack_find_nova_addresses(getattr(instance, 'addresses'), 'fixed', 'private')
        public = openstack_find_nova_addresses(getattr(instance, 'addresses'), 'floating', 'public')
        ips.append( instance.accessIPv4)
	ips.append(''.join(private))
	ips.append(''.join(public))
	if sys.argv[2] in ips:
            for key in vars(instance):
                # Extract value
                value = getattr(instance, key)

                # Generate sanitized key
                key = 'os_' + re.sub("[^A-Za-z0-9\-]", "_", key).lower()

                # Att value to instance result (exclude manager class)
                #TODO: maybe use value.__class__ or similar inside of key_name
                if key != 'os_manager':
                    results[key] = value

    print(json.dumps(results, sort_keys=True, indent=2))
    sys.exit(0)

else:
    print "usage: --list  ..OR.. --host <hostname>"
    sys.exit(1)
