#!/usr/bin/env python
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import json
from ipalib import api, errors
from six import u


def initialize():
    '''
    This function initializes the FreeIPA/IPA API. This function requires
    no arguments. A kerberos key must be present in the users keyring in
    order for this to work.
    '''

    api.bootstrap(context='cli')
    api.finalize()
    try:
        api.Backend.rpcclient.connect()
    except AttributeError:
        # FreeIPA < 4.0 compatibility
        api.Backend.xmlclient.connect()

    return api


def list_groups(api):
    '''
    This function prints a list of all host groups. This function requires
    one argument, the FreeIPA/IPA API object.
    '''

    inventory = {}
    hostvars = {}

    result = api.Command.hostgroup_find(all=True)['result']

    for hostgroup in result:
        # Get direct and indirect members (nested hostgroups) of hostgroup
        members = []

        if 'member_host' in hostgroup:
            members = [host for host in hostgroup['member_host']]
        if 'memberindirect_host' in hostgroup:
            members += (host for host in hostgroup['memberindirect_host'])
        inventory[hostgroup['cn'][0]] = {'hosts': [host for host in members]}

        for member in members:
            hostvars[member] = {}

    inventory['_meta'] = {'hostvars': hostvars}
    inv_string = json.dumps(inventory, indent=1, sort_keys=True)
    print(inv_string)

    return None


def parse_args():
    '''
    This function parses the arguments that were passed in via the command line.
    This function expects no arguments.
    '''

    parser = argparse.ArgumentParser(description='Ansible FreeIPA/IPA '
                                     'inventory module')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true',
                       help='List active servers')
    group.add_argument('--host', help='List details about the specified host')

    return parser.parse_args()


def get_host_attributes(api, host):
    """
    This function expects one string, this hostname to lookup variables for.
    Args:
        api: FreeIPA API Object
        host: Name of Hostname

    Returns: Dict of Host vars if found else None
    """
    try:
        result = api.Command.host_show(u(host))['result']
        if 'usercertificate' in result:
            del result['usercertificate']
        return json.dumps(result, indent=1)
    except errors.NotFound as e:
        return {}


if __name__ == '__main__':
    args = parse_args()
    api = initialize()

    if args.host:
        print(get_host_attributes(api, args.host))
    elif args.list:
        list_groups(api)
