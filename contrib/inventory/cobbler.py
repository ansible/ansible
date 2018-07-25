#!/usr/bin/env python

"""
Cobbler external inventory script
=================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this, copy this file over /etc/ansible/hosts and chmod +x the file.
This, more or less, allows you to keep one central database containing
info about all of your managed instances.

This script is an example of sourcing that data from Cobbler
(https://cobbler.github.io).  With cobbler each --mgmt-class in cobbler
will correspond to a group in Ansible, and --ks-meta variables will be
passed down for use in templates or even in argument lines.

NOTE: The cobbler system names will not be used.  Make sure a
cobbler --dns-name is set for each cobbler system.   If a system
appears with two DNS names we do not add it twice because we don't want
ansible talking to it twice.  The first one found will be used. If no
--dns-name is set the system will NOT be visible to ansible.  We do
not add cobbler system names because there is no requirement in cobbler
that those correspond to addresses.

Tested with Cobbler 2.0.11.

Changelog:
    - 2015-06-21 dmccue: Modified to support run-once _meta retrieval, results in
         higher performance at ansible startup.  Groups are determined by owner rather than
         default mgmt_classes.  DNS name determined from hostname. cobbler values are written
         to a 'cobbler' fact namespace

    - 2013-09-01 pgehres: Refactored implementation to make use of caching and to
        limit the number of connections to external cobbler server for performance.
        Added use of cobbler.ini file to configure settings. Tested with Cobbler 2.4.0

"""

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
# along with Ansible.  If not, see <https://www.gnu.org/licenses/>.

######################################################################

import argparse
import ConfigParser
import os
import re
from time import time
import xmlrpclib

try:
    import json
except ImportError:
    import simplejson as json

from six import iteritems

# NOTE -- this file assumes Ansible is being accessed FROM the cobbler
# server, so it does not attempt to login with a username and password.
# this will be addressed in a future version of this script.

orderby_keyname = 'owners'  # alternatively 'mgmt_classes'


class CobblerInventory(object):

    def __init__(self):

        """ Main execution path """
        self.conn = None

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory
        self.ignore_settings = False  # used to only look at env vars for settings.

        # Read env vars, read settings, and parse CLI arguments
        self.parse_env_vars()
        self.read_settings()
        self.parse_cli_args()

        # Cache
        if self.args.refresh_cache:
            self.update_cache()
        elif not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_cache_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            data_to_print += self.get_host_info()
        else:
            self.inventory['_meta'] = {'hostvars': {}}
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = {'cobbler': self.cache[hostname]}
            data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def _connect(self):
        if not self.conn:
            self.conn = xmlrpclib.Server(self.cobbler_host, allow_none=True)
            self.token = None
            if self.cobbler_username is not None:
                self.token = self.conn.login(self.cobbler_username, self.cobbler_password)

    def is_cache_valid(self):
        """ Determines if the cache files have expired, or if it is still valid """

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_inventory):
                    return True

        return False

    def read_settings(self):
        """ Reads the settings from the cobbler.ini file """

        if(self.ignore_settings):
            return

        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/cobbler.ini')

        self.cobbler_host = config.get('cobbler', 'host')
        self.cobbler_username = None
        self.cobbler_password = None
        if config.has_option('cobbler', 'username'):
            self.cobbler_username = config.get('cobbler', 'username')
        if config.has_option('cobbler', 'password'):
            self.cobbler_password = config.get('cobbler', 'password')

        # Cache related
        cache_path = config.get('cobbler', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-cobbler.cache"
        self.cache_path_inventory = cache_path + "/ansible-cobbler.index"
        self.cache_max_age = config.getint('cobbler', 'cache_max_age')

    def parse_env_vars(self):
        """ Reads the settings from the environment """

        # Env. Vars:
        #   COBBLER_host
        #   COBBLER_username
        #   COBBLER_password
        #   COBBLER_cache_path
        #   COBBLER_cache_max_age
        #   COBBLER_ignore_settings

        self.cobbler_host = os.getenv('COBBLER_host', None)
        self.cobbler_username = os.getenv('COBBLER_username', None)
        self.cobbler_password = os.getenv('COBBLER_password', None)

        # Cache related
        cache_path = os.getenv('COBBLER_cache_path', None)
        if(cache_path is not None):
            self.cache_path_cache = cache_path + "/ansible-cobbler.cache"
            self.cache_path_inventory = cache_path + "/ansible-cobbler.index"

        self.cache_max_age = int(os.getenv('COBBLER_cache_max_age', "30"))

        # ignore_settings is used to ignore the settings file, for use in Ansible
        # Tower (or AWX inventory scripts and not throw python exceptions.)
        if(os.getenv('COBBLER_ignore_settings', False) == "True"):
            self.ignore_settings = True

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Cobbler')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to cobbler (default: False - use cache files)')
        self.args = parser.parse_args()

    def update_cache(self):
        """ Make calls to cobbler and save the output in a cache """

        self._connect()
        self.groups = dict()
        self.hosts = dict()
        if self.token is not None:
            data = self.conn.get_systems(self.token)
        else:
            data = self.conn.get_systems()

        for host in data:
            # Get the FQDN for the host and add it to the right groups
            dns_name = host['hostname']  # None
            ksmeta = None
            interfaces = host['interfaces']
            # hostname is often empty for non-static IP hosts
            if dns_name == '':
                for (iname, ivalue) in iteritems(interfaces):
                    if ivalue['management'] or not ivalue['static']:
                        this_dns_name = ivalue.get('dns_name', None)
                        if this_dns_name is not None and this_dns_name is not "":
                            dns_name = this_dns_name

            if dns_name == '' or dns_name is None:
                continue

            status = host['status']
            profile = host['profile']
            classes = host[orderby_keyname]

            if status not in self.inventory:
                self.inventory[status] = []
            self.inventory[status].append(dns_name)

            if profile not in self.inventory:
                self.inventory[profile] = []
            self.inventory[profile].append(dns_name)

            for cls in classes:
                if cls not in self.inventory:
                    self.inventory[cls] = []
                self.inventory[cls].append(dns_name)

            # Since we already have all of the data for the host, update the host details as well

            # The old way was ksmeta only -- provide backwards compatibility

            self.cache[dns_name] = host
            if "ks_meta" in host:
                for key, value in iteritems(host["ks_meta"]):
                    self.cache[dns_name][key] = value

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)

    def get_host_info(self):
        """ Get variables about a specific host """

        if not self.cache or len(self.cache) == 0:
            # Need to load index from cache
            self.load_cache_from_cache()

        if self.args.host not in self.cache:
            # try updating the cache
            self.update_cache()

            if self.args.host not in self.cache:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.cache[self.args.host], True)

    def push(self, my_dict, key, element):
        """ Pushed an element onto an array that may not have been defined in the dict """

        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]

    def load_inventory_from_cache(self):
        """ Reads the index from the cache file sets self.index """

        cache = open(self.cache_path_inventory, 'r')
        json_inventory = cache.read()
        self.inventory = json.loads(json_inventory)

    def load_cache_from_cache(self):
        """ Reads the cache from the cache file sets self.cache """

        cache = open(self.cache_path_cache, 'r')
        json_cache = cache.read()
        self.cache = json.loads(json_cache)

    def write_to_cache(self, data, filename):
        """ Writes data in JSON format to a file """
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """ Converts 'bad' characters in a string to underscores so they can be used as Ansible groups """

        return re.sub(r"[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

CobblerInventory()
