#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
External inventory script for Abiquo
====================================

Shamelessly copied from an existing inventory script.

This script generates an inventory that Ansible can understand by making API requests to Abiquo API
Requires some python libraries, ensure to have them installed when using this script.

This script has been tested in Abiquo 3.0 but it may work also for Abiquo 2.6.

Before using this script you may want to modify abiquo.ini config file.

This script generates an Ansible hosts file with these host groups:

ABQ_xxx: Defines a hosts itself by Abiquo VM name label
all: Contains all hosts defined in Abiquo user's enterprise
virtualdatecenter: Creates a host group for each virtualdatacenter containing all hosts defined on it
virtualappliance: Creates a host group for each virtualappliance containing all hosts defined on it
imagetemplate: Creates a host group for each image template containing all hosts using it

'''

# (c) 2014, Daniel Beneyto <daniel.beneyto@abiquo.com>
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

import os
import sys
import time

import json

from ansible.module_utils.six.moves import configparser as ConfigParser
from ansible.module_utils.urls import open_url


def api_get(link, config):
    try:
        if link is None:
            url = config.get('api', 'uri') + config.get('api', 'login_path')
            headers = {"Accept": config.get('api', 'login_type')}
        else:
            url = link['href'] + '?limit=0'
            headers = {"Accept": link['type']}
        result = open_url(url, headers=headers, url_username=config.get('auth', 'apiuser').replace('\n', ''),
                          url_password=config.get('auth', 'apipass').replace('\n', ''))
        return json.loads(result.read())
    except Exception:
        return None


def save_cache(data, config):
    ''' saves item to cache '''
    dpath = config.get('cache', 'cache_dir')
    try:
        cache = open('/'.join([dpath, 'inventory']), 'w')
        cache.write(json.dumps(data))
        cache.close()
    except IOError as e:
        pass  # not really sure what to do here


def get_cache(cache_item, config):
    ''' returns cached item  '''
    dpath = config.get('cache', 'cache_dir')
    inv = {}
    try:
        cache = open('/'.join([dpath, 'inventory']), 'r')
        inv = cache.read()
        cache.close()
    except IOError as e:
        pass  # not really sure what to do here

    return inv


def cache_available(config):
    ''' checks if we have a 'fresh' cache available for item requested '''

    if config.has_option('cache', 'cache_dir'):
        dpath = config.get('cache', 'cache_dir')

        try:
            existing = os.stat('/'.join([dpath, 'inventory']))
        except Exception:
            # cache doesn't exist or isn't accessible
            return False

        if config.has_option('cache', 'cache_max_age'):
            maxage = config.get('cache', 'cache_max_age')
            if (int(time.time()) - int(existing.st_mtime)) <= int(maxage):
                return True

    return False


def generate_inv_from_api(enterprise_entity, config):
    try:
        inventory['all'] = {}
        inventory['all']['children'] = []
        inventory['all']['hosts'] = []
        inventory['_meta'] = {}
        inventory['_meta']['hostvars'] = {}

        enterprise = api_get(enterprise_entity, config)
        vms_entity = next(link for link in enterprise['links'] if link['rel'] == 'virtualmachines')
        vms = api_get(vms_entity, config)
        for vmcollection in vms['collection']:
            for link in vmcollection['links']:
                if link['rel'] == 'virtualappliance':
                    vm_vapp = link['title'].replace('[', '').replace(']', '').replace(' ', '_')
                elif link['rel'] == 'virtualdatacenter':
                    vm_vdc = link['title'].replace('[', '').replace(']', '').replace(' ', '_')
                elif link['rel'] == 'virtualmachinetemplate':
                    vm_template = link['title'].replace('[', '').replace(']', '').replace(' ', '_')

            # From abiquo.ini: Only adding to inventory VMs with public IP
            if config.getboolean('defaults', 'public_ip_only') is True:
                for link in vmcollection['links']:
                    if link['type'] == 'application/vnd.abiquo.publicip+json' and link['rel'] == 'ip':
                        vm_nic = link['title']
                        break
                    else:
                        vm_nic = None
            # Otherwise, assigning defined network interface IP address
            else:
                for link in vmcollection['links']:
                    if link['rel'] == config.get('defaults', 'default_net_interface'):
                        vm_nic = link['title']
                        break
                    else:
                        vm_nic = None

            vm_state = True
            # From abiquo.ini: Only adding to inventory VMs deployed
            if config.getboolean('defaults', 'deployed_only') is True and vmcollection['state'] == 'NOT_ALLOCATED':
                vm_state = False

            if vm_nic is not None and vm_state:
                if vm_vapp not in inventory:
                    inventory[vm_vapp] = {}
                    inventory[vm_vapp]['children'] = []
                    inventory[vm_vapp]['hosts'] = []
                if vm_vdc not in inventory:
                    inventory[vm_vdc] = {}
                    inventory[vm_vdc]['hosts'] = []
                    inventory[vm_vdc]['children'] = []
                if vm_template not in inventory:
                    inventory[vm_template] = {}
                    inventory[vm_template]['children'] = []
                    inventory[vm_template]['hosts'] = []
                if config.getboolean('defaults', 'get_metadata') is True:
                    meta_entity = next(link for link in vmcollection['links'] if link['rel'] == 'metadata')
                    try:
                        metadata = api_get(meta_entity, config)
                        if (config.getfloat("api", "version") >= 3.0):
                            vm_metadata = metadata['metadata']
                        else:
                            vm_metadata = metadata['metadata']['metadata']
                        inventory['_meta']['hostvars'][vm_nic] = vm_metadata
                    except Exception as e:
                        pass

                inventory[vm_vapp]['children'].append(vmcollection['name'])
                inventory[vm_vdc]['children'].append(vmcollection['name'])
                inventory[vm_template]['children'].append(vmcollection['name'])
                inventory['all']['children'].append(vmcollection['name'])
                inventory[vmcollection['name']] = []
                inventory[vmcollection['name']].append(vm_nic)

        return inventory
    except Exception as e:
        # Return empty hosts output
        return {'all': {'hosts': []}, '_meta': {'hostvars': {}}}


def get_inventory(enterprise, config):
    ''' Reads the inventory from cache or Abiquo api '''

    if cache_available(config):
        inv = get_cache('inventory', config)
    else:
        default_group = os.path.basename(sys.argv[0]).rstrip('.py')
        # MAKE ABIQUO API CALLS #
        inv = generate_inv_from_api(enterprise, config)

    save_cache(inv, config)
    return json.dumps(inv)


if __name__ == '__main__':
    inventory = {}
    enterprise = {}

    # Read config
    config = ConfigParser.SafeConfigParser()
    for configfilename in [os.path.abspath(sys.argv[0]).rstrip('.py') + '.ini', 'abiquo.ini']:
        if os.path.exists(configfilename):
            config.read(configfilename)
            break

    try:
        login = api_get(None, config)
        enterprise = next(link for link in login['links'] if link['rel'] == 'enterprise')
    except Exception as e:
        enterprise = None

    if cache_available(config):
        inventory = get_cache('inventory', config)
    else:
        inventory = get_inventory(enterprise, config)

    # return to ansible
    sys.stdout.write(str(inventory))
    sys.stdout.flush()
