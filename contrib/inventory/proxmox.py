#!/usr/bin/env python

# Copyright (C) 2014  Mathieu GAUTHIER-LAFAYE <gauthierl@lapth.cnrs.fr>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import urllib
try:
    import json
except ImportError:
    import simplejson as json
import os
import sys
from optparse import OptionParser

from six import iteritems

from ansible.module_utils.urls import open_url

class ProxmoxNodeList(list):
    def get_names(self):
        return [node['node'] for node in self]

class ProxmoxQemu(dict):
    def get_variables(self):
        variables = {}
        for key, value in iteritems(self):
            variables['proxmox_' + key] = value
        return variables

class ProxmoxQemuList(list):
    def __init__(self, data=[]):
        for item in data:
            self.append(ProxmoxQemu(item))

    def get_names(self):
        return [qemu['name'] for qemu in self if qemu['template'] != 1]

    def get_by_name(self, name):
        results = [qemu for qemu in self if qemu['name'] == name]
        return results[0] if len(results) > 0 else None

    def get_variables(self):
        variables = {}
        for qemu in self:
            variables[qemu['name']] = qemu.get_variables()

        return variables

class ProxmoxPoolList(list):
    def get_names(self):
        return [pool['poolid'] for pool in self]

class ProxmoxPool(dict):
    def get_members_name(self):
        return [member['name'] for member in self['members'] if member['template'] != 1]

class ProxmoxAPI(object):
    def __init__(self, options):
        self.options = options
        self.credentials = None

        if not options.url:
            raise Exception('Missing mandatory parameter --url (or PROXMOX_URL).')
        elif not options.username:
            raise Exception('Missing mandatory parameter --username (or PROXMOX_USERNAME).')
        elif not options.password:
            raise Exception('Missing mandatory parameter --password (or PROXMOX_PASSWORD).')

    def auth(self):
        request_path = '{}api2/json/access/ticket'.format(self.options.url)

        request_params = urllib.urlencode({
            'username': self.options.username,
            'password': self.options.password,
        })

        data = json.load(open_url(request_path, data=request_params))

        self.credentials = {
            'ticket': data['data']['ticket'],
            'CSRFPreventionToken': data['data']['CSRFPreventionToken'],
        }

    def get(self, url, data=None):
        request_path = '{}{}'.format(self.options.url, url)

        headers = {'Cookie': 'PVEAuthCookie={}'.format(self.credentials['ticket'])}
        request = open_url(request_path, data=data, headers=headers)

        response = json.load(request)
        return response['data']

    def nodes(self):
        return ProxmoxNodeList(self.get('api2/json/nodes'))

    def node_qemu(self, node):
        return ProxmoxQemuList(self.get('api2/json/nodes/{}/qemu'.format(node)))

    def pools(self):
        return ProxmoxPoolList(self.get('api2/json/pools'))

    def pool(self, poolid):
        return ProxmoxPool(self.get('api2/json/pools/{}'.format(poolid)))

def main_list(options):
    results = {
        'all': {
            'hosts': [],
        },
        '_meta': {
            'hostvars': {},
        }
    }

    proxmox_api = ProxmoxAPI(options)
    proxmox_api.auth()

    for node in proxmox_api.nodes().get_names():
        qemu_list = proxmox_api.node_qemu(node)
        results['all']['hosts'] += qemu_list.get_names()
        results['_meta']['hostvars'].update(qemu_list.get_variables())

    # pools
    for pool in proxmox_api.pools().get_names():
        results[pool] = {
            'hosts': proxmox_api.pool(pool).get_members_name(),
        }

    return results

def main_host(options):
    proxmox_api = ProxmoxAPI(options)
    proxmox_api.auth()

    for node in proxmox_api.nodes().get_names():
        qemu_list = proxmox_api.node_qemu(node)
        qemu = qemu_list.get_by_name(options.host)
        if qemu:
            return qemu.get_variables()

    return {}

def main():
    parser = OptionParser(usage='%prog [options] --list | --host HOSTNAME')
    parser.add_option('--list', action="store_true", default=False, dest="list")
    parser.add_option('--host', dest="host")
    parser.add_option('--url', default=os.environ.get('PROXMOX_URL'), dest='url')
    parser.add_option('--username', default=os.environ.get('PROXMOX_USERNAME'), dest='username')
    parser.add_option('--password', default=os.environ.get('PROXMOX_PASSWORD'), dest='password')
    parser.add_option('--pretty', action="store_true", default=False, dest='pretty')
    (options, args) = parser.parse_args()

    if options.list:
        data = main_list(options)
    elif options.host:
        data = main_host(options)
    else:
        parser.print_help()
        sys.exit(1)

    indent = None
    if options.pretty:
        indent = 2

    print(json.dumps(data, indent=indent))

if __name__ == '__main__':
    main()
