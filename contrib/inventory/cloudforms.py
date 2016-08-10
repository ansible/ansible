#!/usr/bin/python
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

import argparse
import ConfigParser
import copy
import os
import re
from time import time
import requests
from requests.auth import HTTPBasicAuth

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
        self.cache = dict()      # Details about hosts in the inventory
        self.params = dict()     # Params of each host

        # Parse CLI arguments
        self.parse_cli_args()

        # Debug?
        self.debug = self.args.debug

        # Read settings
        self.read_settings()

        # Cache
        if self.args.refresh_cache or not self.is_cache_valid():
            self.update_cache()
        else:
            self.load_inventory_from_cache()
            self.load_params_from_cache()
            self.load_cache_from_cache()

        data_to_print = ""

        # Data to print
        if self.args.host:
            if self.debug:
                print "Fetching host [%s]" % self.args.host
            data_to_print += self.get_host_info(self.args.host)
        else:
            self.inventory['_meta'] = {'hostvars': {}}
            for hostname in self.cache:
                self.inventory['_meta']['hostvars'][hostname] = {
                    'cloudforms': self.cache[hostname],
                    'cloudforms_params': self.params[hostname],
                }
            data_to_print += self.json_format_dict(self.inventory, True)

        print(data_to_print)

    def is_cache_valid(self):
        """
        Determines if the cache files have expired, or if it is still valid
        """
        if self.debug:
            print "Determining if cache [%s] is still valid (< %s seconds old)" % (self.cache_path_cache, self.cache_max_age)

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                if (os.path.isfile(self.cache_path_inventory) and
                    os.path.isfile(self.cache_path_params)):
                    if self.debug:
                        print "Cache is still valid!"
                    return True

        if self.debug:
            print "Cache is stale or does not exist."

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

        if self.debug:
            for config_path in config_paths:
                print "Reading from configuration file [%s]" % config_path

        config.read(config_paths)

        # CloudForms API related
        self.cloudforms_url = config.get('cloudforms', 'url')
        self.cloudforms_user = config.get('cloudforms', 'user')
        self.cloudforms_pw = config.get('cloudforms', 'password')
        self.cloudforms_ssl_verify = config.getboolean('cloudforms', 'ssl_verify')
        self.cloudforms_version = config.get('cloudforms', 'version')
        self.cloudforms_limit = config.getint('cloudforms', 'limit')

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
        self.cache_path_cache = cache_path + "/%s.cache" % script
        self.cache_path_inventory = cache_path + "/%s.inventory" % script
        self.cache_path_params = cache_path + "/%s.params" % script
        self.cache_max_age = config.getint('cache', 'max_age')

        if self.debug:
            print "CloudForms settings:"
            print "cloudforms_url        = %s" % self.cloudforms_url
            print "cloudforms_user       = %s" % self.cloudforms_user
            print "cloudforms_pw         = %s" % self.cloudforms_pw
            print "cloudforms_ssl_verify = %s" % self.cloudforms_ssl_verify
            print "cloudforms_version    = %s" % self.cloudforms_version
            print "cloudforms_limit      = %s" % self.cloudforms_limit
            print "Cache settings:"
            print "cache_path_cache      = %s" % self.cache_path_cache
            print "cache_path_inventory  = %s" % self.cache_path_inventory
            print "cache_path_params     = %s" % self.cache_path_params
            print "cache_max_age         = %s" % self.cache_max_age

    def parse_cli_args(self):
        """
        Command line argument processing
        """
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on CloudForms managed VMs')
        parser.add_argument('--list', action='store_true', default=True, help='List instances (default: True)')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to cloudforms (default: False - use cache files)')
        parser.add_argument('--debug', action='store_true', default=False, help='Show debug output while running (default: False)')
        self.args = parser.parse_args()

    def _get_json(self, url):
        """
        Make a request and return the JSON
        """
        results = []

        ret = requests.get(url,
                           auth=HTTPBasicAuth(self.cloudforms_user, self.cloudforms_pw),
                           verify=self.cloudforms_ssl_verify)

        ret.raise_for_status()
        results = json.loads(ret.text)

        if self.debug:
            print "======================================================================="
            print "======================================================================="
            print "======================================================================="
            print json.dumps(results, indent=2)
            print "======================================================================="
            print "======================================================================="
            print "======================================================================="

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
            ret = self._get_json("%s/api/vms?offset=%s&limit=%s&expand=resources,tags&attributes=id,ipaddresses,name,power_state" % (self.cloudforms_url, offset, limit))
            results += ret['resources']
            if ret['subcount'] < limit:
                last_page = True
            page += 1

        return results

    def _get_host_by_id(self, hid):
        return self._get_json("%s/api/vms/%s" % (self.cloudforms_url, hid))

    def _resolve_params(self, host):
        """
        Resolve all params of the host.
        """
        host_id = host['id']
        params = self._get_host_by_id(host_id)

        # get rid of the silly actions...
        del params['actions']

        return params

    def update_cache(self):
        """
        Make calls to cloudforms and save the output in a cache
        """
        self.groups = dict()
        self.hosts = dict()

        if self.debug:
            print "Updating cache..."

        for host in self._get_hosts():
            if host['power_state'] != 'on':
                if self.debug:
                    print "Skipping %s because power_state = %s" % (host['name'], host['power_state'])
                continue

            if host.has_key('ipaddresses') and host['ipaddresses'][0]:
                dns_name = host['ipaddresses'][0]
            else:
                dns_name = host['name']

            if self.debug:
                print "Host named [%s] will use [%s] as dns_name" % (host['name'], dns_name)

            # Create ansible groups for hostgroup, location and organization
            if host.has_key('tags'):
                for group in host['tags']:
                    safe_key = self.to_safe(group['name'])
                    self.push(self.inventory, safe_key, dns_name)

                    if self.debug:
                        print "Found tag [%s] for host which will be mapped to [%s]" % (group['name'], safe_key)

            params = self._resolve_params(host)

            self.cache[dns_name] = host
            self.params[dns_name] = params
            self.push(self.inventory, 'all', dns_name)

        if self.debug:
            print "Saving cached data"

        self.write_to_cache(self.cache, self.cache_path_cache)
        self.write_to_cache(self.inventory, self.cache_path_inventory)
        self.write_to_cache(self.params, self.cache_path_params)

    def get_host_info(self, host):
        """
        Get variables about a specific host
        """
        if not self.params or len(self.params) == 0:
            # Need to load params from cache
            self.load_params_from_cache()

        if host not in self.params:
            if self.debug:
                print "[%s] not found in cache." % host

            # try updating the cache
            self.update_cache()

            if host not in self.params:
                if self.debug:
                    print "[%s] does not exist after cache update." % host
                # host might not exist anymore
                return self.json_format_dict({}, True)

        return self.json_format_dict(self.params[host], True)

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

    def load_params_from_cache(self):
        """
        Reads the params from the cache file sets self.params
        """
        cache = open(self.cache_path_params, 'r')
        json_params = cache.read()
        self.params = json.loads(json_params)

    def load_cache_from_cache(self):
        """
        Reads the cache from the cache file sets self.cache
        """
        cache = open(self.cache_path_cache, 'r')
        json_cache = cache.read()
        self.cache = json.loads(json_cache)

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
        regex = "[^A-Za-z0-9\_]"
        return re.sub(regex, "_", word.replace(" ", ""))

    def json_format_dict(self, data, pretty=False):
        """
        Converts a dict to a JSON object and dumps it as a formatted string
        """
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

CloudFormsInventory()
