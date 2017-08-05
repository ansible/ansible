#!/usr/bin/env python
#
# (c) 2017 Apstra Inc, <community@apstra.com>
#
# This file is part of Ansible
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
"""
Apstra AOS external inventory script
====================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this:
 - copy this file over /etc/ansible/hosts and chmod +x the file.
 - Copy both files (.py and .ini) in your preferred directory

More information about Ansible Dynamic Inventory here
http://unix.stackexchange.com/questions/205479/in-ansible-dynamic-inventory-json-can-i-render-hostvars-based-on-the-hostname

2 modes are currently, supported: **device based** or **blueprint based**:
  - For **Device based**, the list of device is taken from the global device list
    the serial ID will be used as the inventory_hostname
  - For **Blueprint based**, the list of device is taken from the given blueprint
    the Node name will be used as the inventory_hostname

Input parameters parameter can be provided using either with the ini file or by using Environment Variables:
The following list of Environment Variables are supported: AOS_SERVER, AOS_PORT, AOS_USERNAME, AOS_PASSWORD, AOS_BLUEPRINT
The config file takes precedence over the Environment Variables

Tested with Apstra AOS 1.1

This script has been inspired by the cobbler.py inventory. thanks

Author: Damien Garros (@dgarros)
Version: 0.2.0
"""
import json
import os
import re
import sys

try:
    import argparse
    HAS_ARGPARSE = True
except ImportError:
    HAS_ARGPARSE = False

try:
    from apstra.aosom.session import Session
    HAS_AOS_PYEZ = True
except ImportError:
    HAS_AOS_PYEZ = False

from ansible.module_utils.six.moves import configparser


