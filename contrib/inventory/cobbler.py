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

Tested with Cobbler 2.8.5.

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
try:
    import ConfigParser as configparser
except ImportError:
    import configparser
import os
import re
import socket
import sys
from time import time
try:
    import xmlrpclib as xmlrpc_client
except ImportError:
    import xmlrpc.client as xmlrpc_client

try:
    import json
except ImportError:
    import simplejson as json

from six import iteritems


class CobblerInventory(object):
    """ Cobbler Inventory object """

    def __init__(self):

        """ Main execution path """
        self.conn = dict()
        self.sites = dict()
        self.token = dict()

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Options
        self.exclude_profiles = [] # A list of profiles to exclude

        # Cache
        if self.args.refresh_cache or not self.is_cache_valid():
            try:
                self.update_cache()
            except (socket.gaierror, socket.error, xmlrpc_client.ProtocolError):
                if self.args.debug:
                    sys.stderr.write('Cannot update cache, loading cache\n')
                self.load_inventory_from_cache()
                self.load_cache_from_cache()
        else:
            if self.args.debug:
                sys.stderr.write('Loading cache\n')
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
            for site in list(self.sites.keys()):
                self.conn[site] = xmlrpc_client.Server(self.sites[site]['cobbler_host'], allow_none=True)
                self.token[site] = None
                if self.sites[site]['cobbler_username'] is not None:
                    self.token[site] = self.conn[site].login(self.sites[site]['cobbler_username'], self.sites[site]['cobbler_password'])

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

        config = configparser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/cobbler.ini')

        if config.has_option('cobbler', 'host'):
            self.sites['default'] = dict()
            self.sites['default']['cobbler_host'] = config.get('cobbler', 'host')
            self.sites['default']['cobbler_username'] = None
            self.sites['default']['cobbler_password'] = None
            if config.has_option('cobbler', 'username'):
                self.sites['default']['cobbler_username'] = config.get('cobbler', 'username')
            if config.has_option('cobbler', 'password'):
                self.sites['default']['cobbler_password'] = config.get('cobbler', 'password')
        else:
            for section in config.sections():
                match = re.search('^site_(.*)', section)
                if match is not None:
                    section = match.group(0)
                    site = match.group(1)
                    self.sites[site] = dict()
                    self.sites[site]['cobbler_host'] = config.get(section, 'host')
                    self.sites[site]['cobbler_username'] = None
                    self.sites[site]['cobbler_password'] = None
                    if config.has_option(section, 'username'):
                        self.sites[site]['cobbler_username'] = config.get(section, 'username')
                    if config.has_option(section, 'password'):
                        self.sites[site]['cobbler_password'] = config.get(section, 'password')

        if config.has_option('cobbler', 'exclude_profiles'):
            self.exclude_profiles = config.get('cobbler', 'exclude_profiles').split(',')

        # Cache related
        try:
            cache_path = config.get('cobbler', 'cache_path')
        except configparser.NoOptionError:
            cache_path = "$XDG_CACHE_HOME"
        if os.getenv('XDG_CACHE_HOME') is None:
            os.environ['XDG_CACHE_HOME'] = os.path.expandvars('$HOME/.cache')
        cache_path = os.path.expandvars(cache_path)
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        self.cache_path_cache = cache_path + "/ansible-cobbler.cache"
        self.cache_path_inventory = cache_path + "/ansible-cobbler.index"
        self.cache_max_age = config.getint('cobbler', 'cache_max_age')

        self.orderby_keyname = config.get('cobbler', 'orderby_keyname')

    def parse_cli_args(self):
        """ Command line argument processing """

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Cobbler')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--debug', action='store_true', default=False, help='Print debug info')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to cobbler (default: False - use cache files)')
        self.args = parser.parse_args()

    def update_cache(self):
        """ Make calls to cobbler and save the output in a cache """

        self._connect()
        self.groups = dict()
        self.hosts = dict()
        self.parent_profiles = dict()

        for site in list(self.sites.keys()):
            if self.args.debug:
                sys.stderr.write('Processing site %s\n' % site)
            if self.token[site] is not None:
                data = self.conn[site].get_profiles(self.token[site])
            else:
                data = self.conn[site].get_profiles()

            for profile in data:
                if profile['parent']:
                    if self.args.debug:
                        sys.stderr.write('Processing profile %s with parent %s\n' % (profile['name'], profile['parent']))
                    if profile['parent'] not in self.exclude_profiles:
                        if profile['parent'] not in self.inventory:
                            self.inventory[profile['parent']] = {'children': [], 'hosts': []}
                        if profile['name'] not in self.inventory[profile['parent']]['children']:
                            self.inventory[profile['parent']]['children'].append(profile['name'])
                else:
                    if self.args.debug:
                        sys.stderr.write('Processing profile %s without parent\n' % profile['name'])
                    # Create a heirarchy of profile names
                    profile_elements = profile['name'].split('-')
                    i = 0
                    while i < len(profile_elements)-1:
                        profile_group = '-'.join(profile_elements[0:i+1])
                        profile_group_child = '-'.join(profile_elements[0:i+2])
                        if profile_group in self.exclude_profiles:
                            if self.args.debug:
                                sys.stderr.write('Excluding profile %s\n' % profile_group)
                            break
                        if profile_group not in self.inventory:
                            if self.args.debug:
                                sys.stderr.write('Adding profile %s\n' % profile_group)
                            self.inventory[profile_group] = {'children': [], 'hosts': []}
                        if profile_group_child not in self.inventory[profile_group]['children']:
                            if self.args.debug:
                                sys.stderr.write('Adding profile child %s to %s\n' % (profile_group_child, profile_group))
                            self.inventory[profile_group]['children'].append(profile_group_child)
                        i = i + 1

            if self.token[site] is not None:
                data = self.conn[site].get_systems(self.token[site])
            else:
                data = self.conn[site].get_systems()

            for host in data:
                # Get the FQDN for the host and add it to the right groups
                dns_name = host['hostname']  # None
                interfaces = host['interfaces']
                if self.args.debug:
                    sys.stderr.write('Processing host %s dns_name %s\n' % (host['name'], dns_name))
                if host['profile'] in self.exclude_profiles:
                    continue
                # hostname is often empty for non-static IP hosts
                if dns_name == '':
                    for (iname, ivalue) in iteritems(interfaces):
                        if ivalue['management'] or not ivalue['static']:
                            this_dns_name = ivalue.get('dns_name', None)
                            if this_dns_name is not None and this_dns_name is not "":
                                dns_name = this_dns_name
                                if self.args.debug:
                                    sys.stderr.write('Set dns_name to %s from %s\n' % (dns_name, iname))

                if dns_name == '':
                    continue

                status = host['status']
                profile = host['profile']
                if host[self.orderby_keyname] == '<<inherit>>':
                    classes = []
                else:
                    classes = host[self.orderby_keyname]

                if status not in self.inventory:
                    self.inventory[status] = {'hosts': []}
                self.inventory[status]['hosts'].append(dns_name)

                # Add host to profile group
                if profile not in self.inventory:
                    self.inventory[profile] = {'children': [], 'hosts': []}
                self.inventory[profile]['hosts'].append(dns_name)

                if self.args.debug:
                    sys.stderr.write('Adding host %s to profile %s\n' % (dns_name, profile))

                for cls in classes:
                    if cls not in self.inventory:
                        self.inventory[cls] = {'hosts': []}
                    if self.args.debug:
                        sys.stderr.write('Adding host %s to class %s\n' % (dns_name, cls))
                    self.inventory[cls]['hosts'].append(dns_name)

                if site != 'default':
                    if site not in self.inventory:
                        if self.args.debug:
                            sys.stderr.write('Adding site %s to inventory\n' % site)
                        self.inventory[site] = {'hosts': []}
                    if self.args.debug:
                        sys.stderr.write('Adding %s to site %s\n' % (dns_name, site))
                    self.inventory[site]['hosts'].append(dns_name)

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

        return re.sub("[^A-Za-z0-9\-]", "_", word)

    def json_format_dict(self, data, pretty=False):
        """ Converts a dict to a JSON object and dumps it as a formatted string """

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


CobblerInventory()
