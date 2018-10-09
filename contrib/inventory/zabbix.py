#!/usr/bin/env python

# (c) 2013, Greg Buehler
# Updates 2017-2018 by tony@nieuwenborg.nl
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

Metadata:
- ansible_host: IP found in host info, or macro {$ANSIBLE_HOST} if set.
- ansible_port: macro {$ANSIBLE_PORT} if set, otherwise 22
- ansible_enabled: macro {$ANSIBLE_ENABLED}, defaults to '1'
- user defined vars: macro {$ANSIBLE_VARS} takes json like:
  { "foo":"bar", "num":2 }
- templates: list of templates used by host

Notes:
- disabled hosts are skipped.
- group_all is the group containing all hosts

Configuration is read from `zabbix.ini`.

Tested with Zabbix Server 2.0.6 and 3.2.9.
"""

from __future__ import print_function

import os
import sys
import argparse
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from zabbix_api import ZabbixAPI
except:
    print("Error: Zabbix API library must be installed.",
          file=sys.stderr)
    sys.exit(1)

try:
    import json
except:
    import simplejson as json


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
        #data = {}
        data = api.host.get({"filter": {'name': name}})
        return data

    def get_list(self, api):
        hostsData = api.host.get({'output': 'extend',
                                  'selectGroups': 'extend',
                                  'selectInterfaces': 'extend',
                                  'selectMacros': 'extend',
                                  'selectParentTemplates': 'extend'})

        data = {}
        data[self.defaultgroup] = self.hoststub()
        data['_meta'] = {'hostvars': self.meta}

        for host in hostsData:
            if host['status'] != "0":
                continue
            hostname = host['name']
            ip = host['interfaces'][0]['ip']
            port = 22
            enabled = '1'

            #data[self.defaultgroup]['hosts'].append(hostname)
            zabbixvars = ''
            for m in host['macros']:
                if m['macro'] == '{$ANSIBLE_PORT}':
                    port = m['value']
                elif m['macro'] == '{$ANSIBLE_HOST}':
                    ip = m['value']
                elif m['macro'] == '{$ANSIBLE_ENABLED}':
                    enabled = m['value']
                elif m['macro'] == '{$ANSIBLE_VARS}':
                    zv = m['value']
                    try:
                        zabbixvars = json.loads(zv)
                    except:
                        print("Invalid JSON in "
                              + hostname + ":"
                              + "{$ANSIBLE_VARS}: " + zv)
                        sys.exit(1)
            if '0' == enabled:
                print("host " + hostname + " has enabled flag set to 0", file=sys.stderr)
                continue
            data[self.defaultgroup]['hosts'].append(hostname)
#            if '0' == enabled:
            #    print("Ansible has been disabled for host " 
            #        + hostname)
        #        sys.exit(1)
            #    return {}
                
            # TODO maybe only add when actually (re)defined?
            data['_meta']['hostvars'][hostname] = {'ansible_host': ip,
                                                   'ansible_port': port}
            if zabbixvars:
                data['_meta']['hostvars'][hostname].update(zabbixvars)

            data['_meta']['hostvars'][hostname]['templates'] = []
            for t in host['parentTemplates']:
                data['_meta']['hostvars'][hostname]['templates'].append(t['name'])

            for group in host['groups']:
                groupname = group['name']

                if groupname not in data:
                    data[groupname] = self.hoststub()

                data[groupname]['hosts'].append(hostname)

        return data

    def __init__(self):

        self.defaultgroup = 'group_all'
        self.zabbix_server = None
        self.zabbix_username = None
        self.zabbix_password = None
        self.meta = {}

        self.read_settings()
        self.read_cli()

        if self.zabbix_server and self.zabbix_username:
            try:
                api = ZabbixAPI(server=self.zabbix_server)
                api.login(user=self.zabbix_username,
                          password=self.zabbix_password)
            except BaseException as e:
                print("Error: Could not login to Zabbix server. Check your zabbix.ini.",
                      file=sys.stderr)
                print("Error message was: " + str(e))
                sys.exit(1)

            if self.options.host:
                data = self.get_host(api, self.options.host)
                print(json.dumps(data, indent=2))

            elif self.options.list:
                data = self.get_list(api)
                print(json.dumps(data, indent=2))

            else:
                print("usage: --list  ..OR.. --host <hostname>",
                      file=sys.stderr)
                sys.exit(1)

        else:
            print("Error: Configuration of server and credentials are required. See zabbix.ini.",
                  file=sys.stderr)
            sys.exit(1)

ZabbixInventory()
