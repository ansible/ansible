#!/usr/bin/python

"""
OpenStack external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
OpenStack endpoint using the novaclient library.

NOTE: This script assumes Ansible is being executed where the environment
variables needed for novaclient have already been set on nova.ini file

For more details, see: https://github.com/openstack/python-novaclient

When run against a specific host, this script returns the following variables:
    os_os-ext-sts_task_state
    os_addresses
    os_links
    os_image
    os_os-ext-sts_vm_state
    os_flavor
    os_id
    os_rax-bandwidth_bandwidth
    os_user_id
    os_os-dcf_diskconfig
    os_accessipv4
    os_accessipv6
    os_progress
    os_os-ext-sts_power_state
    os_metadata
    os_status
    os_updated
    os_hostid
    os_name
    os_created
    os_tenant_id
    os__info
    os__loaded

where some item can have nested structure.

"""

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

######################################################################


import sys
import re
import os
import ConfigParser
from novaclient import client as nova_client

try:
    import json
except:
    import simplejson as json

###################################################
# executed with no parameters, return the list of
# all groups and hosts


config = ConfigParser.SafeConfigParser()
config.read(os.path.dirname(os.path.realpath(__file__)) + '/nova.ini')

client = nova_client.Client(
    version     = config.get('openstack', 'version'),
    username    = config.get('openstack', 'username'),
    api_key     = config.get('openstack', 'api_key'),
    auth_url    = config.get('openstack', 'auth_url'),
    project_id  = config.get('openstack', 'project_id')
)

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    groups = {}

    # Cycle on servers
    for f in client.servers.list():
        # Define group (or set to empty string)
        group = f.metadata['group'] if f.metadata.has_key('group') else 'undefined'

        # Create group if not exist
        if group not in groups:
            groups[group] = []

        # Append group to list
        groups[group].append(f.accessIPv4)

    # Return server list
    print json.dumps(groups)
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    for instance in client.servers.list():
        if instance.accessIPv4 == sys.argv[2]:
            for key in vars(instance):
                # Extract value
                value = getattr(instance, key)

                # Generate sanitized key
                key = 'os_' + re.sub("[^A-Za-z0-9\-]", "_", key).lower()

                # Att value to instance result (exclude manager class)
                #TODO: maybe use value.__class__ or similar inside of key_name
                if key != 'os_manager':
                    results[key] = value

    print json.dumps(results)
    sys.exit(0)

else:
    print "usage: --list  ..OR.. --host <hostname>"
    sys.exit(1)
