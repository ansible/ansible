#!/usr/bin/env python

# (c) 2017, Lutz Reinhardt <l.reinhardt@posteo.de>
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

"""
Icinga1 inventory script.
========================================
Returns hosts and hostgroups from Icinga1 REST API.
Configuration is read from icinga1.ini.
"""

import os
import argparse

try:
    import configparser
except ImportError:
    import ConfigParser

    configparser = ConfigParser

import json
import requests


def read_settings():
    config = configparser.SafeConfigParser()
    config.read(os.path.dirname(os.path.realpath(__file__)) + '/icinga1.ini')
    return config.items('settings')


def read_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--host', nargs=1)
    group.add_argument('--list', action='store_true')
    return parser.parse_args()


def get_data(url):
    response = {}
    try:
        r = requests.get(url)
        response = r.json()
    except:
        print("ERROR: request '%s' FAILED!" % url)
        exit(2)

    if 'result' not in response or 'success' not in response or response['success'] != 'true':
        print("ERROR: response error!")
        exit(3)

    return response


def read_hosts(url, authkey):
    group_url = url + '/web/api/hostgroup/columns[HOSTGROUP_NAME|HOST_NAME]/authkey=%s/json' % authkey
    response = get_data(group_url)

    groups_found = {}
    hosts_found = {}

    for item in response['result']:
        group = item['HOSTGROUP_NAME']
        host = item['HOST_NAME']

        groups_found.setdefault(group, {}).setdefault('hosts', []).append(host)
        hosts_found[host] = ""

    host_url = url + '/web/api/host/columns[HOST_NAME|HOST_ADDRESS]/authkey=%s/json' % authkey
    response = get_data(host_url)

    for item in response['result']:
        hosts_found[item['HOST_NAME']] = item['HOST_ADDRESS']

    return {'groups': groups_found, 'hosts': hosts_found}


def main():
    settings = {}
    for i in read_settings():
        settings[i[0]] = i[1]
    options = read_args()

    if options.host:
        print(json.dumps({}))
        exit()

    if 'url' not in settings or 'authkey' not in settings:
        print("ERROR: url and authkey is required in config file!")
        exit(-1)

    hosts = read_hosts(**settings)

    result = hosts['groups']
    result['_meta'] = {'hostvars': {}}

    for host, ip in iter(hosts['hosts'].items()):
        result['_meta']['hostvars'][host] = {'ansible_host': ip}

    print(json.dumps(result))


if __name__ == "__main__":
    # execute only if run as a script
    main()
