#!/usr/bin/env python

# (c) 2013, Greg Buehler
# (c) 2018, Filippo Ferrazini
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

"""
Zabbix Server external inventory script.
========================================

Returns hosts and hostgroups from Zabbix Server.
If you want to run with --limit against a host group with space in the
name, use asterisk. For example --limit="Linux*servers".

Configuration is read from `zabbix.ini`.

Tested with Zabbix Server 2.0.6, 3.2.3 and 3.4.
"""

from __future__ import print_function

import os
import sys
import argparse
from ansible.module_utils.six.moves import configparser

try:
    from zabbix_api import ZabbixAPI
except Exception:
    print("Error: Zabbix API library must be installed: pip install zabbix-api.",
          file=sys.stderr)
    sys.exit(1)

import json


class ZabbixInventory(object):

    def read_settings(self):
        config = configparser.SafeConfigParser()
        conf_path = './zabbix.ini'
        if not os.path.exists(conf_path):
            conf_path = os.path.dirname(os.path.realpath(__file__)) + '/zabbix.ini'
        if os.path.exists(conf_path):
            config.read(conf_path)
        # server
        if config.has_option('zabbix', 'server'):
            self.zabbix_server = config.get('zabbix', 'server')

        # login
        if config.has_option('zabbix', 'username'):
            self.zabbix_username = config.get('zabbix', 'username')
        if config.has_option('zabbix', 'password'):
            self.zabbix_password = config.get('zabbix', 'password')
        # ssl certs
        if config.has_option('zabbix', 'validate_certs'):
            if config.get('zabbix', 'validate_certs') in ['false', 'False', False]:
                self.validate_certs = False
        # host inventory
        if config.has_option('zabbix', 'read_host_inventory'):
            if config.get('zabbix', 'read_host_inventory') in ['true', 'True', True]:
                self.read_host_inventory = True
        # host interface
        if config.has_option('zabbix', 'use_host_interface'):
            if config.get('zabbix', 'use_host_interface') in ['false', 'False', False]:
                self.use_host_interface = False

    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host')
        parser.add_argument('--list', action='store_true')
        self.options = parser.parse_args()

    def hoststub(self):
        return {
            'hosts': []
        }

    def get_host(self, api, name):
        api_query = {'output': 'extend', 'selectGroups': 'extend', "filter": {"host": [name]}}
        if self.use_host_interface:
            api_query['selectInterfaces'] = ['useip', 'ip', 'dns']
        if self.read_host_inventory:
            api_query['selectInventory'] = "extend"

        data = {'ansible_ssh_host': name}
        if self.use_host_interface or self.read_host_inventory:
            try:
                hosts_data = api.host.get(api_query)[0]
                if 'interfaces' in hosts_data:
                    # use first interface only
                    if hosts_data['interfaces'][0]['useip'] == 0:
                        data['ansible_ssh_host'] = hosts_data['interfaces'][0]['dns']
                    else:
                        data['ansible_ssh_host'] = hosts_data['interfaces'][0]['ip']
                if ('inventory' in hosts_data) and (hosts_data['inventory']):
                    data.update(hosts_data['inventory'])
            except IndexError:
                # Host not found in zabbix
                pass
        return data

    def get_list(self, api):
        api_query = {'output': 'extend', 'selectGroups': 'extend'}
        if self.use_host_interface:
            api_query['selectInterfaces'] = ['useip', 'ip', 'dns']
        if self.read_host_inventory:
            api_query['selectInventory'] = "extend"

        hosts_data = api.host.get(api_query)
        data = {'_meta': {'hostvars': {}}}

        data[self.defaultgroup] = self.hoststub()
        for host in hosts_data:
            hostname = host['name']
            hostvars = dict()
            data[self.defaultgroup]['hosts'].append(hostname)

            for group in host['groups']:
                groupname = group['name']

                if groupname not in data:
                    data[groupname] = self.hoststub()

                data[groupname]['hosts'].append(hostname)
            if 'interfaces' in host:
                # use first interface only
                if host['interfaces'][0]['useip'] == 0:
                    hostvars['ansible_ssh_host'] = host['interfaces'][0]['dns']
                else:
                    hostvars['ansible_ssh_host'] = host['interfaces'][0]['ip']
            if ('inventory' in host) and (host['inventory']):
                hostvars.update(host['inventory'])
            data['_meta']['hostvars'][hostname] = hostvars

        return data

    def __init__(self):

        self.defaultgroup = 'group_all'
        self.zabbix_server = None
        self.zabbix_username = None
        self.zabbix_password = None
        self.validate_certs = True
        self.read_host_inventory = False
        self.use_host_interface = True

        self.meta = {}

        self.read_settings()
        self.read_cli()

        if self.zabbix_server and self.zabbix_username:
            try:
                api = ZabbixAPI(server=self.zabbix_server, validate_certs=self.validate_certs)
                api.login(user=self.zabbix_username, password=self.zabbix_password)
            # zabbix_api tries to exit if it cannot parse what the zabbix server returned
            # so we have to use SystemExit here
            except (Exception, SystemExit) as e:
                print("Error: Could not login to Zabbix server. Check your zabbix.ini.", file=sys.stderr)
                sys.exit(1)

            if self.options.host:
                data = self.get_host(api, self.options.host)
                print(json.dumps(data, indent=2))

            elif self.options.list:
                data = self.get_list(api)
                print(json.dumps(data, indent=2))

            else:
                print("usage: --list  ..OR.. --host <hostname>", file=sys.stderr)
                sys.exit(1)

        else:
            print("Error: Configuration of server and credentials are required. See zabbix.ini.", file=sys.stderr)
            sys.exit(1)


ZabbixInventory()
