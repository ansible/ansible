#!/usr/bin/env python

'''
CloudAtCost external inventory script
=================================

Generates inventory that Ansible can understand by making API request to
CloutAtCost APIs.

NOTE: This script assumes Ansible is being executed where the environment
variables needed for Boto have already been set:
    export CAC_API_KEY='YOURAPIKEY'
    export CAC_LOGIN='your@email'
For more details, see: https://panel.cloudatcost.com/api-details.php

It's possible to define extra vars using the `Notes` section in CloudAtCost
panel. Unfortunately that field does not support new lines, but you can use
'__CAC__' as separator to specify multiple variables inline;
e.g.: ansible_user=myuser__CAC__ansible_var=foo bar__CAC__ansible_var2=baz
'''

import argparse
import os
import requests
import sys

try:
    import json
except ImportError:
    import simplejson as json

class CloudAtCostInventory(object):

    def __init__(self):
        ''' Main execution path '''
        self.inventory = {}

        # Parse CLI arguments
        self.parse_cli_args()

        # API key, get one from https://panel.cloudatcost.com/api-details.php
        self.api_key = os.environ.get('CAC_API_KEY')
        if not self.api_key:
            print ("Environment variable CAC_API_KEY is not set!")
            sys.exit(1)

        self.login = os.environ.get('CAC_LOGIN')
        if not self.login:
            print ("Environment variable CAC_LOGIN is not set!")
            sys.exit(1)

        if self.args.list:
            self.inventory = self.get_inventory()
        elif self.args.host:
            self.inventory = self.get_inventory()['_meta']['hostvars'][self.args.host]

        print (self.to_json(self.inventory))

    def get_inventory(self):
        ''' Reads the inventory and returns it as a JSON object '''
        inventory = {}
        inventory['all'] = {}
        inventory['all']['hosts'] = []
        inventory['all']['vars'] = {'ansible_user': 'root'}
        inventory['_meta'] = {'hostvars': {}}

        url = "https://panel.cloudatcost.com/api/v1/listservers.php?key={0}&login={1}".format(self.api_key, self.login)
        response = requests.get(url)

        if response.status_code is 200:
            for data in json.loads(response.text)['data']:
                if data['status'] == 'Powered On':
                    id = data['id']
                    inventory['all']['hosts'].append(id)
                    inventory['_meta']['hostvars'][id] = {}
                    inventory['_meta']['hostvars'][id]['ansible_host'] = data['ip']
                    inventory['_meta']['hostvars'][id]['ansible_password'] = data['rootpass']
                    for v in data['panel_note'].split('__CAC__'):
                        key = v.split('=')[0]
                        value = v.split('=')[1]
                        inventory['_meta']['hostvars'][id][key] = value
        else:
            print ("Cannot fetch server list!")
            sys.exit(1)

        return inventory

    def to_json(self, in_dict):
        return json.dumps(in_dict, sort_keys=True, indent=2)

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on CloudAtCost')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--list', action='store_true', help='List active servers')
        group.add_argument('--host', help='List details about the specific host')
        self.args = parser.parse_args()

# Run the script
CloudAtCostInventory()
