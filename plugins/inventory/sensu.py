#!/usr/bin/env python

# (c) 2014, Nobutoshi Ogata
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
Sensu Server external inventory script.
========================================

Returns hosts and subscriptions from Sensu Server.

Configuration is read from `sensu.ini`.

Tested with Sensu Server 0.12.6.
"""

import os
import sys
import argparse
try:
    import requests
except:
    print >> sys.stderr, "Error: HTTP request library must be installed: pip install requests."
    sys.exit(1)
try:
    import json
except:
    import simplejson as json
import ConfigParser

class SensuInventory(object):

    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host')
        parser.add_argument('--list', action='store_true')
        self.options = parser.parse_args()

    def read_settings(self):
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/sensu.ini')
        if config.has_option('sensu', 'server'):
            self.server   = config.get('sensu', 'server')
        if config.has_option('sensu', 'port'):
            self.port     = config.get('sensu', 'port')
        if config.has_option('sensu', 'user'):
            self.user     = config.get('sensu', 'user')
        if config.has_option('sensu', 'password'):
            self.password = config.get('sensu', 'password')

    def hoststub(self):
        return {
            'hosts': []
        }

    def get_host(self, url, name):
        data = {}
        return data

    def get_list(self, url):
        resp = requests.get(url)
        data = {}
        for server in resp.json():
            hostname = server['name']
            for group in server['subscriptions']:
                if not group in data:
                    data[group] = self.hoststub()
                data[group]['hosts'].append(hostname)
        return data

    def __init__(self):
        self.server   = None
        self.port     = 4567
        self.user     = None
        self.password = None

        self.read_settings()
        self.read_cli()

        if self.server:
            if self.user and self.password:
                url = "http://{}:{}@{}:{}/clients".format(self.user, self.password, self.server, self.port)
            elif not self.user and not self.password:
                url = "http://{}:{}/clients".format(self.server, self.port)
            else:
                print >> sys.stderr, "Error: Must specify both user and password"
                sys.exit(1)

            if self.options.host:
                data = self.get_host(url, self.options.host)
                print json.dumps(data, indent=2)
            elif self.options.list:
                data = self.get_list(url)
                print json.dumps(data, indent=2)
            else:
                print >> sys.stderr, "usage: --list  ..OR.. --host <hostname>"
                sys.exit(1)
        else:
            print >> sys.stderr, "Error: Configuration of server and credentials are required. See sensu.ini."
            sys.exit(1)

SensuInventory()
