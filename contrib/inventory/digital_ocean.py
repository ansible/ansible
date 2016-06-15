#!/usr/bin/env python

'''
DigitalOcean external inventory script
======================================

Generates Ansible inventory of DigitalOcean Droplets.

In addition to the --list and --host options used by Ansible, there are options
for generating JSON of other DigitalOcean data.  This is useful when creating
droplets.  For example, --regions will return all the DigitalOcean Regions.
This information can also be easily found in the cache file, whose default
location is /tmp/ansible-digital_ocean.cache).

The --pretty (-p) option pretty-prints the output for better human readability.

----
Although the cache stores all the information received from DigitalOcean,
the cache is not used for current droplet information (in --list, --host,
--all, and --droplets).  This is so that accurate droplet information is always
found.  You can force this script to use the cache with --force-cache.

----
Configuration is read from `digital_ocean.ini`, then from environment variables,
then and command-line arguments.

Most notably, the DigitalOcean API Token must be specified. It can be specified
in the INI file or with the following environment variables:
    export DO_API_TOKEN='abc123' or
    export DO_API_KEY='abc123'

Alternatively, it can be passed on the command-line with --api-token.

If you specify DigitalOcean credentials in the INI file, a handy way to
get them into your environment (e.g., to use the digital_ocean module)
is to use the output of the --env option with export:
    export $(digital_ocean.py --env)

----
The following groups are generated from --list:
 - ID    (droplet ID)
 - NAME  (droplet NAME)
 - image_ID
 - image_NAME
 - distro_NAME  (distribution NAME from image)
 - region_NAME
 - size_NAME
 - status_STATUS

When run against a specific host, this script returns the following variables:
 - do_backup_ids
 - do_created_at
 - do_disk
 - do_features - list
 - do_id
 - do_image - object
 - do_ip_address
 - do_private_ip_address
 - do_kernel - object
 - do_locked
 - de_memory
 - do_name
 - do_networks - object
 - do_next_backup_window
 - do_region - object
 - do_size - object
 - do_size_slug
 - do_snapshot_ids - list
 - do_status
 - do_vcpus

-----
```
usage: digital_ocean.py [-h] [--list] [--host HOST] [--all]
                                 [--droplets] [--regions] [--images] [--sizes]
                                 [--ssh-keys] [--domains] [--pretty]
                                 [--cache-path CACHE_PATH]
                                 [--cache-max_age CACHE_MAX_AGE]
                                 [--force-cache]
                                 [--refresh-cache]
                                 [--api-token API_TOKEN]

Produce an Ansible Inventory file based on DigitalOcean credentials

optional arguments:
  -h, --help            show this help message and exit
  --list                List all active Droplets as Ansible inventory
                        (default: True)
  --host HOST           Get all Ansible inventory variables about a specific
                        Droplet
  --all                 List all DigitalOcean information as JSON
  --droplets            List Droplets as JSON
  --regions             List Regions as JSON
  --images              List Images as JSON
  --sizes               List Sizes as JSON
  --ssh-keys            List SSH keys as JSON
  --domains             List Domains as JSON
  --pretty, -p          Pretty-print results
  --cache-path CACHE_PATH
                        Path to the cache files (default: .)
  --cache-max_age CACHE_MAX_AGE
                        Maximum age of the cached items (default: 0)
  --force-cache         Only use data from the cache
  --refresh-cache       Force refresh of cache by making API requests to
                        DigitalOcean (default: False - use cache files)
  --api-token API_TOKEN, -a API_TOKEN
                        DigitalOcean API Token
```

'''

# (c) 2013, Evan Wies <evan@neomantra.net>
#
# Inspired by the EC2 inventory plugin:
# https://github.com/ansible/ansible/blob/devel/contrib/inventory/ec2.py
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

import os
import sys
import re
import argparse
from time import time
import ConfigParser
import ast

try:
    import json
except ImportError:
    import simplejson as json

try:
    from dopy.manager import DoManager
except ImportError as e:
    print("failed=True msg='`dopy` library required for this script'")
    sys.exit(1)



