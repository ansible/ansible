#!/usr/bin/env python
#
# (c) 2015, Prakritish Sen Eshore
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

'''
MongoDB external inventory script
=================================
Generates inventory that Ansible can understand by making API request to
Mongo Database.
NOTE: This script also assumes there is an mongo.ini file alongside it.

Returns hosts and hostgroups from Mongo DB.

Following Fields are needed:
    * host
    * group

Other Fields non mandatory fields:
    * updated_at
    * created_at

All other fields will be used as Host Variables.

'''

import os
import argparse
try:
    import configparser
except ImportError:
    import ConfigParser
    configparser = ConfigParser
import json
import re

try:
    from pymongo import MongoClient
except ImportError:
    print("Error: pymongo is needed. Try something like: pip install pymongo")
    exit(1)

class MongoInventory(object):

    def read_settings(self):
        config = configparser.SafeConfigParser()
        config.read(os.path.dirname(os.path.realpath(__file__)) + '/mongo.ini')
        if config.has_option('mongo', 'database_uri'):
            self.mongo_database_uri = config.get('mongo', 'database_uri')

        if config.has_option('mongo', 'db'):
            self.mongo_db = config.get('mongo', 'db')

        if config.has_option('mongo', 'collection'):
            self.mongo_collection = config.get('mongo', 'collection')

    def read_cli(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', nargs=1)
        parser.add_argument('--list', action='store_true')
        self.options = parser.parse_args()

    def get_hosts(self):
        client = MongoClient(self.mongo_database_uri)
        db = client[self.mongo_db]
        collection = db[self.mongo_collection]
        host_groups = collection.find().distinct("group")
        for hostgroup in host_groups:
            self.result[hostgroup] = []
            for host in collection.find({"group" : hostgroup}):
                res = re.search('^(.*)\[(\d+):(\d+)\](.*)$', host['host'])
                if res:
                    pad = len(res.group(2))
                    for counter in range(int(res.group(2)), int(res.group(3)) + 1):
                        hostname = res.group(1) + str(counter).zfill(pad) + res.group(4)
                        self.result[hostgroup].append(hostname)
                        self.result['_meta']['hostvars'][hostname] = {}
                        for key, value in iter(host.items()):
                            if key in ('_id', 'host', 'group', 'updated_at', 'created_at'):
                                next
                            else:
                                self.result['_meta']['hostvars'][hostname][key] = value
                else:
                    self.result[hostgroup].append(host['host'])
                    self.result['_meta']['hostvars'][host['host']] = {}
                    for key, value in host.iteritems():
                        if key in ('_id', 'host', 'group', 'updated_at', 'created_at'):
                            next
                        else:
                            self.result['_meta']['hostvars'][host['host']][key] = value

    def __init__(self):

        self.defaultgroup = 'group_all'
        self.ndo_database_uri = None
        self.options = None

        self.read_settings()
        self.read_cli()

        self.result = {}
        self.result['_meta'] = {}
        self.result['_meta']['hostvars'] = {}

        if self.mongo_database_uri:
            self.get_hosts()
            if self.options.host:
                if self.options.host[0] in self.result['_meta']['hostvars']:
                    print(json.dumps(self.result['_meta']['hostvars'][self.options.host[0]]))
                else:
                    exit(1)
            elif self.options.list:
                print(json.dumps(self.result))
            else:
                print("usage: --list or --host HOSTNAME")
                exit(1)
        else:
            print("Error: Database configuration is missing. See mongo.ini.")
            exit(1)

MongoInventory()
