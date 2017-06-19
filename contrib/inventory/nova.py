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

# WARNING: This file is deprecated. New work should focus on the openstack.py
# inventory module, which properly handles multiple clouds as well as keystone
# v3 and keystone auth plugins

import sys
import re
import os
import ConfigParser
from novaclient import client as nova_client
from six import iteritems, itervalues

try:
    import json
except ImportError:
    import simplejson as json


sys.stderr.write("WARNING: this inventory module is deprecated. please migrate usage to openstack.py\n")

###################################################
# executed with no parameters, return the list of
# all groups and hosts

NOVA_CONFIG_FILES = [os.getcwd() + "/nova.ini",
                     os.path.expanduser(os.environ.get('ANSIBLE_CONFIG', "~/nova.ini")),
                     "/etc/ansible/nova.ini"]

NOVA_DEFAULTS = {
    'auth_system': None,
    'region_name': None,
    'service_type': 'compute',
}


def nova_load_config_file():
    p = ConfigParser.SafeConfigParser(NOVA_DEFAULTS)

    for path in NOVA_CONFIG_FILES:
        if os.path.exists(path):
            p.read(path)
            return p

    return None


def get_fallback(config, value, section="openstack"):
    """
    Get value from config object and return the value
    or false
    """
    try:
        return config.get(section, value)
    except ConfigParser.NoOptionError:
        return False


def push(data, key, element):
    """
    Assist in items to a dictionary of lists
    """
    if (not element) or (not key):
        return

    if key in data:
        data[key].append(element)
    else:
        data[key] = [element]


def to_safe(word):
    '''
    Converts 'bad' characters in a string to underscores so they can
    be used as Ansible groups
    '''
    return re.sub(r"[^A-Za-z0-9\-]", "_", word)


def get_ips(server, access_ip=True):
    """
    Returns a list of the server's IPs, or the preferred
    access IP
    """
    private = []
    public = []
    address_list = []
    # Iterate through each servers network(s), get addresses and get type
    addresses = getattr(server, 'addresses', {})
    if len(addresses) > 0:
        for network in itervalues(addresses):
            for address in network:
                if address.get('OS-EXT-IPS:type', False) == 'fixed':
                    private.append(address['addr'])
                elif address.get('OS-EXT-IPS:type', False) == 'floating':
                    public.append(address['addr'])

    if not access_ip:
        address_list.append(server.accessIPv4)
        address_list.extend(private)
        address_list.extend(public)
        return address_list

    access_ip = None
    # Append group to list
    if server.accessIPv4:
        access_ip = server.accessIPv4
    if (not access_ip) and public and not (private and prefer_private):
        access_ip = public[0]
    if private and not access_ip:
        access_ip = private[0]

    return access_ip


def get_metadata(server):
    """Returns dictionary of all host metadata"""
    get_ips(server, False)
    results = {}
    for key in vars(server):
        # Extract value
        value = getattr(server, key)

        # Generate sanitized key
        key = 'os_' + re.sub(r"[^A-Za-z0-9\-]", "_", key).lower()

        # Att value to instance result (exclude manager class)
        # TODO: maybe use value.__class__ or similar inside of key_name
        if key != 'os_manager':
            results[key] = value
    return results

config = nova_load_config_file()
if not config:
    sys.exit('Unable to find configfile in %s' % ', '.join(NOVA_CONFIG_FILES))

# Load up connections info based on config and then environment
# variables
username = (get_fallback(config, 'username') or
            os.environ.get('OS_USERNAME', None))
api_key = (get_fallback(config, 'api_key') or
           os.environ.get('OS_PASSWORD', None))
auth_url = (get_fallback(config, 'auth_url') or
            os.environ.get('OS_AUTH_URL', None))
project_id = (get_fallback(config, 'project_id') or
              os.environ.get('OS_TENANT_NAME', None))
region_name = (get_fallback(config, 'region_name') or
               os.environ.get('OS_REGION_NAME', None))
auth_system = (get_fallback(config, 'auth_system') or
               os.environ.get('OS_AUTH_SYSTEM', None))

# Determine what type of IP is preferred to return
prefer_private = False
try:
    prefer_private = config.getboolean('openstack', 'prefer_private')
except ConfigParser.NoOptionError:
    pass

client = nova_client.Client(
    version=config.get('openstack', 'version'),
    username=username,
    api_key=api_key,
    auth_url=auth_url,
    region_name=region_name,
    project_id=project_id,
    auth_system=auth_system,
    service_type=config.get('openstack', 'service_type'),
)

# Default or added list option
if (len(sys.argv) == 2 and sys.argv[1] == '--list') or len(sys.argv) == 1:
    groups = {'_meta': {'hostvars': {}}}
    # Cycle on servers
    for server in client.servers.list():
        access_ip = get_ips(server)

        # Push to name group of 1
        push(groups, server.name, access_ip)

        # Run through each metadata item and add instance to it
        for key, value in iteritems(server.metadata):
            composed_key = to_safe('tag_{0}_{1}'.format(key, value))
            push(groups, composed_key, access_ip)

        # Do special handling of group for backwards compat
        # inventory groups
        group = server.metadata['group'] if 'group' in server.metadata else 'undefined'
        push(groups, group, access_ip)

        # Add vars to _meta key for performance optimization in
        # Ansible 1.3+
        groups['_meta']['hostvars'][access_ip] = get_metadata(server)

    # Return server list
    print(json.dumps(groups, sort_keys=True, indent=2))
    sys.exit(0)

#####################################################
# executed with a hostname as a parameter, return the
# variables for that host

elif len(sys.argv) == 3 and (sys.argv[1] == '--host'):
    results = {}
    ips = []
    for server in client.servers.list():
        if sys.argv[2] in (get_ips(server) or []):
            results = get_metadata(server)
    print(json.dumps(results, sort_keys=True, indent=2))
    sys.exit(0)

else:
    sys.exit("usage: --list  ..OR.. --host <hostname>")
