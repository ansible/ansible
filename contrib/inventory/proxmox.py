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

# Updated 2016 by Matt Harris <matthaeus.harris@gmail.com>
#
# Added support for Proxmox VE 4.x
# Added support for using the Notes field of a VM to define groups and variables:
# A well-formatted JSON object in the Notes field will be added to the _meta
# section for that VM.  In addition, the "groups" key of this JSON object may be
# used to specify group membership:
#
# { "groups": ["utility", "databases"], "a": false, "b": true }

import json
import os
import sys
from optparse import OptionParser

from ansible.module_utils.six import iteritems
from ansible.module_utils.six.moves.urllib.parse import urlencode

from ansible.module_utils.urls import open_url


class ProxmoxNodeList(list):
    def get_names(self):
        return [node['node'] for node in self]


class ProxmoxVM(dict):
    def get_variables(self):
        variables = {}
        for key, value in iteritems(self):
            variables['proxmox_' + key] = value
        return variables


class ProxmoxVMList(list):
    def __init__(self, data=None):
        data = [] if data is None else data

        for item in data:
            self.append(ProxmoxVM(item))

    def get_names(self):
        return [vm['name'] for vm in self if vm['template'] != 1]

    def get_by_name(self, name):
        results = [vm for vm in self if vm['name'] == name]
        return results[0] if len(results) > 0 else None

    def get_variables(self):
        variables = {}
        for vm in self:
            variables[vm['name']] = vm.get_variables()

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
        request_path = '{0}api2/json/access/ticket'.format(self.options.url)

        request_params = urlencode({
            'username': self.options.username,
            'password': self.options.password,
        })

        data = json.load(open_url(request_path, data=request_params))

        self.credentials = {
            'ticket': data['data']['ticket'],
            'CSRFPreventionToken': data['data']['CSRFPreventionToken'],
        }

    def get(self, url, data=None):
        request_path = '{0}{1}'.format(self.options.url, url)

        headers = {'Cookie': 'PVEAuthCookie={0}'.format(self.credentials['ticket'])}
        request = open_url(request_path, data=data, headers=headers)

        response = json.load(request)
        return response['data']

    def nodes(self):
        return ProxmoxNodeList(self.get('api2/json/nodes'))

    def vms_by_type(self, node, type):
        return ProxmoxVMList(self.get('api2/json/nodes/{0}/{1}'.format(node, type)))

    def vm_description_by_type(self, node, vm, type):
        return self.get('api2/json/nodes/{0}/{1}/{2}/config'.format(node, type, vm))

    def node_qemu(self, node):
        return self.vms_by_type(node, 'qemu')

    def node_qemu_description(self, node, vm):
        return self.vm_description_by_type(node, vm, 'qemu')

    def node_lxc(self, node):
        return self.vms_by_type(node, 'lxc')

    def node_lxc_description(self, node, vm):
        return self.vm_description_by_type(node, vm, 'lxc')

    def pools(self):
        return ProxmoxPoolList(self.get('api2/json/pools'))

    def pool(self, poolid):
        return ProxmoxPool(self.get('api2/json/pools/{0}'.format(poolid)))


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
        lxc_list = proxmox_api.node_lxc(node)
        results['all']['hosts'] += lxc_list.get_names()
        results['_meta']['hostvars'].update(lxc_list.get_variables())

        for vm in results['_meta']['hostvars']:
            vmid = results['_meta']['hostvars'][vm]['proxmox_vmid']
            try:
                type = results['_meta']['hostvars'][vm]['proxmox_type']
            except KeyError:
                type = 'qemu'
            try:
                description = proxmox_api.vm_description_by_type(node, vmid, type)['description']
            except KeyError:
                description = None

            try:
                metadata = json.loads(description)
            except TypeError:
                metadata = {}
            except ValueError:
                metadata = {
                    'notes': description
                }

            if 'groups' in metadata:
                # print metadata
                for group in metadata['groups']:
                    if group not in results:
                        results[group] = {
                            'hosts': []
                        }
                    results[group]['hosts'] += [vm]

            results['_meta']['hostvars'][vm].update(metadata)

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
