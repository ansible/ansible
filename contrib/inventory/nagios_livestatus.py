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

Checkmk livestatus: https://mathias-kettner.de/checkmk_livestatus.html
Livestatus API: http://www.naemon.org/documentation/usersguide/livestatus.html
'''

import os
import re
import argparse
import sys

from ansible.module_utils.six.moves import configparser
import json

try:
    from mk_livestatus import Socket
except ImportError:
    sys.exit("Error: mk_livestatus is needed. Try something like: pip install python-mk-livestatus")


class NagiosLivestatusInventory(object):

    def parse_ini_file(self):
        config = configparser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/nagios_livestatus.ini')
        for section in config.sections():
            if not config.has_option(section, 'livestatus_uri'):
                continue

            # If fields_to_retrieve is not set, using default fields
            fields_to_retrieve = self.default_fields_to_retrieve
            if config.has_option(section, 'fields_to_retrieve'):
                fields_to_retrieve = [field.strip() for field in config.get(section, 'fields_to_retrieve').split(',')]
                fields_to_retrieve = tuple(fields_to_retrieve)

            # default section values
            section_values = {
                'var_prefix': 'livestatus_',
                'host_filter': None,
                'host_field': 'name',
                'group_field': 'groups'
            }
            for key, value in section_values.items():
                if config.has_option(section, key):
                    section_values[key] = config.get(section, key).strip()

            # Retrieving livestatus string connection
            livestatus_uri = config.get(section, 'livestatus_uri')
            backend_definition = None

            # Local unix socket
            unix_match = re.match('unix:(.*)', livestatus_uri)
            if unix_match is not None:
                backend_definition = {'connection': unix_match.group(1)}

            # Remote tcp connection
            tcp_match = re.match('tcp:(.*):([^:]*)', livestatus_uri)
            if tcp_match is not None:
                backend_definition = {'connection': (tcp_match.group(1), int(tcp_match.group(2)))}

            # No valid livestatus_uri => exiting
            if backend_definition is None:
                raise Exception('livestatus_uri field is invalid (%s). Expected: unix:/path/to/live or tcp:host:port' % livestatus_uri)

            # Updating backend_definition with current value
            backend_definition['name'] = section
            backend_definition['fields'] = fields_to_retrieve
            for key, value in section_values.items():
                backend_definition[key] = value

            self.backends.append(backend_definition)

    def parse_options(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', nargs=1)
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--pretty', action='store_true')
        self.options = parser.parse_args()

    def add_host(self, hostname, group):
        if group not in self.result:
            self.result[group] = {}
            self.result[group]['hosts'] = []
        if hostname not in self.result[group]['hosts']:
            self.result[group]['hosts'].append(hostname)

    def query_backend(self, backend, host=None):
        '''Query a livestatus backend'''
        hosts_request = Socket(backend['connection']).hosts.columns(backend['host_field'], backend['group_field'])

        if backend['host_filter'] is not None:
            hosts_request = hosts_request.filter(backend['host_filter'])

        if host is not None:
            hosts_request = hosts_request.filter('name = ' + host[0])

        hosts_request._columns += backend['fields']

        hosts = hosts_request.call()
        for host in hosts:
            hostname = host[backend['host_field']]
            hostgroups = host[backend['group_field']]
            if not isinstance(hostgroups, list):
                hostgroups = [hostgroups]
            self.add_host(hostname, 'all')
            self.add_host(hostname, backend['name'])
            for group in hostgroups:
                self.add_host(hostname, group)
            for field in backend['fields']:
                var_name = backend['var_prefix'] + field
                if hostname not in self.result['_meta']['hostvars']:
                    self.result['_meta']['hostvars'][hostname] = {}
                self.result['_meta']['hostvars'][hostname][var_name] = host[field]

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
            sys.exit("Error: Livestatus configuration is missing. See nagios_livestatus.ini.")

        for backend in self.backends:
            self.query_backend(backend, self.options.host)

        if self.options.host:
            print(json.dumps(self.result['_meta']['hostvars'][self.options.host[0]], indent=self.json_indent))
        elif self.options.list:
            print(json.dumps(self.result, indent=self.json_indent))
        else:
            sys.exit("usage: --list or --host HOSTNAME [--pretty]")


NagiosLivestatusInventory()