"""
##
Expected output format in Device mode
{
  "Cumulus": {
    "hosts": [
      "52540073956E",
      "52540022211A"
    ],
    "vars": {}
  },
  "EOS": {
    "hosts": [
      "5254001CAFD8",
      "525400DDDF72"
    ],
    "vars": {}
  },
  "Generic Model": {
    "hosts": [
      "525400E5486D"
    ],
    "vars": {}
  },
  "Ubuntu GNU/Linux": {
    "hosts": [
      "525400E5486D"
    ],
    "vars": {}
  },
  "VX": {
    "hosts": [
      "52540073956E",
      "52540022211A"
    ],
    "vars": {}
  },
  "_meta": {
    "hostvars": {
      "5254001CAFD8": {
        "agent_start_time": "2017-02-03T00:49:16.000000Z",
        "ansible_ssh_host": "172.20.52.6",
        "aos_hcl_model": "Arista_vEOS",
        "aos_server": "",
        "aos_version": "AOS_1.1.1_OB.5",
        "comm_state": "on",
        "device_start_time": "2017-02-03T00:47:58.454480Z",
        "domain_name": "",
        "error_message": "",
        "fqdn": "localhost",
        "hostname": "localhost",
        "hw_model": "vEOS",
        "hw_version": "",
        "is_acknowledged": false,
        "mgmt_ifname": "Management1",
        "mgmt_ipaddr": "172.20.52.6",
        "mgmt_macaddr": "52:54:00:1C:AF:D8",
        "os_arch": "x86_64",
        "os_family": "EOS",
        "os_version": "4.16.6M",
        "os_version_info": {
          "build": "6M",
          "major": "4",
          "minor": "16"
        },
        "serial_number": "5254001CAFD8",
        "state": "OOS-QUARANTINED",
        "vendor": "Arista"
      },
      "52540022211A": {
        "agent_start_time": "2017-02-03T00:45:22.000000Z",
        "ansible_ssh_host": "172.20.52.7",
        "aos_hcl_model": "Cumulus_VX",
        "aos_server": "172.20.52.3",
        "aos_version": "AOS_1.1.1_OB.5",
        "comm_state": "on",
        "device_start_time": "2017-02-03T00:45:11.019189Z",
        "domain_name": "",
        "error_message": "",
        "fqdn": "cumulus",
        "hostname": "cumulus",
        "hw_model": "VX",
        "hw_version": "",
        "is_acknowledged": false,
        "mgmt_ifname": "eth0",
        "mgmt_ipaddr": "172.20.52.7",
        "mgmt_macaddr": "52:54:00:22:21:1a",
        "os_arch": "x86_64",
        "os_family": "Cumulus",
        "os_version": "3.1.1",
        "os_version_info": {
          "build": "1",
          "major": "3",
          "minor": "1"
        },
        "serial_number": "52540022211A",
        "state": "OOS-QUARANTINED",
        "vendor": "Cumulus"
      },
      "52540073956E": {
        "agent_start_time": "2017-02-03T00:45:19.000000Z",
        "ansible_ssh_host": "172.20.52.8",
        "aos_hcl_model": "Cumulus_VX",
        "aos_server": "172.20.52.3",
        "aos_version": "AOS_1.1.1_OB.5",
        "comm_state": "on",
        "device_start_time": "2017-02-03T00:45:11.030113Z",
        "domain_name": "",
        "error_message": "",
        "fqdn": "cumulus",
        "hostname": "cumulus",
        "hw_model": "VX",
        "hw_version": "",
        "is_acknowledged": false,
        "mgmt_ifname": "eth0",
        "mgmt_ipaddr": "172.20.52.8",
        "mgmt_macaddr": "52:54:00:73:95:6e",
        "os_arch": "x86_64",
        "os_family": "Cumulus",
        "os_version": "3.1.1",
        "os_version_info": {
          "build": "1",
          "major": "3",
          "minor": "1"
        },
        "serial_number": "52540073956E",
        "state": "OOS-QUARANTINED",
        "vendor": "Cumulus"
      },
      "525400DDDF72": {
        "agent_start_time": "2017-02-03T00:49:07.000000Z",
        "ansible_ssh_host": "172.20.52.5",
        "aos_hcl_model": "Arista_vEOS",
        "aos_server": "",
        "aos_version": "AOS_1.1.1_OB.5",
        "comm_state": "on",
        "device_start_time": "2017-02-03T00:47:46.929921Z",
        "domain_name": "",
        "error_message": "",
        "fqdn": "localhost",
        "hostname": "localhost",
        "hw_model": "vEOS",
        "hw_version": "",
        "is_acknowledged": false,
        "mgmt_ifname": "Management1",
        "mgmt_ipaddr": "172.20.52.5",
        "mgmt_macaddr": "52:54:00:DD:DF:72",
        "os_arch": "x86_64",
        "os_family": "EOS",
        "os_version": "4.16.6M",
        "os_version_info": {
          "build": "6M",
          "major": "4",
          "minor": "16"
        },
        "serial_number": "525400DDDF72",
        "state": "OOS-QUARANTINED",
        "vendor": "Arista"
      },
      "525400E5486D": {
        "agent_start_time": "2017-02-02T18:44:42.000000Z",
        "ansible_ssh_host": "172.20.52.4",
        "aos_hcl_model": "Generic_Server_1RU_1x10G",
        "aos_server": "172.20.52.3",
        "aos_version": "AOS_1.1.1_OB.5",
        "comm_state": "on",
        "device_start_time": "2017-02-02T21:11:25.188734Z",
        "domain_name": "",
        "error_message": "",
        "fqdn": "localhost",
        "hostname": "localhost",
        "hw_model": "Generic Model",
        "hw_version": "pc-i440fx-trusty",
        "is_acknowledged": false,
        "mgmt_ifname": "eth0",
        "mgmt_ipaddr": "172.20.52.4",
        "mgmt_macaddr": "52:54:00:e5:48:6d",
        "os_arch": "x86_64",
        "os_family": "Ubuntu GNU/Linux",
        "os_version": "14.04 LTS",
        "os_version_info": {
          "build": "",
          "major": "14",
          "minor": "04"
        },
        "serial_number": "525400E5486D",
        "state": "OOS-QUARANTINED",
        "vendor": "Generic Manufacturer"
      }
    }
  },
  "all": {
    "hosts": [
      "5254001CAFD8",
      "52540073956E",
      "525400DDDF72",
      "525400E5486D",
      "52540022211A"
    ],
    "vars": {}
  },
  "vEOS": {
    "hosts": [
      "5254001CAFD8",
      "525400DDDF72"
    ],
    "vars": {}
  }
}
"""


def fail(msg):
    sys.stderr.write("%s\n" % msg)
    sys.exit(1)


