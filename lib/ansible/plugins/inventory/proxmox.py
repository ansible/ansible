# -*- coding: utf-8 -*-
# Copyright (C) 2016 Guido Günther <agx@sigxcpu.org>, Daniel Lobato Garcia <dlobatog@redhat.com>
# Copyright (c) 2018 Ansible Project
# Copyright (c) 2019 Jeffrey van Pelt <thulium@element-networks.nl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    name: proxmox
    plugin_type: inventory
    short_description: proxmox inventory source
    version_added: "2.7"
    requirements:
        - requests >= 1.1
    description:
        - Get inventory hosts from the proxmox service.
        - "Uses a configuration file as an inventory source, it must end in ``.proxmox.yml`` or ``.proxmox.yaml`` and has a ``plugin: proxmox`` entry."
        - Will retrieve the first network interface with an IP for Proxmox nodes
        - Can retrieve LXC/QEMU configuration as facts
    extends_documentation_fragment:
        - inventory_cache
    options:
      plugin:
        description: the name of this plugin, it should alwys be set to 'proxmox' for this plugin to recognize it as it's own.
        required: True
        choices: ['proxmox']
      url:
        description: url to proxmox
        default: 'http://localhost:8006'
      user:
        description: proxmox authentication user
        required: True
      password:
        description: proxmox authentication password
        required: True
      validate_certs:
        description: verify SSL certificate if using https
        type: boolean
        default: False
      group_prefix:
        description: prefix to apply to proxmox groups
        default: proxmox_
      facts_prefix:
        description: prefix to apply to vm config facts
        default: proxmox_
      want_facts:
        description: gather vm configuration facts
        default: False
