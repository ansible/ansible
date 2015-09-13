#!/usr/bin/env python

# (c) 2015, Yannig Perre <yannig.perre@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

'''
Nagios livestatus inventory script. Before using this script, please
update nagios_livestatus.ini file.

Livestatus is a nagios/naemon/shinken module which let you retrieve
informations stored in the monitoring core.

This plugin inventory need livestatus API for python. Please install it
before using this script (apt/pip/yum/...).

'''

import os
import re
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser
    configparser = ConfigParser
import json

try:
    from mk_livestatus import Socket
except ImportError:
    print("Error: mk_livestatus is needed. Try something like: pip install python-mk-livestatus")
    exit(1)

class NagiosLivestatusInventory(object):

    def parse_ini_file(self):
        config = configparser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/nagios_livestatus.ini')
        for section in config.sections():
            if not config.has_option(section, 'livestatus_uri'): continue

            # If fields_to_retrieve is not set, using default fields
            fields_to_retrieve = self.default_fields_to_retrieve
            if config.has_option(section, 'fields_to_retrieve'):
                fields_to_retrieve = [field.strip() for field in config.get(section, 'fields_to_retrieve').split(',')]
                fields_to_retrieve = tuple(fields_to_retrieve)

            # If prefix is not set, using livestatus_
            prefix = "livestatus_"
            if config.has_option(section, 'prefix'):
                prefix = config.get(section, 'prefix').strip()

            # Retrieving livestatus string connection
            livestatus_uri = config.get(section, 'livestatus_uri')
            # Local unix socket
            unix_match = re.match('unix:(.*)', livestatus_uri)
            if unix_match is not None:
                self.backends.append({
                  'connection': unix_match.group(1),
                  'fields':     fields_to_retrieve,
                  'name':       section,
                  'prefix':     prefix,
                })
                return
            # Remote tcp connection
            tcp_match = re.match('tcp:(.*):([^:]*)', livestatus_uri)
            if tcp_match is not None:
                self.backends.append({
                  'connection': (tcp_match.group(1), int(tcp_match.group(2))),
                  'fields':     fields_to_retrieve,
                  'name':       section,
                  'prefix':     prefix,
                })
                return
            raise Exception('livestatus_uri field is invalid (%s). Expected: unix:/path/to/live or tcp:host:port' % livestatus_uri)

    def parse_options(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host',   nargs=1)
        parser.add_argument('--list',   action='store_true')
        parser.add_argument('--pretty', action='store_true')
        self.options = parser.parse_args()

    def add_host(self, hostname, group):
        if group not in self.result:
            self.result[group] = {}
            self.result[group]['hosts'] = []
        if hostname not in self.result[group]:
            self.result[group]['hosts'].append(hostname)

    def query_backend(self, backend, host = None):
        '''Query a livestatus backend'''
        hosts_request = Socket(backend['connection']).hosts.columns('name', 'groups')
        if host is not None:
            hosts_request = hosts_request.filter('name = ' + host[0])
        hosts_request._columns += backend['fields']

        hosts = hosts_request.call()
        for host in hosts:
            self.add_host(host['name'], 'all')
            self.add_host(host['name'], backend['name'])
            for group in host['groups']:
                self.add_host(host['name'], group)
            for field in backend['fields']:
                var_name = backend['prefix'] + field
                if host['name'] not in self.result['_meta']['hostvars']:
                    self.result['_meta']['hostvars'][host['name']] = {}
                self.result['_meta']['hostvars'][host['name']][var_name] = host[field]

    def __init__(self):

        self.defaultgroup = 'group_all'
        self.default_fields_to_retrieve = ('address', 'alias', 'display_name', 'childs', 'parents')
        self.backends = []
        self.options = None

        self.parse_ini_file()
        self.parse_options()

        self.result = {}
        self.result['_meta'] = {}
        self.result['_meta']['hostvars'] = {}
        self.json_indent = None
        if self.options.pretty:
            self.json_indent = 2

        if len(self.backends) == 0:
            print "Error: Livestatus configuration is missing. See nagios_livestatus.ini."
            exit(1)

        for backend in self.backends:
            self.query_backend(backend, self.options.host)

        if self.options.host:
            print json.dumps(self.result['_meta']['hostvars'][self.options.host[0]], indent = self.json_indent)
        elif self.options.list:
            print json.dumps(self.result, indent = self.json_indent)
        else:
            print "usage: --list or --host HOSTNAME [--pretty]"
            exit(1)

NagiosLivestatusInventory()