class DigitalOceanInventory(object):

    ###########################################################################
    # Main execution path
    ###########################################################################

    def __init__(self):
        ''' Main execution path '''

        # DigitalOceanInventory data
        self.data = {}      # All DigitalOcean data
        self.inventory = {} # Ansible Inventory

        # Define defaults
        self.cache_path = '.'
        self.cache_max_age = 0
        self.use_private_network = False
        self.group_variables = {}

        # Read settings, environment variables, and CLI arguments
        self.read_settings()
        self.read_environment()
        self.read_cli_args()

        # Verify credentials were set
        if not hasattr(self, 'api_token'):
            print('''Could not find values for DigitalOcean api_token.
They must be specified via either ini file, command line argument (--api-token),
or environment variables (DO_API_TOKEN)''')
            sys.exit(-1)

        # env command, show DigitalOcean credentials
        if self.args.env:
            print("DO_API_TOKEN=%s" % self.api_token)
            sys.exit(0)

        # Manage cache
        self.cache_filename = self.cache_path + "/ansible-digital_ocean.cache"
        self.cache_refreshed = False

        if self.is_cache_valid:
            self.load_from_cache()
            if len(self.data) == 0:
                if self.args.force_cache:
                    print('''Cache is empty and --force-cache was specified''')
                    sys.exit(-1)

        self.manager = DoManager(None, self.api_token, api_version=2)

        # Pick the json_data to print based on the CLI command
        if self.args.droplets:
            self.load_from_digital_ocean('droplets')
            json_data = {'droplets': self.data['droplets']}
        elif self.args.regions:
            self.load_from_digital_ocean('regions')
            json_data = {'regions': self.data['regions']}
        elif self.args.images:
            self.load_from_digital_ocean('images')
            json_data = {'images': self.data['images']}
        elif self.args.sizes:
            self.load_from_digital_ocean('sizes')
            json_data = {'sizes': self.data['sizes']}
        elif self.args.ssh_keys:
            self.load_from_digital_ocean('ssh_keys')
            json_data = {'ssh_keys': self.data['ssh_keys']}
        elif self.args.domains:
            self.load_from_digital_ocean('domains')
            json_data = {'domains': self.data['domains']}
        elif self.args.all:
            self.load_from_digital_ocean()
            json_data = self.data
        elif self.args.host:
            json_data = self.load_droplet_variables_for_host()
        else:    # '--list' this is last to make it default
            self.load_from_digital_ocean('droplets')
            self.build_inventory()
            json_data = self.inventory

        if self.cache_refreshed:
            self.write_to_cache()

        if self.args.pretty:
            print(json.dumps(json_data, sort_keys=True, indent=2))
        else:
            print(json.dumps(json_data))
        # That's all she wrote...


    ###########################################################################
    # Script configuration
    ###########################################################################

    def read_settings(self):
        ''' Reads the settings from the digital_ocean.ini file '''
        config = ConfigParser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/digital_ocean.ini')

        # Credentials
        if config.has_option('digital_ocean', 'api_token'):
            self.api_token = config.get('digital_ocean', 'api_token')

        # Cache related
        if config.has_option('digital_ocean', 'cache_path'):
            self.cache_path = config.get('digital_ocean', 'cache_path')
        if config.has_option('digital_ocean', 'cache_max_age'):
            self.cache_max_age = config.getint('digital_ocean', 'cache_max_age')

        # Private IP Address
        if config.has_option('digital_ocean', 'use_private_network'):
            self.use_private_network = config.get('digital_ocean', 'use_private_network')

        # Group variables
        if config.has_option('digital_ocean', 'group_variables'):
            self.group_variables = ast.literal_eval(config.get('digital_ocean', 'group_variables'))

    def read_environment(self):
        ''' Reads the settings from environment variables '''
        # Setup credentials
        if os.getenv("DO_API_TOKEN"):
            self.api_token = os.getenv("DO_API_TOKEN")
        if os.getenv("DO_API_KEY"):
            self.api_token = os.getenv("DO_API_KEY")


    def read_cli_args(self):
        ''' Command line argument processing '''
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on DigitalOcean credentials')

        parser.add_argument('--list', action='store_true', help='List all active Droplets as Ansible inventory (default: True)')
        parser.add_argument('--host', action='store', help='Get all Ansible inventory variables about a specific Droplet')

        parser.add_argument('--all', action='store_true', help='List all DigitalOcean information as JSON')
        parser.add_argument('--droplets','-d', action='store_true', help='List Droplets as JSON')
        parser.add_argument('--regions', action='store_true', help='List Regions as JSON')
        parser.add_argument('--images', action='store_true', help='List Images as JSON')
        parser.add_argument('--sizes', action='store_true', help='List Sizes as JSON')
        parser.add_argument('--ssh-keys', action='store_true', help='List SSH keys as JSON')
        parser.add_argument('--domains', action='store_true',help='List Domains as JSON')

        parser.add_argument('--pretty','-p', action='store_true', help='Pretty-print results')

        parser.add_argument('--cache-path', action='store', help='Path to the cache files (default: .)')
        parser.add_argument('--cache-max_age', action='store', help='Maximum age of the cached items (default: 0)')
        parser.add_argument('--force-cache', action='store_true', default=False, help='Only use data from the cache')
        parser.add_argument('--refresh-cache','-r', action='store_true', default=False,
                            help='Force refresh of cache by making API requests to DigitalOcean (default: False - use cache files)')

        parser.add_argument('--env','-e', action='store_true', help='Display DO_API_TOKEN')
        parser.add_argument('--api-token','-a', action='store', help='DigitalOcean API Token')

        self.args = parser.parse_args()

        if self.args.api_token:
            self.api_token = self.args.api_token

        # Make --list default if none of the other commands are specified
        if (not self.args.droplets and not self.args.regions and
                not self.args.images and not self.args.sizes and
                not self.args.ssh_keys and not self.args.domains and
                not self.args.all and not self.args.host):
            self.args.list = True


    ###########################################################################
    # Data Management
    ###########################################################################

    def load_from_digital_ocean(self, resource=None):
        '''Get JSON from DigitalOcean API'''
        if self.args.force_cache:
            return
        # We always get fresh droplets
        if self.is_cache_valid() and not (resource=='droplets' or resource is None):
            return
        if self.args.refresh_cache:
            resource=None

        if resource == 'droplets' or resource is None:
            self.data['droplets'] = self.manager.all_active_droplets()
            self.cache_refreshed = True
        if resource == 'regions' or resource is None:
            self.data['regions'] = self.manager.all_regions()
            self.cache_refreshed = True
        if resource == 'images' or resource is None:
            self.data['images'] = self.manager.all_images(filter=None)
            self.cache_refreshed = True
        if resource == 'sizes' or resource is None:
            self.data['sizes'] = self.manager.sizes()
            self.cache_refreshed = True
        if resource == 'ssh_keys' or resource is None:
            self.data['ssh_keys'] = self.manager.all_ssh_keys()
            self.cache_refreshed = True
        if resource == 'domains' or resource is None:
            self.data['domains'] = self.manager.all_domains()
            self.cache_refreshed = True


    def build_inventory(self):
        '''Build Ansible inventory of droplets'''
        self.inventory = {
                            'all': {
                                    'hosts': [],
                                    'vars': self.group_variables
                                   },
                            '_meta': {'hostvars': {}}
                        }

        # add all droplets by id and name
        for droplet in self.data['droplets']:
            #when using private_networking, the API reports the private one in "ip_address".
            if 'private_networking' in droplet['features'] and not self.use_private_network:
                for net in droplet['networks']['v4']:
                    if net['type']=='public':
                        dest=net['ip_address']
                    else:
                        continue
            else:
                dest = droplet['ip_address']

            self.inventory['all']['hosts'].append(dest)

            self.inventory[droplet['id']] = [dest]
            self.inventory[droplet['name']] = [dest]

            # groups that are always present
            for group in [
                            'region_' + droplet['region']['slug'],
                            'image_' + str(droplet['image']['id']),
                            'size_' + droplet['size']['slug'],
                            'distro_' + self.to_safe(droplet['image']['distribution']),
                            'status_' + droplet['status'],

                        ]:
                if group not in self.inventory:
                    self.inventory[group] = { 'hosts': [ ], 'vars': {} }
                self.inventory[group]['hosts'].append(dest)

            # groups that are not always present
            for group in [
                            droplet['image']['slug'],
                            droplet['image']['name']
                         ]:
                if group:
                    image = 'image_' + self.to_safe(group)
                    if image not in self.inventory:
                        self.inventory[image] = { 'hosts': [ ], 'vars': {} }
                    self.inventory[image]['hosts'].append(dest)



    def load_droplet_variables_for_host(self):
        '''Generate a JSON response to a --host call'''
        host = int(self.args.host)

        droplet = self.manager.show_droplet(host)

        # Put all the information in a 'do_' namespace
        info = {}
        for k, v in droplet.items():
            info['do_'+k] = v

        return {'droplet': info}



    ###########################################################################
    # Cache Management
    ###########################################################################

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''
        if os.path.isfile(self.cache_filename):
            mod_time = os.path.getmtime(self.cache_filename)
            current_time = time()
            if (mod_time + self.cache_max_age) > current_time:
                return True
        return False


    def load_from_cache(self):
        ''' Reads the data from the cache file and assigns it to member variables as Python Objects'''
        try:
            cache = open(self.cache_filename, 'r')
            json_data = cache.read()
            cache.close()
            data = json.loads(json_data)
        except IOError:
            data = {'data': {}, 'inventory': {}}

        self.data = data['data']
        self.inventory = data['inventory']


    def write_to_cache(self):
        ''' Writes data in JSON format to a file '''
        data = { 'data': self.data, 'inventory': self.inventory }
        json_data = json.dumps(data, sort_keys=True, indent=2)

        cache = open(self.cache_filename, 'w')
        cache.write(json_data)
        cache.close()


    ###########################################################################
    # Utilities
    ###########################################################################

    def push(self, my_dict, key, element):
        ''' Pushed an element onto an array that may not have been defined in the dict '''
        if key in my_dict:
            my_dict[key].append(element)
        else:
            my_dict[key] = [element]


    def to_safe(self, word):
        ''' Converts 'bad' characters in a string to underscores so they can be used as Ansible groups '''
        return re.sub("[^A-Za-z0-9\-\.]", "_", word)



###########################################################################
# Run the script
DigitalOceanInventory()
