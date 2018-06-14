#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This script uses the FreeIPA API to create an Ansible dynamic directory
# This is a shell script version of freeipa-api-inv.py
#
# DEPENDENCIES: before this script will work with AWX or Tower
# the python_freeipa module has to be installed
#
# Add this to your Docker image
# RUN pip install python_freeipa
#
# Set the following variables in Inventory Source:
# freeipaserver : the FQDN of the FreeIPA/RHIdM server
# freeipauser : an unprivileged user account for connecting to the API
# freeipapassword : password for freeipauser

from argparse import ArgumentParser
import json
import urllib3
from os import environ as env
from sys import exit
try:
    from python_freeipa import Client
except ImportError:
    print('The ipa dynamic inventory script requires python_freeipa.')

# We don't need warnings
urllib3.disable_warnings()

parser = ArgumentParser(description="AWX FreeIPA API dynamic host inventory")
parser.add_argument(
    '--list',
    default=False,
    dest="list",
    action="store_true",
    help="Produce a JSON consumable grouping of servers for Ansible"
)
parser.add_argument(
    '--host',
    default=None,
    dest="host",
    help="Generate additional host specific details for given host for Ansible"
)
parser.add_argument(
    '-u',
    '--user',
    default=None,
    dest="user",
    help="username to log into FreeIPA API"
)
parser.add_argument(
    '-w',
    '--password',
    default=None,
    dest="password",
    help="password to log into FreeIPA API"
)
parser.add_argument(
    '-s',
    '--server',
    default=None,
    dest="server",
    help="hostname of FreeIPA server"
)
parser.add_argument(
    '--ipa-version',
    default='2.228',
    dest="ipaversion",
    help="version of FreeIPA server"
)
args = parser.parse_args()

# Hard code varibles here if required
freeipaserver = None
freeipauser = None
freeipapassword = None

if 'freeipaserver' in env:
    freeipaserver = env['freeipaserver']

if 'freeipauser' in env:
    freeipauser = env['freeipauser']

if 'freeipapassword' in env:
    freeipapassword = env['freeipapassword']

if args.server:
    freeipaserver = args.server

if args.user:
    freeipauser = args.user

if args.password:
    freeipapassword = args.password

if not freeipaserver:
    exit("HALT: No FreeIPA server set")

if not freeipauser:
    exit("HALT: No FreeIPA user set")

if not freeipapassword:
    exit("HALT: No FreeIPA password set")

client = Client(
    freeipaserver,
    version='2.228',
    verify_ssl=False
)
client.login(
    freeipauser,
    freeipapassword
)

if args.host:
    # List host
    result = client._request(
        'host_show',
        args.host,
        {'all': True, 'raw': False}
    )['result']
    if 'usercertificate' in result:
        del result['usercertificate']
    print(json.dumps(result, indent=1))
elif args.list:
    inventory = {}
    hostvars = {}
    result = client._request(
        'hostgroup_find',
        '',
        {'all': True, 'raw': False}
    )['result']
    for hostgroup in result:
        members = []
        children = []

        if 'member_host' in hostgroup:
            members = [host for host in hostgroup['member_host']]
        if 'member_hostgroup' in hostgroup:
            children = hostgroup['member_hostgroup']
        inventory[hostgroup['cn'][0]] = {
            'hosts': [host for host in members],
            'children': children
        }

        for member in members:
            # This should actually grab the hostvars for the hosts
            result = client._request(
                'host_show',
                member,
                {'all': True, 'raw': False}
            )['result']
            if 'usercertificate' in result:
                del result['usercertificate']
            hostvars[member] = result

    inventory['_meta'] = {'hostvars': hostvars}
    inv_string = json.dumps(inventory, indent=1, sort_keys=True)
    print(inv_string)
else:
    print("%s:%s@%s" % (
        freeipauser,
        freeipapassword,
        freeipaserver
    ))
