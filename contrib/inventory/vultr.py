#!/usr/bin/env python
# Copyright 2016 422long.
#
# This file is part of Ansible
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

"""
Vultr.com external inventory script
==================================

Generates inventory that Ansible can understand by making API requests to Vultr.com via the requests
library. Hence, such dependency must be installed in the system to run this script.

The default configuration file is named 'vultr.ini' and is located alongside this script. You can
choose any other file by setting the VULTR_INI_PATH environment variable.

The following variables are established for every host. They can be retrieved from the hostvars
dictionary.
 - vultr_os
 - vultr_vcpu_count
 - vultr_ram
 - vultr_disk
 - vultr_status
 - vultr_main_ip
 - vultr_power_status
 - vultr_server_state
 - vultr_internal_ip
 - vultr_netmask_v4
 - vultr_gateway_v4
 - vultr_location
 - vultr_v6_network
 - vultr_v6_main_ip
 - vultr_v6_network_size
 - vultr_auto_backups
 - vultr_SUBID
 - vultr_DCID

Instances are grouped by the following categories:
 - vultr:
   A group containing all hosts
 - tag:
   A group is created for each tag. E.g. groups 'tag_foo' and 'tag_bar' are created if there exist
   instances with tags 'foo' or 'bar'.
 - location:
   A group is created for each location. E.g. group 'location_Chicago' is created if a server resides
   in Chicago.

Examples:
  Execute uname on all instances in location 'Chicago'
  $ ansible -i vultr.py location_Chicago -m shell -a "/bin/uname -a"

  Install nginx on all Red Hat web servers tagged with 'www'
  $ ansible -i vultr.py tag_www -m yum -a "name=nginx state=present"

  Run site.yml playbook on web servers
  $ ansible-playbook -i vultr.py site.yml -l tag_www

Support:
  This script is tested on Python 2.7 and 3.4. It may work on other versions though.

Author: Keth Resar <Keith.Resar@422long.com>
Version: 0.1
"""


import sys
import os

class VultrApiException(Exception):
    pass

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser

try:
    import json
except ImportError:
    import simplejson as json

try:
    import requests
except:
    sys.exit('Vultr.com inventory script requires requests. See http://docs.python-requests.org/en/master/')


class VultrInventory:

    _API_ENDPOINT = 'https://api.vultr.com'

    def __init__(self):
        self._configure_from_file()
        self.inventory = self.get_inventory()

    def _configure_from_file(self):
        """Initialize from .ini file.

        Configuration file is assumed to be named 'vultr.ini' and to be located on the same
        directory than this file, unless the environment variable BROOK_INI_PATH says otherwise.
        """

        vultr_ini_default_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), 'vultr.ini')
        vultr_ini_path = os.environ.get('VULTR_INI_PATH', vultr_ini_default_path)

        config = ConfigParser(defaults={
            'api_token': '',
        })
        config.read(vultr_ini_path)
        self.api_token = config.get('vultr', 'api_token')

        if not self.api_token:
            print('You must provide (at least) your Vultr.com API token to generate the dynamic '
                  'inventory.')
            sys.exit(1)


    def get_inventory(self):
        """Generate Ansible inventory.
        """

        groups = { 'vultr': [], '_meta': { 'hostvars': { } } }

        r = requests.get('%s/v1/server/list' % self._API_ENDPOINT, headers={ 'API-Key': self.api_token })

        if r.status_code != 200:  raise(VultrApiException("Error listing servers"))


        # Build inventory from instances in all projects
        #
        for server in r.json().values():
            groups['vultr'].append(server['label'])

            if not len(server['tag']):  pass
            if 'tag_'+server['tag'] not in groups:  groups['tag_'+server['tag']] = [server['label']]
            else:  groups['tag_'+server['tag']].append(server['label'])

            if server['location'] not in groups:  groups[server['location']] = [server['label']]
            else:  groups[server['location']].append(server['label'])

            groups['_meta']['hostvars'][server['label']] = {}
            for key in ('SUBID','os','ram','disk','vcpu_count','location','DCID','status','netmask_v4','gateway_v4','main_ip',
                        'power_status','server_state','v6_main_ip','v6_network_size','v6_network','internal_ip','auto_backups'):
                groups['_meta']['hostvars'][server['label']]['vultr_'+key] = server[key]

            groups['_meta']['hostvars'][server['label']]['ansible_ssh_host'] = server['main_ip']
            groups['_meta']['hostvars'][server['label']]['ansible_host'] = server['main_ip']

            if len(server['internal_ip']): groups['_meta']['hostvars'][server['label']]['private_ip'] = server['internal_ip']

        return(groups) 



# Run the script
#
vultr = VultrInventory()
print(json.dumps(vultr.inventory))
