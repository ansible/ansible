#!/usr/bin/env python

'''
Nodepool external inventory script
==================================

Generates an inventory that Ansible can understand by making Zookeeper calls
to the Nodepool service using the kazoo library.
Zookeeper IP and port are read from environment variables NODEPOOL_ZK_IP and
NODEPOOL_ZK_PORT respectively. If those variables are not set, the script checks if
/etc/nodepool/nodepool.yaml exists and reads values from there, otherwise it defaults
to 127.0.0.1 for the address and 2181 for the port.
Example:

  #!/bin/bash
  export NODEPOOL_ZK_IP=10.10.10.10
  export NODEPOOL_ZK_PORT=9000

  nodepool.py --list

The above script would try to connect to 10.10.10.10:9000 for gathering Nodepool data.

When run against a specific host, this script returns the following variables:

  {
    "ansible_connection": "ssh",
    "ansible_host": "38.145.35.76",
    "ansible_port": 22,
    "ansible_user": ubuntu,
    "nodepool_label": "ubuntu-xenial"
  }



# (c) 2018, Ricardo Carrillo Cruz
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

######################################################################
'''

import argparse
import os
import sys
import yaml

try:
    import json
except:
    import simplejson as json

HAS_KAZOO = False
try:
    import kazoo.client
    HAS_KAZOO = True
except ImportError:
    pass


class NodepoolInventory(object):

    def __init__(self):
        self.args = self.parse_cli_args()
        self.initialize_zk()

        if self.args.host:
            data = self.get_host_info()
        elif self.args.list:
            data = self.get_list()

        print(json.dumps(data, sort_keys=True, indent=2))
        self.zk.stop()

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Nodepool Inventory Plugin')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--list', action='store_true', help='List all available hosts')
        group.add_argument('--host', help='Show details about a specific host')

        return parser.parse_args()

    def initialize_zk(self):
        if 'NODEPOOL_ZK_IP' in os.environ:
            zk_address = os.environ['NODEPOOL_ZK_IP']
            zk_port = os.environ.get('NODEPOOL_ZK_PORT', '2181')
        elif os.path.isfile('/etc/nodepool/nodepool.yaml'):
            with open('/etc/nodepool/nodepool.yaml') as f:
                try:
                    y = yaml.load(f)
                    zk = y['zookeeper-servers'][0]
                    zk_address = zk['host']
                    zk_port = zk.get('port', 2181)
                except:
                    sys.exit("Unable to parse /etc/nodepool/nodepool.yaml as valid YAML file")
        else:
            zk_address = '127.0.0.1'
            zk_port = '2181'

        self.zk = kazoo.client.KazooClient(hosts='{0}:{1}'.format(zk_address, zk_port))
        try:
            self.zk.start()
        except:
            self.zk.stop()
            sys.exit("Unable to connect to Zookeeper on {0}:{1}".format(zk_address, zk_port))

    def get_list(self):
        data = {'all': {'hosts': []}, '_meta': {'hostvars': {}}}

        for n in self.zk.get_children('/nodepool/nodes'):
            node = json.loads(self.zk.get('/nodepool/nodes/' + n)[0])
            label = node['type']
            state = node['state']
            provider = node['provider']
            image = node['image_id']
            data['_meta']['hostvars'][n] = {
                'ansible_host': node['interface_ip'],
                'ansible_port': node['connection_port'],
                'ansible_connection': node['connection_type'],
                'ansible_user': node['username'],
                'nodepool_label': label,
                'nodepool_state': state,
                'nodepool_provider': provider,
                'nodepool_image': image,
            }
            data['all']['hosts'].append(n)

            if 'nodepool_label_{0}'.format(label) not in data.keys():
                data['nodepool_label_{0}'.format(label)] = {'hosts': []}
            data['nodepool_label_{0}'.format(label)]['hosts'].append(n)

            if 'nodepool_state_{0}'.format(state) not in data.keys():
                data['nodepool_state_{0}'.format(state)] = {'hosts': []}
            data['nodepool_state_{0}'.format(state)]['hosts'].append(n)

            if 'nodepool_provider_{0}'.format(provider) not in data.keys():
                data['nodepool_provider_{0}'.format(provider)] = {'hosts': []}
            data['nodepool_provider_{0}'.format(provider)]['hosts'].append(n)

            if 'nodepool_image_{0}'.format(image) not in data.keys():
                data['nodepool_image_{0}'.format(image)] = {'hosts': []}
            data['nodepool_image_{0}'.format(image)]['hosts'].append(n)

        return data

    def get_host_info(self):
        data = {}

        for n in self.zk.get_children('/nodepool/nodes'):
            node = json.loads(self.zk.get('/nodepool/nodes/' + n)[0])

            if n == self.args.host:
                data['ansible_host'] = node['interface_ip']
                data['ansible_port'] = node['connection_port']
                data['ansible_connection'] = node['connection_type']
                data['ansible_user'] = node['username']
                data['nodepool_label'] = node['type']
                data['nodepool_image'] = node['image_id']
                data['nodepool_provider'] = node['provider']
        return data


def main():
    if not HAS_KAZOO:
        sys.exit("The kazoo python library is not installed (try `pip install kazoo --user`)")

    NodepoolInventory()

if __name__ == '__main__':
    main()
