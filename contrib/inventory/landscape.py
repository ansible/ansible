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

# Dynamic inventory script which lets you use nodes discovered by Canonical's
# Landscape (http://www.ubuntu.com/management/landscape-features).
#
# Requires the `landscape_api` Python module
# See:
#   - https://landscape.canonical.com/static/doc/api/api-client-package.html
#   - https://landscape.canonical.com/static/doc/api/python-api.html
#
# Environment variables
# ---------------------
#   - `LANDSCAPE_API_URI`
#   - `LANDSCAPE_API_KEY`
#   - `LANDSCAPE_API_SECRET`
#   - `LANDSCAPE_API_SSL_CA_FILE` (optional)


import argparse
import collections
import os
import sys

from landscape_api.base import API, HTTPError

import json

_key = 'landscape'


class EnvironmentConfig(object):
    uri = os.getenv('LANDSCAPE_API_URI')
    access_key = os.getenv('LANDSCAPE_API_KEY')
    secret_key = os.getenv('LANDSCAPE_API_SECRET')
    ssl_ca_file = os.getenv('LANDSCAPE_API_SSL_CA_FILE')


def _landscape_client():
    env = EnvironmentConfig()
    return API(
        uri=env.uri,
        access_key=env.access_key,
        secret_key=env.secret_key,
        ssl_ca_file=env.ssl_ca_file)


def get_landscape_members_data():
    return _landscape_client().get_computers()


def get_nodes(data):
    return [node['hostname'] for node in data]


def get_groups(data):
    groups = collections.defaultdict(list)

    for node in data:
        for value in node['tags']:
            groups[value].append(node['hostname'])

    return groups


def get_meta(data):
    meta = {'hostvars': {}}
    for node in data:
        meta['hostvars'][node['hostname']] = {'tags': node['tags']}
    return meta


def print_list():
    data = get_landscape_members_data()
    nodes = get_nodes(data)
    groups = get_groups(data)
    meta = get_meta(data)
    inventory_data = {_key: nodes, '_meta': meta}
    inventory_data.update(groups)
    print(json.dumps(inventory_data))


def print_host(host):
    data = get_landscape_members_data()
    meta = get_meta(data)
    print(json.dumps(meta['hostvars'][host]))


def get_args(args_list):
    parser = argparse.ArgumentParser(
        description='ansible inventory script reading from landscape cluster')
    mutex_group = parser.add_mutually_exclusive_group(required=True)
    help_list = 'list all hosts from landscape cluster'
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
