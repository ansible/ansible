#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2016 Guido Günther <agx@sigxcpu.org>
#
# This script is free software: you can redistribute it and/or modify
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
# along with it.  If not, see <http://www.gnu.org/licenses/>.
#
# This is loosely based on the foreman inventory script
# -- Josh Preston <jpreston@redhat.com>
#

from __future__ import print_function
import argparse
import ConfigParser
import os
import re
from time import time
import requests
from requests.auth import HTTPBasicAuth
import warnings
from ansible.errors import AnsibleError

try:
    import json
except ImportError:
    import simplejson as json


class CloudFormsInventory(object):
    def __init__(self):
        """
        Main execution path
        """
        self.inventory = dict()  # A list of groups and the hosts in that group
        self.hosts = dict()      # Details about hosts in the inventory

        # Parse CLI arguments
        self.parse_cli_args()

        # Read settings
        self.read_settings()

        # Cache
        if self.args.refresh_cache or not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_hosts_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            if self.args.debug:
                print("Fetching host [%s]" % self.args.host)
            data_to_print += self.get_host_info(self.args.host)
        else:
            self.inventory['_meta'] = {'hostvars': {}}
            for hostname in self.hosts:
                self.inventory['_meta']['hostvars'][hostname] = {
                    'cloudforms': self.hosts[hostname],
                }
                # include the ansible_ssh_host in the top level
                if 'ansible_ssh_host' in self.hosts[hostname]:
                    self.inventory['_meta']['hostvars'][hostname]['ansible_ssh_host'] = self.hosts[hostname]['ansible_ssh_host']

            data_to_print += self.json_format_dict(self.inventory, self.args.pretty)

        print(data_to_print)

    def is_cache_valid(self):
        """
        Determines if the cache files have expired, or if it is still valid
        """
        if self.args.debug:
            print("Determining if cache [%s] is still valid (< %s seconds old)" % (self.cache_path_hosts, self.cache_max_age))

        if os.path.isfile(self.cache_path_hosts):
            mod_time = os.path.getmtime(self.cache_path_hosts)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if os.path.isfile(self.cache_path_inventory):
                    if self.args.debug:
                        print("Cache is still valid!")
                    return True

        if self.args.debug:
            print("Cache is stale or does not exist.")

        return False

    def read_settings(self):
        """
        Reads the settings from the cloudforms.ini file
        """
        config = ConfigParser.SafeConfigParser()
        config_paths = [
            os.path.dirname(os.path.realpath(__file__)) + '/cloudforms.ini',
            "/etc/ansible/cloudforms.ini",
        ]

        env_value = os.environ.get('CLOUDFORMS_INI_PATH')
        if env_value is not None:
            config_paths.append(os.path.expanduser(os.path.expandvars(env_value)))

        if self.args.debug:
            for config_path in config_paths:
                print("Reading from configuration file [%s]" % config_path)

        config.read(config_paths)

        # CloudForms API related
        if config.has_option('cloudforms', 'url'):
            self.cloudforms_url = config.get('cloudforms', 'url')
        else:
            self.cloudforms_url = None

        if not self.cloudforms_url:
            warnings.warn("No url specified, expected something like 'https://cfme.example.com'")

        if config.has_option('cloudforms', 'username'):
            self.cloudforms_username = config.get('cloudforms', 'username')
        else:
            self.cloudforms_username = None

        if not self.cloudforms_username:
            warnings.warn("No username specified, you need to specify a CloudForms username.")

        if config.has_option('cloudforms', 'password'):
            self.cloudforms_pw = config.get('cloudforms', 'password', raw=True)
        else:
            self.cloudforms_pw = None

        if not self.cloudforms_pw:
            warnings.warn("No password specified, you need to specify a password for the CloudForms user.")

        if config.has_option('cloudforms', 'ssl_verify'):
            self.cloudforms_ssl_verify = config.getboolean('cloudforms', 'ssl_verify')
        else:
            self.cloudforms_ssl_verify = True

        if config.has_option('cloudforms', 'version'):
            self.cloudforms_version = config.get('cloudforms', 'version')
        else:
            self.cloudforms_version = None

        if config.has_option('cloudforms', 'limit'):
            self.cloudforms_limit = config.getint('cloudforms', 'limit')
        else:
            self.cloudforms_limit = 100

        if config.has_option('cloudforms', 'purge_actions'):
            self.cloudforms_purge_actions = config.getboolean('cloudforms', 'purge_actions')
        else:
            self.cloudforms_purge_actions = True

        if config.has_option('cloudforms', 'clean_group_keys'):
            self.cloudforms_clean_group_keys = config.getboolean('cloudforms', 'clean_group_keys')
        else:
            self.cloudforms_clean_group_keys = True

        if config.has_option('cloudforms', 'nest_tags'):
            self.cloudforms_nest_tags = config.getboolean('cloudforms', 'nest_tags')
        else:
            self.cloudforms_nest_tags = False

        if config.has_option('cloudforms', 'suffix'):
            self.cloudforms_suffix = config.get('cloudforms', 'suffix')
            if self.cloudforms_suffix[0] != '.':
                raise AnsibleError('Leading fullstop is required for Cloudforms suffix')
        else:
            self.cloudforms_suffix = None

        if config.has_option('cloudforms', 'prefer_ipv4'):
            self.cloudforms_prefer_ipv4 = config.getboolean('cloudforms', 'prefer_ipv4')
        else:
            self.cloudforms_prefer_ipv4 = False

        # Ansible related
        try:
            group_patterns = config.get('ansible', 'group_patterns')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            group_patterns = "[]"

        self.group_patterns = eval(group_patterns)

        # Cache related
        try:
            cache_path = os.path.expanduser(config.get('cache', 'path'))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            cache_path = '.'
        (script, ext) = os.path.splitext(os.path.basename(__file__))
        self.cache_path_hosts = cache_path + "/%s.hosts" % script
        self.cache_path_inventory = cache_path + "/%s.inventory" % script
        self.cache_max_age = config.getint('cache', 'max_age')

        if self.args.debug:
            print("CloudForms settings:")
            print("cloudforms_url               = %s" % self.cloudforms_url)
            print("cloudforms_username          = %s" % self.cloudforms_username)
            print("cloudforms_pw                = %s" % self.cloudforms_pw)
            print("cloudforms_ssl_verify        = %s" % self.cloudforms_ssl_verify)
            print("cloudforms_version           = %s" % self.cloudforms_version)
            print("cloudforms_limit             = %s" % self.cloudforms_limit)
            print("cloudforms_purge_actions     = %s" % self.cloudforms_purge_actions)
            print("Cache settings:")
            print("cache_max_age        = %s" % self.cache_max_age)
            print("cache_path_hosts     = %s" % self.cache_path_hosts)
            print("cache_path_inventory = %s" % self.cache_path_inventory)

    def parse_cli_args(self):
        """
        Command line argument processing
        """
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on CloudForms managed VMs')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--pretty', action='store_true', default=False, help='Pretty print JSON output (default: False)')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to CloudForms (default: False - use cache files)')
        parser.add_argument('--debug', action='store_true', default=False, help='Show debug output while running (default: False)')
        self.args = parser.parse_args()

    def _get_json(self, url):
        """
        Make a request and return the JSON
        """
        results = []

        ret = requests.get(url,
                           auth=HTTPBasicAuth(self.cloudforms_username, self.cloudforms_pw),
                           verify=self.cloudforms_ssl_verify)

        ret.raise_for_status()

        try:
            results = json.loads(ret.text)
        except ValueError:
            warnings.warn("Unexpected response from {0} ({1}): {2}".format(self.cloudforms_url, ret.status_code, ret.reason))
            results = {}

        if self.args.debug:
            print("=======================================================================")
            print("=======================================================================")
            print("=======================================================================")
            print(ret.text)
            print("=======================================================================")
            print("=======================================================================")
            print("=======================================================================")

        return results

    def _get_hosts(self):
        """
        Get all hosts by paging through the results
        """
        limit = self.cloudforms_limit

        page = 0
        last_page = False

        results = []

        while not last_page:
            offset = page * limit
            ret = self._get_json("%s/api/vms?offset=%s&limit=%s&expand=resources,tags,hosts,&attributes=ipaddresses" % (self.cloudforms_url, offset, limit))
            results += ret['resources']
            if ret['subcount'] < limit:
                last_page = True
            page += 1

        return results

    def update_cache(self):
        """
        Make calls to cloudforms and save the output in a cache
        """
        self.groups = dict()
        self.hosts = dict()

        if self.args.debug:
            print("Updating cache...")

        for host in self._get_hosts():
            if self.cloudforms_suffix is not None and not host['name'].endswith(self.cloudforms_suffix):
                host['name'] = host['name'] + self.cloudforms_suffix

            # Ignore VMs that are not powered on
            if host['power_state'] != 'on':
                if self.args.debug:
                    print("Skipping %s because power_state = %s" % (host['name'], host['power_state']))
                continue

            # purge actions
            if self.cloudforms_purge_actions and 'actions' in host:
                del host['actions']

            # Create ansible groups for tags
            if 'tags' in host:

                # Create top-level group
                if 'tags' not in self.inventory:
                    self.inventory['tags'] = dict(children=[], vars={}, hosts=[])

                if not self.cloudforms_nest_tags:
                    # don't expand tags, just use them in a safe way
                    for group in host['tags']:
                        # Add sub-group, as a child of top-level
                        safe_key = self.to_safe(group['name'])
                        if safe_key:
                            if self.args.debug:
                                print("Adding sub-group '%s' to parent 'tags'" % safe_key)

                            if safe_key not in self.inventory['tags']['children']:
                                self.push(self.inventory['tags'], 'children', safe_key)

                            self.push(self.inventory, safe_key, host['name'])

                            if self.args.debug:
                                print("Found tag [%s] for host which will be mapped to [%s]" % (group['name'], safe_key))
                else:
                    # expand the tags into nested groups / sub-groups
                    # Create nested groups for tags
                    safe_parent_tag_name = 'tags'
                    for tag in host['tags']:
                        tag_hierarchy = tag['name'][1:].split('/')

                        if self.args.debug:
                            print("Working on list %s" % tag_hierarchy)

                        for tag_name in tag_hierarchy:
                            if self.args.debug:
                                print("Working on tag_name = %s" % tag_name)

                            safe_tag_name = self.to_safe(tag_name)
                            if self.args.debug:
                                print("Using sanitized name %s" % safe_tag_name)

                            # Create sub-group
                            if safe_tag_name not in self.inventory:
                                self.inventory[safe_tag_name] = dict(children=[], vars={}, hosts=[])

                            # Add sub-group, as a child of top-level
                            if safe_parent_tag_name:
                                if self.args.debug:
                                    print("Adding sub-group '%s' to parent '%s'" % (safe_tag_name, safe_parent_tag_name))

                                if safe_tag_name not in self.inventory[safe_parent_tag_name]['children']:
                                    self.push(self.inventory[safe_parent_tag_name], 'children', safe_tag_name)

                            # Make sure the next one uses this one as it's parent
                            safe_parent_tag_name = safe_tag_name

                        # Add the host to the last tag
                        self.push(self.inventory[safe_parent_tag_name], 'hosts', host['name'])

            # Set ansible_ssh_host to the first available ip address
            if 'ipaddresses' in host and host['ipaddresses'] and isinstance(host['ipaddresses'], list):
                # If no preference for IPv4, just use the first entry
                if not self.cloudforms_prefer_ipv4:
                    host['ansible_ssh_host'] = host['ipaddresses'][0]
                else:
                    # Before we search for an IPv4 address, set using the first entry in case we don't find any
                    host['ansible_ssh_host'] = host['ipaddresses'][0]
                    for currenthost in host['ipaddresses']:
                        if '.' in currenthost:
                            host['ansible_ssh_host'] = currenthost

            # Create additional groups
            for key in ('location', 'type', 'vendor'):
                safe_key = self.to_safe(host[key])

                # Create top-level group
                if key not in self.inventory:
                    self.inventory[key] = dict(children=[], vars={}, hosts=[])

                # Create sub-group
                if safe_key not in self.inventory:
                    self.inventory[safe_key] = dict(children=[], vars={}, hosts=[])

                # Add sub-group, as a child of top-level
                if safe_key not in self.inventory[key]['children']:
                    self.push(self.inventory[key], 'children', safe_key)

                if key in host:
                    # Add host to sub-group
                    self.push(self.inventory[safe_key], 'hosts', host['name'])

            self.hosts[host['name']] = host
            self.push(self.inventory, 'all', host['name'])

        if self.args.debug:
            print("Saving cached data")

        self.write_to_cache(self.hosts, self.cache_path_hosts)
        self.write_to_cache(self.inventory, self.cache_path_inventory)

    def get_host_info(self, host):
        """
        Get variables about a specific host
        """
        if not self.hosts or len(self.hosts) == 0:
            # Need to load cache from cache
            self.load_hosts_from_cache()

        if host not in self.hosts:
            if self.args.debug:
                print("[%s] not found in cache." % host)

            # try updating the cache
            self.update_cache()

            if host not in self.hosts:
                if self.args.debug:
                    print("[%s] does not exist after cache update." % host)
                # host might not exist anymore
                return self.json_format_dict({}, self.args.pretty)

        return self.json_format_dict(self.hosts[host], self.args.pretty)

    def push(self, d, k, v):
        """
        Safely puts a new entry onto an array.
        """
        if k in d:
            d[k].append(v)
        else:
            d[k] = [v]

    def load_inventory_from_cache(self):
        """
        Reads the inventory from the cache file sets self.inventory
        """
        cache = open(self.cache_path_inventory, 'r')
        json_inventory = cache.read()
        self.inventory = json.loads(json_inventory)

    def load_hosts_from_cache(self):
        """
        Reads the cache from the cache file sets self.hosts
        """
        cache = open(self.cache_path_hosts, 'r')
        json_cache = cache.read()
        self.hosts = json.loads(json_cache)

    def write_to_cache(self, data, filename):
        """
        Writes data in JSON format to a file
        """
        json_data = self.json_format_dict(data, True)
        cache = open(filename, 'w')
        cache.write(json_data)
        cache.close()

    def to_safe(self, word):
        """
        Converts 'bad' characters in a string to underscores so they can be used as Ansible groups
        """
        if self.cloudforms_clean_group_keys:
            regex = r"[^A-Za-z0-9\_]"
            return re.sub(regex, "_", word.replace(" ", ""))
        else:
            return word

    def json_format_dict(self, data, pretty=False):
        """
        Converts a dict to a JSON object and dumps it as a formatted string
        """
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

CloudFormsInventory()
