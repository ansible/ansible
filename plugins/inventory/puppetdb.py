#!/usr/bin/env python2
#
# Ansible inventory script based on puppetdb.
#
# Author: Jan Collijs
# Source: https://github.com/visibilityspots/ansible-puppet-inventory

# If you want to use the api version 4 you have to install the pypuppetdb
# library made by https://github.com/NeCTAR-RC/pypuppetdb from source untill
# it got merged https://github.com/puppet-community/pypuppetdb/pull/34

import sys
import os
import ConfigParser
import argparse
from pypuppetdb import connect
try:
        import json
except:
        import simplejson as json

''' This class will generate a list of nodes based on puppetdb '''
class PuppetDBInventory():
    def __init__(self):
        self.inventory = {}
        self.read_settings()
        self.parse_cli_args()
        if self.args.list:
            if self.puppetdb_api_version == '4':
                data = self.get_host_list_based_on_environments()
            else:
                data = self.get_host_list()

            print json.dumps(data)

    ''' Getting the settings out of the puppetdb.ini file '''
    def read_settings(self):
        config = ConfigParser.SafeConfigParser()
        puppetdb_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'puppetdb.ini')
        puppetdb_ini_path = os.environ.get('PUPPETDB_INI_PATH', puppetdb_default_ini_path)
        config.read(puppetdb_ini_path)

        if not config.has_section('server'):
            raise ValueError('puppetdb.ini file must contain a [server] section')

        if config.has_option('server', 'host'):
            self.puppetdb_server = config.get('server', 'host')
        else:
            raise ValueError('puppetdb.ini does not have a server - host param defined')

        if config.has_option('server', 'port'):
            self.puppetdb_server_port = config.get('server','port')
        else:
            raise ValueError('puppetdb.ini does not have a server - port param  defined')

        if config.has_option('server', 'api_version'):
            self.puppetdb_api_version = config.get('server','api_version')
        else:
            raise ValueError('puppetdb.ini does not have a server - api_version param defined')

        if config.has_option('server', 'environments'):
            self.puppetdb_environments = config.get('server','environments').split()
        else:
            raise ValueError('puppetdb.ini does not have a server - environments param defined')

    ''' Parsing the parameters given through the commond line '''
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on puppetdb')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        self.args = parser.parse_args()

    ''' Getting all the nodes out of puppetdb based on the api version 3 '''
    def get_host_list(self):
        db = connect(api_version=3, host=self.puppetdb_server, port=self.puppetdb_server_port)
        nodes = db.nodes()
        inv = { 'all': []}
        for node in nodes:
            inv['all'].append(node.name)

        return inv

    ''' Getting the nodes out of puppetdb based on the expirimental api 4 based on environments '''
    def get_host_list_based_on_environments(self):
        db = connect(api_version=4, host=self.puppetdb_server, port=self.puppetdb_server_port)
        json_data_toReturn = ''
        inv = {}
        for env in self.puppetdb_environments:
            inv.update( { env: [] })

            facts = db.facts('fqdn', environment=env)
            for fact in facts:
                inv[env].append(fact.value)

        return inv

''' Main class which initiates the whole script'''
def main():
    PuppetDBInventory()

if __name__ == '__main__':
    main()