'''

EXAMPLES = '''
# my.proxmox.yml
plugin: proxmox
url: http://localhost:8006
user: ansible-tester
password: secure
validate_certs: False
'''

import re

from collections import MutableMapping
from distutils.version import LooseVersion

from ansible.errors import AnsibleError
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable
from ansible.module_utils.six.moves.urllib.parse import urlencode


# 3rd party imports
try:
    import requests
    if LooseVersion(requests.__version__) < LooseVersion('1.1.0'):
        raise ImportError
except ImportError:
    raise AnsibleError('This script requires python-requests 1.1 as a minimum version')


class InventoryModule(BaseInventoryPlugin, Cacheable):
    ''' Host inventory parser for ansible using proxmox as source. '''

    NAME = 'proxmox'

    def __init__(self):

        super(InventoryModule, self).__init__()

        # from config
        self.proxmox_url = None

        self.session = None
        self.cache_key = None
        self.use_cache = None

    def verify_file(self, path):

        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(('proxmox.yaml', 'proxmox.yml')):
                valid = True
            else:
                self.display.vvv('Skipping due to inventory source not ending in "proxmox.yaml" nor "proxmox.yml"')
        return valid

    def _get_session(self):
        if not self.session:
            self.session = requests.session()
            self.session.verify = self.get_option('validate_certs')
        return self.session

    def _get_auth(self):
        credentials = urlencode({'username': self.proxmox_user, 'password': self.proxmox_password, })

        a = self._get_session()
        ret = a.post('%s/api2/json/access/ticket' % self.proxmox_url, data=credentials)

        json = ret.json()

        self.credentials = {
            'ticket': json['data']['ticket'],
            'CSRFPreventionToken': json['data']['CSRFPreventionToken'],
        }

    def _get_json(self, url, ignore_errors=None):

        if not self.use_cache or url not in self._cache.get(self.cache_key, {}):

            if self.cache_key not in self._cache:
                self._cache[self.cache_key] = {'url': ''}

            data = []
            s = self._get_session()
            while True:
                headers = {'Cookie': 'PVEAuthCookie={0}'.format(self.credentials['ticket'])}
                ret = s.get(url, headers=headers)
                if ignore_errors and ret.status_code in ignore_errors:
                    break
                ret.raise_for_status()
                json = ret.json()

                # process results
                # FIXME: This assumes 'return type' matches a specific query,
                #        it will break if we expand the queries and they dont have different types
                if 'data' not in json:
                    # /hosts/:id dos not have a 'data' key
                    data = json
                    break
                elif isinstance(json['data'], MutableMapping):
                    # /facts are returned as dict in 'data'
                    data = json['data']
                    break
                else:
                    # /hosts 's 'results' is a list of all hosts, returned is paginated
                    data = data + json['data']
                    break

            self._cache[self.cache_key][url] = data

        return self._cache[self.cache_key][url]

    def _get_nodes(self):
        return self._get_json("%s/api2/json/nodes" % self.proxmox_url)

    def _get_pools(self):
        return self._get_json("%s/api2/json/pools" % self.proxmox_url)

    def _get_lxc_per_node(self, node):
        return self._get_json("%s/api2/json/nodes/%s/lxc" % (self.proxmox_url, node))

    def _get_qemu_per_node(self, node):
        return self._get_json("%s/api2/json/nodes/%s/qemu" % (self.proxmox_url, node))

    def _get_members_per_pool(self, pool):
        ret = self._get_json("%s/api2/json/pools/%s" % (self.proxmox_url, pool))
        return ret['members']

    def _get_node_ip(self, node):
        ret = self._get_json("%s/api2/json/nodes/%s/network" % (self.proxmox_url, node))

        for iface in ret:
            try:
                return iface['address']
            except NameError:
                return None

    def _get_vm_config(self, node, vmid, vmtype, name):
        ret = self._get_json("%s/api2/json/nodes/%s/%s/%s/config" % (self.proxmox_url, node, vmtype, vmid))

        for config in ret:
            key = config
            key = self.to_safe('%s%s' % (self.get_option('facts_prefix'), key.lower()))
            value = ret[config]
            try:
                # fixup disk images as they have no key
                if config == 'rootfs' or config.startswith(('virtio', 'sata', 'ide', 'scsi')):
                    value = ('disk_image=' + value)

                if isinstance(value, int) or ',' not in value:
                    value = value
                # split off strings with commas to a dict
                else:
                    value = dict(key.split("=") for key in value.split(","))

                self.inventory.set_variable(name, key, value)
            except NameError:
                return None

    def to_safe(self, word):
        '''Converts 'bad' characters in a string to underscores so they can be used as Ansible groups
        #> ProxmoxInventory.to_safe("foo-bar baz")
        'foo_barbaz'
        '''
        regex = r"[^A-Za-z0-9\_]"
        return re.sub(regex, "_", word.replace(" ", ""))

    def _populate(self):

        self._get_auth()

        # gather vm's on nodes
        for node in self._get_nodes():
            # create groups
            group_prefix = self.get_option('group_prefix')
            lxc_group = self.to_safe('%s%s' % (group_prefix, 'all_lxc'))
            self.inventory.add_group(lxc_group)
            qemu_group = self.to_safe('%s%s' % (group_prefix, 'all_qemu'))
            self.inventory.add_group(qemu_group)
            nodes_group = self.to_safe('%s%s' % (group_prefix, 'nodes'))
            self.inventory.add_group(nodes_group)

            if node.get('node'):
                self.inventory.add_host(node['node'])

                if node['type'] == 'node':
                    self.inventory.add_child(nodes_group, node['node'])

                # get node IP address
                ip = self._get_node_ip(node['node'])
                self.inventory.set_variable(node['node'], 'ansible_host', ip)

                # get lxc containers for this node
                node_lxc_group = self.to_safe('%s%s' % (group_prefix, ('%s_lxc' % node['node']).lower()))
                self.inventory.add_group(node_lxc_group)
                for lxc in self._get_lxc_per_node(node['node']):
                    self.inventory.add_host(lxc['name'])
                    self.inventory.add_child(lxc_group, lxc['name'])
                    self.inventory.add_child(node_lxc_group, lxc['name'])

                    # get lxc config for facts
                    if self.get_option('want_facts'):
                        self._get_vm_config(node['node'], lxc['vmid'], 'lxc', lxc['name'])

                # get qemu vm's for this node
                node_qemu_group = self.to_safe('%s%s' % (group_prefix, ('%s_qemu' % node['node']).lower()))
                self.inventory.add_group(node_qemu_group)
                for qemu in self._get_qemu_per_node(node['node']):
                    self.inventory.add_host(qemu['name'])
                    self.inventory.add_child(qemu_group, qemu['name'])
                    self.inventory.add_child(node_qemu_group, qemu['name'])

                    # get qemu config for facts
                    if self.get_option('want_facts'):
                        self._get_vm_config(node['node'], qemu['vmid'], 'qemu', qemu['name'])

        # gather vm's in pools
        for pool in self._get_pools():
            if pool.get('poolid'):
                pool_group = 'pool_' + pool['poolid']
                pool_group = self.to_safe('%s%s' % (group_prefix, pool_group.lower()))
                self.inventory.add_group(pool_group)

                for member in self._get_members_per_pool(pool['poolid']):
                    if member.get('name'):
                        self.inventory.add_child(pool_group, member['name'])

    def parse(self, inventory, loader, path, cache=True):

        super(InventoryModule, self).parse(inventory, loader, path)

        # read config from file, this sets 'options'
        self._read_config_data(path)

        # get connection host
        self.proxmox_url = self.get_option('url')
        self.proxmox_user = self.get_option('user')
        self.proxmox_password = self.get_option('password')
        self.cache_key = self.get_cache_key(path)
        self.use_cache = cache and self.get_option('cache')

        # actually populate inventory
        self._populate()
