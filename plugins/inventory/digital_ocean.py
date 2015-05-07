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

Most notably, the DigitalOcean Client ID and API Key must be specified.  They
can be specified in the INI file or with the following environment variables:
    export DO_CLIENT_ID='DO123' DO_API_KEY='abc123'

Alternatively, they can be passed on the command-line with --client-id and
--api-key.

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
 - region_ID
 - region_NAME
 - size_ID
 - size_NAME
 - status_STATUS

When run against a specific host, this script returns the following variables:
 - do_created_at
 - do_distroy
 - do_id
 - do_image
 - do_image_id
 - do_ip_address
 - do_name
 - do_region
 - do_region_id
 - do_size
 - do_size_id
 - do_status

-----
```
usage: digital_ocean.py [-h] [--list] [--host HOST] [--all]
                                 [--droplets] [--regions] [--images] [--sizes]
                                 [--ssh-keys] [--domains] [--pretty]
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
  --api-token API_TOKEN, -a API_TOKEN
                        DigitalOcean API Token
```

'''

# (c) 2013, Evan Wies <evan@neomantra.net>
#
# Inspired by the EC2 inventory plugin:
# https://github.com/ansible/ansible/blob/devel/plugins/inventory/ec2.py
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

try:
    import json
except ImportError:
    import simplejson as json

try:
    from dopy.manager import DoError, DoManager
except ImportError, e:
    print "failed=True msg='`dopy` library required for this script'"
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

        # Read settings, environment variables, and CLI arguments
        self.read_settings()
        self.read_environment()
        self.read_cli_args()

        # Verify credentials were set
        if not hasattr(self, 'api_token'):
            print '''Could not find values for DigitalOcean api_token.
They must be specified via either ini file, command line argument (--api-token),
or environment variables (DO_API_TOKEN)'''
            sys.exit(-1)

        # env command, show DigitalOcean credentials
        if self.args.env:
            print "DO_API_TOKEN=%s" % self.api_token
            sys.exit(0)

        self.manager = DoManager(None, self.api_token, api_version=2)

        # Pick the json_data to print based on the CLI command
        if self.args.droplets:
            json_data = self.load_from_digital_ocean('droplets')
        elif self.args.regions:
            json_data = self.load_from_digital_ocean('regions')
        elif self.args.images:
            json_data = self.load_from_digital_ocean('images')
        elif self.args.sizes:
            json_data = self.load_from_digital_ocean('sizes')
        elif self.args.ssh_keys:
            json_data = self.load_from_digital_ocean('ssh_keys')
        elif self.args.domains:
            json_data = self.load_from_digital_ocean('domains')
        elif self.args.all:
            json_data = self.load_from_digital_ocean()
        elif self.args.host:
            json_data = self.load_droplet_variables_for_host()
        else:    # '--list' this is last to make it default
            self.data = self.load_from_digital_ocean('droplets')
            self.build_inventory()
            json_data = self.inventory

        if self.args.pretty:
            print json.dumps(json_data, sort_keys=True, indent=2)
        else:
            print json.dumps(json_data)
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
        json_data = {}
        if resource == 'droplets' or resource is None:
            json_data['droplets'] = self.manager.all_active_droplets()
        if resource == 'regions' or resource is None:
            json_data['regions'] = self.manager.all_regions()
        if resource == 'images' or resource is None:
            json_data['images'] = self.manager.all_images(filter=None)
        if resource == 'sizes' or resource is None:
            json_data['sizes'] = self.manager.sizes()
        if resource == 'ssh_keys' or resource is None:
            json_data['ssh_keys'] = self.manager.all_ssh_keys()
        if resource == 'domains' or resource is None:
            json_data['domains'] = self.manager.all_domains()
        return json_data


    def build_inventory(self):
        '''Build Ansible inventory of droplets'''
        self.inventory = {}

        # add all droplets by id and name
        for droplet in self.data['droplets']:
            dest = droplet['ip_address']

            self.inventory[droplet['id']] = [dest]
            self.push(self.inventory, droplet['name'], dest)
            self.push(self.inventory, 'region_' + droplet['region']['slug'], dest)
            self.push(self.inventory, 'image_' + str(droplet['image']['id']), dest)
            self.push(self.inventory, 'size_' + droplet['size']['slug'], dest)

            image_slug = droplet['image']['slug']
            if image_slug:
                self.push(self.inventory, 'image_' + self.to_safe(image_slug), dest)
            else:
                image_name = droplet['image']['name']
                if image_name:
                    self.push(self.inventory, 'image_' + self.to_safe(image_name), dest)

            self.push(self.inventory, 'distro_' + self.to_safe(droplet['image']['distribution']), dest)
            self.push(self.inventory, 'status_' + droplet['status'], dest)


    def load_droplet_variables_for_host(self):
        '''Generate a JSON response to a --host call'''
        host = int(self.args.host)

        return self.manager.show_droplet(host)



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
