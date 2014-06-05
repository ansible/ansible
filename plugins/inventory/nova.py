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

DOCUMENTATION = '''
---
inventory: nova
short_description: OpenStack external inventory script
description:
  - Generates inventory that Ansible can understand by making API request to OpenStack endpoint using the novaclient library.
  - |
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
  - All information are set on B(nova.ini) file
version_added: None
options:
  version:
    description:
      - OpenStack version to use.
    required: true
    default: null
    choices: [ "1.1", "2" ]
  username:
    description:
      - Username used to authenticate in OpenStack.
    required: true
    default: null
  api_key:
    description:
      - Password used to authenticate in OpenStack, can be the ApiKey on some authentication system.
    required: true
    default: null
  auth_url:
    description:
      - Authentication URL required to generate token.
      - To manage RackSpace use I(https://identity.api.rackspacecloud.com/v2.0/)
    required: true
    default: null
  auth_system:
    description:
      - Authentication system used to login
      - To manage RackSpace install B(rackspace-novaclient) and insert I(rackspace)
    required: true
    default: null
  region_name:
    description:
      - Region name to use in request
      - In RackSpace some value can be I(ORD) or I(DWF).
    required: true
    default: null
  project_id:
    description:
      - Project ID to use in connection
      - In RackSpace use OS_TENANT_NAME
    required: false
    default: null
  endpoint_type:
    description:
      - The endpoint type for novaclient
      - In RackSpace use 'publicUrl'
    required: false
    default: null
  service_type:
    description:
      - The service type you are managing.
      - In RackSpace use 'compute'
    required: false
    default: null
  service_name:
    description:
      - The service name you are managing.
      - In RackSpace use 'cloudServersOpenStack'
    required: false
    default: null
  insicure:
    description:
      - To no check security
    required: false
    default: false
    choices: [ "true", "false" ]
author: Marco Vito Moscaritolo
notes:
  - This script assumes Ansible is being executed where the environment variables needed for novaclient have already been set on nova.ini file
  - For more details, see U(https://github.com/openstack/python-novaclient)
examples:
    - description: List instances
      code: nova.py --list
    - description: Instance property
      code: nova.py --instance INSTANCE_IP
'''


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

NOVA_CONFIG_FILES = [os.getcwd() + "/nova.ini",
                     os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/nova.ini")),
                     "/etc/ansible/nova.ini"]

def nova_load_config_file():
    p = ConfigParser.SafeConfigParser()

    for path in NOVA_CONFIG_FILES:
        if os.path.exists(path):
            p.read(path)
            return p

    return None

config = nova_load_config_file()
if not config:
    sys.exit('Unable to find configfile in %s' % ', '.join(NOVA_CONFIG_FILES))

client = nova_client.Client(
    version     = config.get('openstack', 'version'),
    username    = config.get('openstack', 'username'),
    api_key     = config.get('openstack', 'api_key'),
    auth_url    = config.get('openstack', 'auth_url'),
    region_name = config.get('openstack', 'region_name'),
    project_id  = config.get('openstack', 'project_id'),
    auth_system = config.get('openstack', 'auth_system')
)

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    groups = {}

    # Cycle on servers
    for f in client.servers.list():
	private = [ x['addr'] for x in getattr(f, 'addresses').itervalues().next() if x['OS-EXT-IPS:type'] == 'fixed']
	public  = [ x['addr'] for x in getattr(f, 'addresses').itervalues().next() if x['OS-EXT-IPS:type'] == 'floating']
	    
	# Define group (or set to empty string)
        group = f.metadata['group'] if f.metadata.has_key('group') else 'undefined'

        # Create group if not exist
        if group not in groups:
            groups[group] = []

        # Append group to list
	if f.accessIPv4:
        	groups[group].append(f.accessIPv4)
		continue
	if public:
        	groups[group].append(''.join(public))
		continue
	if private:
        	groups[group].append(''.join(private))
		continue

    # Return server list
    print json.dumps(groups)
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    ips = []
    for instance in client.servers.list():
	private = [ x['addr'] for x in getattr(instance, 'addresses').itervalues().next() if x['OS-EXT-IPS:type'] == 'fixed']
	public =  [ x['addr'] for x in getattr(instance, 'addresses').itervalues().next() if x['OS-EXT-IPS:type'] == 'floating']
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

    print json.dumps(results)
    sys.exit(0)

else:
    print "usage: --list  ..OR.. --host <hostname>"
    sys.exit(1)
