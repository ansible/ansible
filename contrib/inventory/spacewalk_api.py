#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function
__metaclass__ = type

# (c) 2019 Jacob Salmela <me@jacobsalmela.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
short_description: A dynamic inventory script that uses the Spacewalk API
description:
    - A dynamic inventory script for Ansible that uses the Spacewalk API
    - It generates an inventory of all hosts and some of their attributes
version_added: "2.8"
author: "Jacob Salmela (@jacobsalmela)"
options:
# One or more of the following
    option_name:
        description:
            - Description of the options goes here.
            - Must be written in sentences.
        required: true or false
        default: a string or the word null
        choices:
          - enable
          - disable
        aliases:
          - repo_name
        version_added: "2.8"
requirements:
    - A Spacewalk server => v2.9
    - like the factor package
    - Click == 7.0
"""

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
#

# notes:
# Tested on Spacewalk v2.9 and Ansible v2.8.1
# This is a dynamic inventory script that uses the Spacewalk API as a source
# Spacewalk won't be developed much more, at least by Redhat, but
# if you have a spacewalk server for patches, you may like to keep it around
# Often, the servers you patch are the ones you need to know about, thus
# this inventory gives you a decent source of truth if you don't have a CMDB
# The only thing you should need are the three ENV vars and then run the script

import json
import ssl
import sys
# Support python2 and 3
if sys.version_info[0] < 3:
    import xmlrpclib
else:
    import xmlrpc.client as xmlrpclib
import os
import click

# Get credentials from environment variables
# "https://spacewalk.local/rpc/api"
SATELLITE_URL = os.environ["SATELLITE_URL"]
# A read-only API use is a decent choice for this
SATELLITE_LOGIN = os.environ["SATELLITE_LOGIN"]
SATELLITE_PASSWORD = os.environ["SATELLITE_PASSWORD"]

# Format Ansible expects:
# DYNAMIC_INVENTORY = { "group": { "hosts": [], "vars": {} }, "_meta": {} } }
DYNAMIC_INVENTORY = {}

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

# Connection info
CLIENT = xmlrpclib.Server(SATELLITE_URL, verbose=False)
KEY = CLIENT.auth.login(SATELLITE_LOGIN, SATELLITE_PASSWORD)

# Get a list of all the clients connected to the Spacwalk server
HOST_LIST = CLIENT.system.list_systems(KEY)
# Get a list of all the groups
GROUP_LIST = CLIENT.systemgroup.list_all_groups(KEY)


def craft_inventory(group_dict):
    """Generate hosts and groups as defined in Spacewalk"""
    # Empty list to hold all members
    members = []
    # For each group found in the API call to Spacewalk,
    for group in group_dict:
        # List each system
        member_list = CLIENT.systemgroup.list_systems(KEY, group['name'])
        # For each system,
        for member in member_list:
            # Append the profile name (as this is the editable field in Spacewalk)
            members.append(member['profile_name'])
        # Add a new key with group name, and all it's members as the value
        DYNAMIC_INVENTORY[group['name']] = {'hosts': members, 'vars': {}}
        # Empty the list for the next group
        members = []
    # Also add the required _meta key, for holding hostvars
    DYNAMIC_INVENTORY['_meta'] = {'hostvars': {}}


def host_info():
    """Gather extra info provided by Spacewalk and use it for hostvars"""
    # Craft the inventory using the API call from Spacewalk
    craft_inventory(GROUP_LIST)
    # For each host,
    for host in HOST_LIST:
        # Get some variables
        id = host['id']
        name = host['name']
        # Get useful info from Spacewalk's API to be used as hostvars
        host_net_devices = CLIENT.system.get_network_devices(KEY, id)
        host_dmi = CLIENT.system.get_dmi(KEY, id)
        host_cpu = CLIENT.system.get_cpu(KEY, id)
        # Create a blank dictionary for each host, which will contain its vars
        DYNAMIC_INVENTORY['_meta']['hostvars'][name] = {}
        # Insert the info gathered from the API as hostvars
        DYNAMIC_INVENTORY['_meta']['hostvars'][name].update({'network': host_net_devices})
        DYNAMIC_INVENTORY['_meta']['hostvars'][name].update({'dmi': host_dmi})
        DYNAMIC_INVENTORY['_meta']['hostvars'][name].update({'cpu': host_cpu})


# Produce json for ansible-inventory
def ansible_list(ctx, param, value):
    """Print entire inventory in JSON"""
    if not value or ctx.resilient_parsing:
        return
    host_info()
    inventory = json.dumps(DYNAMIC_INVENTORY)
    click.echo(inventory)
    ctx.exit()


# Get specific host info
def ansible_host(ctx, param, value):
    """Print inventory for a specific host"""
    if not value or ctx.resilient_parsing:
        return
    host_info()
    inventory = json.dumps(DYNAMIC_INVENTORY['_meta']['hostvars'][value])
    click.echo(inventory)
    ctx.exit()


# Decorated groups for all subcommands
@click.group()
@click.version_option('1.0.0')
# Ansible expected options
@click.option('--list', is_flag=True, callback=ansible_list,
              expose_value=False, is_eager=True)
@click.option('--host', metavar='HOSTNAME', callback=ansible_host,
              expose_value=True)
def spacewalk_inventory():
    """A dynamic inventory script for Ansible that uses the Spacewalk API"""
    pass


if __name__ == '__main__':
    spacewalk_inventory()
    CLIENT.auth.logout(KEY)
