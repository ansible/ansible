#!/usr/bin/env python

# (c) 2015, Marc Abramowitz <marca@surveymonkey.com>
#
# This file is part of Ansible.
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Dynamic inventory script which lets you use nodes discovered by Serf
# (https://serfdom.io/).
#
# Requires the `serfclient` Python module from
# https://pypi.org/project/serfclient/
#
# Environment variables
# ---------------------
#   - `SERF_RPC_ADDR`
#   - `SERF_RPC_AUTH`
#
# These variables are described at https://www.serfdom.io/docs/commands/members.html#_rpc_addr

import argparse
import collections
import os
import sys

# https://pypi.org/project/serfclient/
from serfclient import SerfClient, EnvironmentConfig

import json

_key = 'serf'


def _serf_client():
    env = EnvironmentConfig()
    return SerfClient(host=env.host, port=env.port, rpc_auth=env.auth_key)


def get_serf_members_data():
    return _serf_client().members().body['Members']


def get_nodes(data):
    return [node['Name'] for node in data]


def get_groups(data):
    groups = collections.defaultdict(list)

    for node in data:
        for key, value in node['Tags'].items():
            groups[value].append(node['Name'])

    return groups


def get_meta(data):
    meta = {'hostvars': {}}
    for node in data:
        meta['hostvars'][node['Name']] = node['Tags']
    return meta


def print_list():
    data = get_serf_members_data()
    nodes = get_nodes(data)
    groups = get_groups(data)
    meta = get_meta(data)
    inventory_data = {_key: nodes, '_meta': meta}
    inventory_data.update(groups)
    print(json.dumps(inventory_data))


def print_host(host):
    data = get_serf_members_data()
    meta = get_meta(data)
    print(json.dumps(meta['hostvars'][host]))


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='ansible inventory script reading from serf cluster')
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    help_list = 'list all hosts from serf cluster'
    mutex_group.add_argument('--list', action='store_true', help=help_list)
    help_host = 'display variables for a host'
    mutex_group.add_argument('--host', help=help_host)
    return parser.parse_args(args_list)


def main(args_list):
    args = get_args(args_list)
    if args.list:
        print_list()
    if args.host:
        print_host(args.host)


if __name__ == '__main__':
    main(sys.argv[1:])
