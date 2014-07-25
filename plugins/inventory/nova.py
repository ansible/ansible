#!/usr/bin/env python

# (c) 2012, Marco Vito Moscaritolo <marco@agavee.com>
# (c) 2014 Patrick "CaptTofu" Galbraith <patg@patg.net> 
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
from novaclient.v1_1 import client as nova_client
from novaclient import exceptions

try:
    import json
except:
    import simplejson as json

###################################################
# executed with no parameters, return the list of
# all groups and hosts

USERNAME = os.getenv('OS_USERNAME')
PASSWORD = os.getenv('OS_PASSWORD')
AUTH_URL = os.getenv('OS_AUTH_URL')
REGION_NAME = os.getenv('OS_REGION_NAME')
TENANT_NAME = os.getenv('OS_TENANT_NAME')

NOVA_CONFIG_FILES = [
    os.getcwd() + "/nova.ini",
    os.path.expanduser(
        os.environ.get(
            'ANSIBLE_CONFIG',
            "~/nova.ini")
    ),
    "/etc/ansible/nova.ini"
]

NOVA_DEFAULTS = {
    'auth_system': 'keystone',
    'region_name': 'region1',
    'service_type': 'compute'
}
SERVICE_TYPE = NOVA_DEFAULTS['service_type']
AUTH_SYSTEM = NOVA_DEFAULTS['auth_system']


def nova_load_config_file():
    p = ConfigParser.SafeConfigParser(NOVA_DEFAULTS)

    for path in NOVA_CONFIG_FILES:
        if os.path.exists(path):
            p.read(path)
            return p

    return None

# use a config file if it exists where expected
config = nova_load_config_file()
if not config:
    if not (USERNAME and PASSWORD and AUTH_URL
            and REGION_NAME and TENANT_NAME):
        sys.exit(
            'Unable to find configfile in %s' % ','
            .join(NOVA_CONFIG_FILES))
else:
    USERNAME = config.get('openstack', 'username')
    PASSWORD = config.get('openstack', 'password')
    TENANT_NAME = config.get('openstack', 'project_id')
    if not TENANT_NAME:
        TENANT_NAME = config.get('openstack', 'tenant_name')
    AUTH_URL = config.get('openstack', 'auth_url')
    REGION_NAME = config.get('openstack', 'region_name')
    SERVICE_TYPE = config.get('openstack', 'service_type')
    AUTH_SYSTEM = config.get('openstack', 'auth_system')

# Make the connection
client = nova_client.Client(
    USERNAME,
    PASSWORD,
    TENANT_NAME,
    AUTH_URL,
    region_name=REGION_NAME,
    service_type=SERVICE_TYPE,
    auth_system=AUTH_SYSTEM
)

try:
    client.authenticate()
except exceptions.Unauthorized, e:
    print("Invalid OpenStack Nova credentials.: %s" %
          e.message)
    sys.exit(1)
except exceptions.AuthorizationFailure, e:
    print("Unable to authorize user: %s" % e.message)
    sys.exit(1)

if client is None:
    print("Failed to instantiate nova client. This "
          "could mean that your credentials are wrong.")
    sys.exit(1)

if len(sys.argv) == 2 and (sys.argv[1] == '--list'):
    groups = {}

    # Cycle on servers
    for f in client.servers.list():
        private = [x['addr'] for x in
                   getattr(f, 'addresses').itervalues().next()
                   if x['OS-EXT-IPS:type'] == 'fixed']
        public = [x['addr'] for x in
                  getattr(f, 'addresses').itervalues().next()
                  if x['OS-EXT-IPS:type'] == 'floating']

        # Define group (or set to empty string)
        group = f.metadata['group'] if 'group' in f.metadata else 'undefined'

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
    print(json.dumps(groups, sort_keys=True, indent=2))
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    ips = []
    for instance in client.servers.list():
        private = [x['addr'] for x in
                   getattr(instance, 'addresses').itervalues().next()
                   if x['OS-EXT-IPS:type'] == 'fixed']
        public = [x['addr'] for x in
                  getattr(instance, 'addresses').itervalues().next()
                  if x['OS-EXT-IPS:type'] == 'floating']
        ips.append(instance.accessIPv4)
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
