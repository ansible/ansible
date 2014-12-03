#!/usr/bin/env python

# (c) 2014, Sergei Antipov, 2GIS
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

"""
Chef Server external inventory script.
======================================

Returns hosts and environment groups from Chef Server
"""

import os, sys
import argparse
import ConfigParser
from time import time

try:
    import json
except:
    import simplejson as json

try:
    import chef
except:
    print >> sys.stderr, "Error: PyChef library must be installed: pip install pychef."
    sys.exit(1)

class ChefserverInventory(object):
    def __init__(self):
	"""Main execution path"""
	self.read_settings()
	self.parse_cli_args()
	api = self.get_chefserver_api()

	# Data to print
	if self.args.host:
	    data_to_print = self.json_format_dict(self.node_to_dict(self.get_instance(self.args.host)))
	else:
	    data_to_print = self.json_format_dict(self.get_instances(), True)

	print data_to_print

    def read_settings(self):
	"""Reads the settings from the chefserver.ini file"""
	config = ConfigParser.SafeConfigParser()
	chef_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'chefserver.ini')
	chef_ini_path = os.environ.get('CHEF_INI_PATH', chef_default_ini_path)
	config.read(chef_ini_path)

	self.server_url = config.get('chefserver', 'server_url')
	self.client_pem_path = config.get('chefserver', 'client_key_path')
	self.client_name = config.get('chefserver', 'node_name')

    def parse_cli_args(self):
	"""Command line argument processing"""
	parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Chef Server data')
	parser.add_argument('--list', action='store_true', default=True,
		     help='List instances in Chef Server (default: True)')
	parser.add_argument('--host', action='store',
		     help='Get all the variables about a specific node')
	self.args = parser.parse_args()

    def get_chefserver_api(self):
	"""Return Chef Server API object"""
	try:
	    api = chef.ChefAPI(self.server_url, self.client_pem_path, self.client_name)
	    return api
	except chef.ChefError, e:
	    print "Chef server API is down or check your credentials"
	    print
	    print e
	    sys.exit(1)

    def get_instances(self):
	"""Group all instances by environment name"""
	groups = {}
	meta = {}
	meta["hostvars"] = {}

	for node in chef.Search('node', '*:*'):
	    name = node["name"]

	    meta["hostvars"][name] = self.node_to_dict(name)

	    environment = node["chef_environment"]
	    if groups.has_key(environment):
		groups[environment].append(name)
	    else:
		groups[environment] = [name]

	groups["_meta"] = meta

	return groups

    def get_instance(self, node_name):
	"""Return chef node object"""
	for node in chef.Search('node', "name:{0}".format(node_name)):
	    return node

    def node_to_dict(self, instance):
	if instance is None:
	    return {}

	node = self.get_instance(instance)
	return {
	    "chef_environment": node["chef_environment"],
	    "automatic": node["automatic"],
	    "normal": node["normal"],
	    "default": node["default"],
	    "override": node["override"],
	    "run_list": node["run_list"]
	}

    def json_format_dict(self, data, pretty=False):
	"""Converts a dict to a JSON object and dumps it as a formatted string."""
	if pretty:
	    return json.dumps(data, sort_keys=True, indent=2)
	else:
	    return json.dumps(data)

ChefserverInventory()
