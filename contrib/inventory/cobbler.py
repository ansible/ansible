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
(http://cobbler.github.com).  With cobbler each --mgmt-class in cobbler
will correspond to a group in Ansible, and --ks-meta variables will be
passed down for use in templates or even in argument lines.

NOTE: The cobbler system names will not be used.  Make sure a
cobbler --dns-name is set for each cobbler system.   If a system
appears with two DNS names we do not add it twice because we don't want
ansible talking to it twice.  The first one found will be used. If no
--dns-name is set the system will NOT be visible to ansible.  We do
not add cobbler system names because there is no requirement in cobbler
that those correspond to addresses.

See http://ansible.github.com/api.html for more info

Tested with Cobbler 2.0.11.

Changelog:
    - 2015-08-25 gregmark: Refactored to leverage Cobbler system, profile, and management class
        parameters to produce a more robust and exact output; all configurable in cobbler.ini:
        o  assigning system objects to groups based on owners and/or status and/or profiles,
           and/or management classes. 
        o  assigning groups to parent groups based on the special management class parameter
           "parent". Only one parent per class is currently supported. Profile mgmt classes
            can be inherited, optionally.
        o  assigning group and hostvars based on either or both ks_meta params or management
           parameters.
        o  Optional: have system objects inherit vars from their respective profiles  
        o  Optional: Only include system objects with at least one interface w/ management = 1
        o  Limitations: there is no good way to assign groupvars or children to groups based on
           owners or status. Currently, parents can not be assigned in profiles and only one
           parent can be assigned per child group (this could be added easily). inherit_profiles
           and profile_groups are mutually exclusive, with the former preferred.
        Tested with Cobbler 2.6.7.

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
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

######################################################################

import argparse
import ConfigParser
import os
import re
from time import time
import xmlrpclib
import pprint

try:
    import json
except ImportError:
    import simplejson as json

# NOTE -- this file assumes Ansible is being accessed FROM the cobbler
# server, so it does not attempt to login with a username and password.
# this will be addressed in a future version of this script.


class CobblerInventory(object):

    def __init__(self):

        """ Main execution path """
        self.conn = None

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory

        # Read settings and parse CLI arguments
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
            self.inventory['_meta'] = { 'hostvars': {} }
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = self.cache[hostname]
            data_to_print += self.json_format_dict(self.inventory, True)

        print data_to_print

    def _connect(self):
        if not self.conn:
            self.conn = xmlrpclib.Server(self.cobbler_host, allow_none=True)

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

        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/cobbler.ini')

        self.cobbler_host = config.get('cobbler', 'host')

        # Cache related
        cache_path = config.get('cobbler', 'cache_path')
        self.cache_path_cache = cache_path + "/ansible-cobbler.cache"
        self.cache_path_inventory = cache_path + "/ansible-cobbler.index"
        self.cache_max_age = config.getint('cobbler', 'cache_max_age')

        # Group related
        self.owner_groups = config.getboolean('cobbler', 'owner_groups')
        self.status_groups = config.getboolean('cobbler', 'status_groups')
        self.profile_groups = config.getboolean('cobbler', 'profile_groups')
        self.mgmt_class_groups = config.getboolean('cobbler', 'mgmt_class_groups')

        # Hostvar related
        self.ksmeta_params = config.getboolean('cobbler', 'ksmeta_params')
        self.mgmt_params = config.getboolean('cobbler', 'mgmt_params')

        # Other
        self.require_management = config.getboolean('cobbler', 'require_management')
        self.inherit_profiles = config.getboolean('cobbler', 'inherit_profiles')
        self.inherit_children = config.getboolean('cobbler', 'inherit_children')

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

        data = self.conn.get_systems()
        p_data = dict()
        profile_data = dict()
        c_data = dict()
        class_data = dict()
        parents = dict()
        found_groups = []

        if self.inherit_profiles:
            p_data = self.conn.get_profiles() 
            # Refactor, with profile name as key, profile hash as value
            for _profile in p_data:
                p_name = _profile['name']
                profile_data[p_name] = _profile

        if self.mgmt_class_groups:
            c_data = self.conn.get_mgmtclasses()
            #refactor
            for _class in c_data:
                c_name = _class['name']
                class_data[c_name] = _class

        """ HOSTS """
        for host in data:
            # Get the FQDN for the host and add it to the right groups
            dns_name = None
            ksmeta = None
            hostname = host['hostname']
            interfaces = host['interfaces']

            owners = host['owners']
            status = host['status']
            profile = host['profile']
            classes = host['mgmt_classes']

            # Prevent redundancy
            if self.profile_groups and self.inherit_profiles:
                self.inherit_pofiles = False

            # If set, require at least one cb sys object interface have management = 1
            if self.require_management:
                for (iname, ivalue) in interfaces.iteritems():
                    if ivalue['management']:
                        this_dns_name = ivalue.get('dns_name', None)
                        if this_dns_name is not None and this_dns_name is not "":
                            dns_name = this_dns_name
                            break
            else:
                dns_name = hostname

            if dns_name is None or dns_name is "":
                continue

            # So if A) cobbler.ini param "management = 0" and the cb sys object lacks an
            # interface with cb param "management = 1", we default to the object hostname,
            # rather that search for the first valid dns_name? I thought about changing
            # this behavior, but it was accepted in the last pull request maybe for a 
            # good reason? Dunno.

            """ GROUP ASSIGNMENTS """
            # Assign cb sys object dns_name's to groups
            # Ensure groups can be assigned safely from all group sources at once, if required
            # Precedence: mgmt classes > profiles > status > owners

            if self.owner_groups:
                for own in owners:
                    self.assign_list(self.inventory, own, "hosts", dns_name)
                    self.push_list(found_groups, own)

            if self.status_groups:
                self.assign_list(self.inventory, status, "hosts", dns_name)
                self.push_list(found_groups, status)

            if self.profile_groups:
                self.assign_list(self.inventory, profile, "hosts", dns_name)
                self.push_list(found_groups, profile)

            if self.inherit_profiles:
                for pcls in profile_data[profile]['mgmt_classes']:
                    self.assign_list(self.inventory, pcls, "hosts", dns_name)
                    self.push_list(found_groups, pcls)

            if self.mgmt_class_groups:
                for cls in classes:
                    self.assign_list(self.inventory, cls, "hosts", dns_name)
                    self.push_list(found_groups, cls)

            """ HOSTVARS """
            # Since we already have all of the data for the host, update the host details as well
            # The old way was ksmeta only -- provide backwards compatibility
            # cb mgmt_parameters overwrite ks_meta vars if both are enabled


            # Inherit First from profiles
            if self.inherit_profiles and self.ksmeta_params:
                self.assign_dict(profile_data[profile], self.cache, "ks_meta", dns_name)

            if self.inherit_profiles and self.mgmt_params:
                self.assign_dict(profile_data[profile], self.cache, "mgmt_parameters", dns_name)

            # Now assign or override from system object params
            if self.ksmeta_params:
                self.assign_dict(host, self.cache, "ks_meta", dns_name)

            if self.mgmt_params:
                self.assign_dict(host, self.cache, "mgmt_parameters", dns_name)

        """ GROUPVARS """
        # We also create a dict of parents and children to save time
        for grp in found_groups:

            if self.profile_groups:
                if grp in profile_data:
                    if self.ksmeta_params:
                        self.assign_dict(profile_data[grp], self.inventory[grp], "ks_meta", "vars")
                    if self.mgmt_params:
                        self.assign_dict(profile_data[grp], self.inventory[grp], "mgmt_parameters", "vars")

            if self.mgmt_class_groups:
                if grp in class_data:
                    self.assign_dict(class_data[grp], self.inventory[grp], "params", "vars")
                    if self.inherit_children and 'parent' in class_data[grp]['params']:
                        prt = class_data[grp]['params']['parent']
                        parents[grp] = prt 

        """ PARENTS AND CHILDREN """
        if self.inherit_children:
            for child in parents:
                parent = parents[child]
                self.assign_list(self.inventory, parent, "children", child)

                # Add groups that were reference as a parent, but not directly assigned to a system object
                if parent not in found_groups:
                    self.assign_dict(class_data[parent], self.inventory[parent], "params", "vars")

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)

    def assign_list(self, my_dict, og_key, new_key, my_val):
        if og_key is not None and og_key is not "":
            if og_key not in my_dict:
                my_dict[og_key] = { new_key : [] }
            # no duplicate entries
            if my_val not in my_dict[og_key][new_key]:
                my_dict[og_key][new_key].append(my_val)

    def assign_dict(self, dict_src, dict_dst, key_src, key_dst): 
        if key_src in dict_src:
            # do not create empty hostvars
            if isinstance(dict_src[key_src], dict) and dict_src[key_src]:
                if key_dst not in dict_dst:
                    dict_dst[key_dst] = dict(dict_src[key_src])
                else:
                    dict_dst[key_dst].update(dict_src[key_src])

    def get_host_info(self):
        """ Get variables about a specific host """

        if not self.cache or len(self.cache) == 0:
            # Need to load index from cache
            self.load_cache_from_cache()

        if not self.args.host in self.cache:
            # try updating the cache
            self.update_cache()

            if not self.args.host in self.cache:
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.cache[self.args.host], True)

    def push_list(self, my_list, element):
        if element not in my_list and element is not "":
            my_list.append(element)

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
