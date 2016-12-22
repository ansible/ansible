#!/usr/bin/env python
#
# Ansible inventory script based on puppetdb.
#
# Author: Jan Collijs
# Source: https://github.com/visibilityspots/ansible-puppet-inventory

import os
import argparse
from pypuppetdb import connect

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

try:
    import json
except ImportError:
    import simplejson as json


class PuppetDBInventory:
    """This class will generate a list of nodes based on puppetdb"""
    def __init__(self):
        self.read_settings()
        self.parse_cli_args()
        if self.args.list:
            data = self.get_host_list_based_on_environments()

            print(json.dumps(data))

    def read_settings(self):
        """Getting the settings out of the puppetdb.ini file"""
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
            self.puppetdb_server_port = config.get('server', 'port')
        else:
            raise ValueError('puppetdb.ini does not have a server - port param defined')

        if config.has_option('server', 'api_version'):
            self.puppetdb_api_version = config.get('server', 'api_version')
        else:
            raise ValueError('puppetdb.ini does not have a server - api_version param defined')

        if config.has_option('server', 'environments'):
            self.puppetdb_environments = config.get('server', 'environments').split()
        else:
            raise ValueError('puppetdb.ini does not have a server - environments param defined')

    def parse_cli_args(self):
        """Parsing the parameters given through the command line"""
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on puppetdb')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        self.args = parser.parse_args()

    def get_host_list_based_on_environments(self):
        """Getting the nodes out of puppetdb using api version 4 based on environments"""
        db = connect(host=self.puppetdb_server, port=self.puppetdb_server_port)
        inv = {}
        for env in self.puppetdb_environments:
            inv.update( { env: []})

            facts = db.facts('fqdn', environment=env)
            for fact in facts:
                inv[env].append(fact.value)

        return inv


def main():
    """Main class which initiates the whole script"""
    PuppetDBInventory()

if __name__ == '__main__':
    main()
