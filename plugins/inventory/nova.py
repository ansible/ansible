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
import ConfigParser
from novaclient import client as nova_client

try:
    import json
except:
    import simplejson as json

from ansible.module_utils.openstack import *

###################################################
# executed with no parameters, return the list of
# all groups and hosts

NOVA_CONFIG_FILES = [os.getcwd() + "/nova.ini",
                     os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/nova.ini")),
                     "/etc/ansible/nova.ini"]

NOVA_DEFAULTS = {
    'auth_system': None,
    'region_name': None,
}


def nova_load_config_file():
    p = ConfigParser.SafeConfigParser(NOVA_DEFAULTS)

    for path in NOVA_CONFIG_FILES:
        if os.path.exists(path):
            p.read(path)
            return p

    return None

config = nova_load_config_file()
if not config:
    sys.exit('Unable to find configfile in %s' % ', '.join(NOVA_CONFIG_FILES))

client = nova_client.Client(
    config.get('openstack', 'version'),
    config.get('openstack', 'username'),
    config.get('openstack', 'api_key'),
    config.get('openstack', 'project_id'),
    config.get('openstack', 'auth_url'),
    region_name = config.get('openstack', 'region_name'),
    auth_system = config.get('openstack', 'auth_system')
)

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
