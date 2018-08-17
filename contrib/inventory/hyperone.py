#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from time import time

import requests
import os
import sys
import argparse
import json

try:
    import ConfigParser as configparser
except ImportError:
    import configparser
'''
External inventory script for HyperOne
====================================

Contains parts shamelessly copied from an existing inventory script.

Generates an inventory that Ansible can understand by making API requests
to HyperOne API. Each VM tag match Ansible host group.

Before using this script you need create  hyperone.ini config file and put
token to access service.

To generate token you can use h1-cli and following commands:

$ TOKEN_ID=$(h1 project token add --name ansible-inventory --query "[0]._id" -o json);
$ h1 project token access delete --token $TOKEN_ID --yes \
    --access $(h1 project token access list --token $TOKEN_ID -o tsv --query "[].[_id]" );
$ h1 project token access add --token $TOKEN_ID --method GET --path '/vm'
$ echo "Token ID: $TOKEN_ID";

Example config file:

    [hyperone]
    token=$TOKEN_ID
    cache_path=~/.cache/hyperone
'''


class HyperOneAPI(object):
    def __init__(self, token):
        self.session = requests.Session()
        self.session.headers = {'X-Auth-Token': token}

    def get_vms(self):
        return self.session.get('https://api.hyperone.com/v1/vm').json()

    def get_vm(self, vm_id):
        return self.session.get("https://api.hyperone.com/v1/vm/{vm_id}".format(vm_id=vm_id)).json()

    def get_vm_netadp(self, vm_id):
        return self.session.get("https://api.hyperone.com/v1/vm/{vm_id}/netadp".format(vm_id=vm_id)).json()


class FileCache(object):
    def __init__(self, filename, max_age):
        self.file = filename
        self.max_age = max_age

    def is_valid(self):
        if os.path.isfile(self.file):
            mod_time = os.path.getmtime(self.file)
            current_time = time()
            if (mod_time + self.max_age) > current_time:
                if os.path.isfile(self.file):
                    return True
        return False

    def get(self):
        with open(self.file, 'r') as fp:
            return json.load(fp)

    def save(self, data):
        with open(self.file, 'w') as fp:
            return json.dump(data, fp, sort_keys=True, indent=2)


class HyperOneInventory(object):
    def read_settings(self):
        config = configparser.SafeConfigParser()
        conf_path = './hyperone.ini'
        if os.path.exists(conf_path):
            config.read(conf_path)
        else:
            print("Unable o read {0}".format(conf_path), file=sys.stderr)
        if config.has_option('hyperone', 'token'):
            self.token = config.get('hyperone', 'token')

        if config.has_option('hyperone', 'default_group'):
            self.default_group = config.get('hyperone', 'default_group')

        if config.has_option('hyperone', 'update_username'):
            self.update_username = config.getboolean('hyperone', 'update_username')

        if config.has_option('hyperone', 'connection_host'):
            self.connection_host = config.get('hyperone', 'connection_host')

        cache_path = os.path.expanduser(config.get('hyperone', 'cache_path'))
        self.cache_path_inventory = os.path.join(cache_path, "ansible-hyperone.cache")

        if not os.path.exists(cache_path):
            os.mkdir(cache_path)

        if config.has_option('hyperone', 'cache_max_age'):
            self.cache_max_age = config.getint('hyperone', 'cache_max_age')

    def read_env(self):
        if 'H1_INVENTORY_TOKEN' in os.environ:
            self.token = os.environ['H1_INVENTORY_TOKEN']

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on HyperOne')
        parser.add_argument('--list', action='store_true', default=False,
                            help='List VMs (default: True)')
        parser.add_argument('--host', action='store',
                            help='Get all the variables about a specific Virtual machine')
        parser.add_argument('--purge-cache', action='store_true', default=False,
                            help='Purge cache')
        return parser.parse_args()

    def push(self, my_dict, key, value):
        my_dict[key] = my_dict.get(key, []) + [value]

    def add_vm(self, vm):
        name = vm['name']

        self.inventory[vm['_id']] = [name, ]

        for tag in vm.get('tag', {}).keys() or [self.default_group]:
            self.push(self.inventory, tag, name)

        self.push(self.inventory, 'hyperone', name)

        hostvars = {'hyperone': vm}

        if vm['private_ips']:
            hostvars['private_ip'] = vm['private_ips'][0]

        if self.connection_host:
            if vm['private_ips'] and self.connection_host == 'private_ip':
                hostvars['ansible_ssh_host'] = vm["private_ips"][0]
                hostvars['ansible_host'] = vm["private_ips"][0]

            if vm['public_ips'] and (self.connection_host == 'public_ip' or not vm['private_ips']):
                hostvars['ansible_ssh_host'] = vm["public_ips"][0]
                hostvars['ansible_host'] = vm["public_ips"][0]

        if self.update_username:
            hostvars['ansible_ssh_user'] = vm.get('data', {}).get('username', 'guru')

        self.inventory["_meta"]["hostvars"][name] = hostvars

    def _get_ips(self, netadps, type='public'):
        return [ip['address']
                for netadp in netadps if netadp['network']['type'] == type
                for ip in netadp['ip']]

    def get_inventory(self):
        if self.cache.is_valid():
            return self.cache.get()

        vms = self.api.get_vms()
        for vm in vms:
            vm['netadps'] = self.api.get_vm_netadp(vm_id=vm['_id'])
            vm['public_ips'] = self._get_ips(vm['netadps'])
            vm['private_ips'] = self._get_ips(vm['netadps'], 'private')
            vm['ips'] = vm['private_ips'] + vm['public_ips']
            self.add_vm(vm)
        self.cache.save(self.inventory)
        return self.inventory

    def __init__(self):

        self.token = None
        self.connection_host = None
        self.default_group = 'hyperone_untagged'
        self.cache_path_inventory = None
        self.cache_max_age = 60 * 60
        self.update_username = False
        self.read_settings()
        self.read_env()
        self.cache = FileCache(self.cache_path_inventory, self.cache_max_age)
        self.inventory = {'_meta': {'hostvars': {}}}

        options = self.parse_cli_args()

        if self.token:
            self.api = HyperOneAPI(self.token)

            if options.list:
                print(json.dumps(self.get_inventory(), indent=2))

            elif options.host:
                host = self.get_inventory()['_meta']['hostvars'][options.host]
                print(json.dumps(host, indent=2))

            elif options.purge_cache:
                os.unlink(self.cache_path_inventory)
                print("Cache purged!")

            else:
                print("usage: --list  ..OR.. --host <hostname> ..OR.. --purge-cache", file=sys.stderr)
                sys.exit(1)

        else:
            print("Error: Configuration of toekn are required. See hyperone.ini.")
            sys.exit(1)


HyperOneInventory()
