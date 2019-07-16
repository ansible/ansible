#!/usr/bin/env python

# (c) 2016, Julian Barnett <jbarnett@tableau.com>
#
# This file is part of Ansible.
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

'''
MDT external inventory script
=================================
author: J Barnett 06/23/2016 01:15
maintainer: J Barnett (github @jbarnett1981)
'''

import argparse
import json
import pymssql
from ansible.module_utils.six.moves import configparser


class MDTInventory(object):

    def __init__(self):
        ''' Main execution path '''
        self.conn = None

        # Initialize empty inventory
        self.inventory = self._empty_inventory()

        # Read CLI arguments
        self.read_settings()
        self.parse_cli_args()

        # Get Hosts
        if self.args.list:
            self.get_hosts()

        # Get specific host vars
        if self.args.host:
            self.get_hosts(self.args.host)

    def _connect(self, query):
        '''
        Connect to MDT and dump contents of dbo.ComputerIdentity database
        '''
        if not self.conn:
            self.conn = pymssql.connect(server=self.mdt_server + "\\" + self.mdt_instance, user=self.mdt_user, password=self.mdt_password,
                                        database=self.mdt_database)
            cursor = self.conn.cursor()
            cursor.execute(query)
            self.mdt_dump = cursor.fetchall()
            self.conn.close()

    def get_hosts(self, hostname=False):
        '''
        Gets host from MDT Database
        '''
        if hostname:
            query = ("SELECT t1.ID, t1.Description, t1.MacAddress, t2.Role "
                     "FROM ComputerIdentity as t1 join Settings_Roles as t2 on t1.ID = t2.ID where t1.Description = '%s'" % hostname)
        else:
            query = 'SELECT t1.ID, t1.Description, t1.MacAddress, t2.Role FROM ComputerIdentity as t1 join Settings_Roles as t2 on t1.ID = t2.ID'
        self._connect(query)

        # Configure to group name configured in Ansible Tower for this inventory
        groupname = self.mdt_groupname

        # Initialize empty host list
        hostlist = []

        # Parse through db dump and populate inventory
        for hosts in self.mdt_dump:
            self.inventory['_meta']['hostvars'][hosts[1]] = {'id': hosts[0], 'name': hosts[1], 'mac': hosts[2], 'role': hosts[3]}
            hostlist.append(hosts[1])
        self.inventory[groupname] = hostlist

        # Print it all out
        print(json.dumps(self.inventory, indent=2))

    def _empty_inventory(self):
        '''
        Create empty inventory dictionary
        '''
        return {"_meta": {"hostvars": {}}}

    def read_settings(self):
        '''
        Reads the settings from the mdt.ini file
        '''
        config = configparser.SafeConfigParser()
        config.read('mdt.ini')

        # MDT Server and instance and database
        self.mdt_server = config.get('mdt', 'server')
        self.mdt_instance = config.get('mdt', 'instance')
        self.mdt_database = config.get('mdt', 'database')

        # MDT Login credentials
        if config.has_option('mdt', 'user'):
            self.mdt_user = config.get('mdt', 'user')
        if config.has_option('mdt', 'password'):
            self.mdt_password = config.get('mdt', 'password')

        # Group name in Tower
        if config.has_option('tower', 'groupname'):
            self.mdt_groupname = config.get('tower', 'groupname')

    def parse_cli_args(self):
        '''
        Command line argument processing
        '''
        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on MDT')
        parser.add_argument('--list', action='store_true', default=False, help='List instances')
        parser.add_argument('--host', action='store', help='Get all the variables about a specific instance')
        self.args = parser.parse_args()


if __name__ == "__main__":
    # Run the script
    MDTInventory()