class AosInventory(object):

    def __init__(self):

        """ Main execution path """

        if not HAS_AOS_PYEZ:
            raise Exception('aos-pyez is not installed.  Please see details here: https://github.com/Apstra/aos-pyez')
        if not HAS_ARGPARSE:
            raise Exception('argparse is not installed.  Please install the argparse library or upgrade to python-2.7')

        # Initialize inventory
        self.inventory = dict()  # A list of groups and the hosts in that group
        self.inventory['_meta'] = dict()
        self.inventory['_meta']['hostvars'] = dict()

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # ----------------------------------------------------
        # Open session to AOS
        # ----------------------------------------------------
        aos = Session(server=self.aos_server,
                      port=self.aos_server_port,
                      user=self.aos_username,
                      passwd=self.aos_password)

        aos.login()

        # Save session information in variables of group all
        self.add_var_to_group('all', 'aos_session', aos.session)

        # Add the AOS server itself in the inventory
        self.add_host_to_group("all", 'aos')
        self.add_var_to_host("aos", "ansible_ssh_host", self.aos_server)
        self.add_var_to_host("aos", "ansible_ssh_pass", self.aos_password)
        self.add_var_to_host("aos", "ansible_ssh_user", self.aos_username)

        # ----------------------------------------------------
        # Build the inventory
        #  2 modes are supported: device based or blueprint based
        #  - For device based, the list of device is taken from the global device list
        #    the serial ID will be used as the inventory_hostname
        #  - For Blueprint based, the list of device is taken from the given blueprint
        #    the Node name will be used as the inventory_hostname
        # ----------------------------------------------------
        if self.aos_blueprint:

            bp = aos.Blueprints[self.aos_blueprint]
            if bp.exists is False:
                fail("Unable to find the Blueprint: %s" % self.aos_blueprint)

            for dev_name, dev_id in bp.params['devices'].value.items():

                self.add_host_to_group('all', dev_name)
                device = aos.Devices.find(uid=dev_id)

                if 'facts' in device.value.keys():
                    self.add_device_facts_to_var(dev_name, device)

                # Define admin State and Status
                if 'user_config' in device.value.keys():
                    if 'admin_state' in device.value['user_config'].keys():
                        self.add_var_to_host(dev_name, 'admin_state', device.value['user_config']['admin_state'])

                self.add_device_status_to_var(dev_name, device)

                # Go over the contents data structure
                for node in bp.contents['system']['nodes']:
                    if node['display_name'] == dev_name:
                        self.add_host_to_group(node['role'], dev_name)

                        # Check for additional attribute to import
                        attributes_to_import = [
                            'loopback_ip',
                            'asn',
                            'role',
                            'position',
                        ]
                        for attr in attributes_to_import:
                            if attr in node.keys():
                                self.add_var_to_host(dev_name, attr, node[attr])

                # if blueprint_interface is enabled in the configuration
                #   Collect links information
                if self.aos_blueprint_int:
                    interfaces = dict()

                    for link in bp.contents['system']['links']:
                        # each link has 2 sides [0,1], and it's unknown which one match this device
                        #  at first we assume, first side match(0) and peer is (1)
                        peer_id = 1

                        for side in link['endpoints']:
                            if side['display_name'] == dev_name:

                                # import local information first
                                int_name = side['interface']

                                # init dict
                                interfaces[int_name] = dict()
                                if 'ip' in side.keys():
                                    interfaces[int_name]['ip'] = side['ip']

                                if 'interface' in side.keys():
                                    interfaces[int_name]['name'] = side['interface']

                                if 'display_name' in link['endpoints'][peer_id].keys():
                                    interfaces[int_name]['peer'] = link['endpoints'][peer_id]['display_name']

                                if 'ip' in link['endpoints'][peer_id].keys():
                                    interfaces[int_name]['peer_ip'] = link['endpoints'][peer_id]['ip']

                                if 'type' in link['endpoints'][peer_id].keys():
                                    interfaces[int_name]['peer_type'] = link['endpoints'][peer_id]['type']

                            else:
                                # if we haven't match the first time, prepare the peer_id
                                # for the second loop iteration
                                peer_id = 0

                    self.add_var_to_host(dev_name, 'interfaces', interfaces)

        else:
            for device in aos.Devices:
                # If not reacheable, create by key and
                # If reacheable, create by hostname

                self.add_host_to_group('all', device.name)

                # populate information for this host
                self.add_device_status_to_var(device.name, device)

                if 'user_config' in device.value.keys():
                    for key, value in device.value['user_config'].items():
                        self.add_var_to_host(device.name, key, value)

                # Based on device status online|offline, collect facts as well
                if device.value['status']['comm_state'] == 'on':

                    if 'facts' in device.value.keys():
                        self.add_device_facts_to_var(device.name, device)

                # Check if device is associated with a blueprint
                #  if it's create a new group
                if 'blueprint_active' in device.value['status'].keys():
                    if 'blueprint_id' in device.value['status'].keys():
                        bp = aos.Blueprints.find(uid=device.value['status']['blueprint_id'])

                        if bp:
                            self.add_host_to_group(bp.name, device.name)

        # ----------------------------------------------------
        # Convert the inventory and return a JSON String
        # ----------------------------------------------------
        data_to_print = ""
        data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def read_settings(self):
        """ Reads the settings from the apstra_aos.ini file """

        config = configparser.ConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/apstra_aos.ini')

        # Default Values
        self.aos_blueprint = False
        self.aos_blueprint_int = True
        self.aos_username = 'admin'
        self.aos_password = 'admin'
        self.aos_server_port = 8888

        # Try to reach all parameters from File, if not available try from ENV
        try:
            self.aos_server = config.get('aos', 'aos_server')
        except:
            if 'AOS_SERVER' in os.environ.keys():
                self.aos_server = os.environ['AOS_SERVER']
            pass

        try:
            self.aos_server_port = config.get('aos', 'port')
        except:
            if 'AOS_PORT' in os.environ.keys():
                self.aos_server_port = os.environ['AOS_PORT']
            pass

        try:
            self.aos_username = config.get('aos', 'username')
        except:
            if 'AOS_USERNAME' in os.environ.keys():
                self.aos_username = os.environ['AOS_USERNAME']
            pass

        try:
            self.aos_password = config.get('aos', 'password')
        except:
            if 'AOS_PASSWORD' in os.environ.keys():
                self.aos_password = os.environ['AOS_PASSWORD']
            pass

        try:
            self.aos_blueprint = config.get('aos', 'blueprint')
        except:
            if 'AOS_BLUEPRINT' in os.environ.keys():
                self.aos_blueprint = os.environ['AOS_BLUEPRINT']
            pass

        try:
            if config.get('aos', 'blueprint_interface') in ['false', 'no']:
                self.aos_blueprint_int = False
        except:
            pass

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Apstra AOS')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def add_host_to_group(self, group, host):

        # Cleanup group name first
        clean_group = self.cleanup_group_name(group)

        # Check if the group exist, if not initialize it
        if clean_group not in self.inventory.keys():
            self.inventory[clean_group] = {}
            self.inventory[clean_group]['hosts'] = []
            self.inventory[clean_group]['vars'] = {}

        self.inventory[clean_group]['hosts'].append(host)

    def add_var_to_host(self, host, var, value):

        # Check if the host exist, if not initialize it
        if host not in self.inventory['_meta']['hostvars'].keys():
            self.inventory['_meta']['hostvars'][host] = {}

        self.inventory['_meta']['hostvars'][host][var] = value

    def add_var_to_group(self, group, var, value):

        # Cleanup group name first
        clean_group = self.cleanup_group_name(group)

        # Check if the group exist, if not initialize it
        if clean_group not in self.inventory.keys():
            self.inventory[clean_group] = {}
            self.inventory[clean_group]['hosts'] = []
            self.inventory[clean_group]['vars'] = {}

        self.inventory[clean_group]['vars'][var] = value

    def add_device_facts_to_var(self, device_name, device):

        # Populate variables for this host
        self.add_var_to_host(device_name,
                             'ansible_ssh_host',
                             device.value['facts']['mgmt_ipaddr'])

        self.add_var_to_host(device_name, 'id', device.id)

        # self.add_host_to_group('all', device.name)
        for key, value in device.value['facts'].items():
            self.add_var_to_host(device_name, key, value)

            if key == 'os_family':
                self.add_host_to_group(value, device_name)
            elif key == 'hw_model':
                self.add_host_to_group(value, device_name)

    def cleanup_group_name(self, group_name):
        """
        Clean up group name by :
          - Replacing all non-alphanumeric caracter by underscore
          - Converting to lowercase
        """

        rx = re.compile('\W+')
        clean_group = rx.sub('_', group_name).lower()

        return clean_group

    def add_device_status_to_var(self, device_name, device):

        if 'status' in device.value.keys():
            for key, value in device.value['status'].items():
                self.add_var_to_host(device.name, key, value)

# Run the script
if __name__ == '__main__':
    AosInventory()
