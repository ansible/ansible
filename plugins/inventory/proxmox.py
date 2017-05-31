#!/usr/bin/env python

# (c) 2014, Sergei Antipov <s.antipov@2gis.ru>, 2GIS
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
Ansible ProxmoxVE external inventory script.
======================================

Generates Ansible inventory from Proxmox Cluster.
Configuration is read from 'proxmox.ini'.
When run in --list mode, instances are grouped by the host system.

When run against a specific host, this script returns the following attributes
based on the data obtained from ProxmoxVE API:
    - vmid
    - status
    - type

usage: proxmox.py [--list] [--host HOST]
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
    from proxmoxer import ProxmoxAPI
except:
    print >> sys.stderr, "Error: Proxmoxer library must be installed: pip install proxmoxer."
    sys.exit(1)

class ProxmoxInventory(object):
    def __init__(self):
	"""Main execution path"""
	self.read_settings()
	self.parse_cli_args()
	self.api = self.get_proxmox_driver()

	# Data to print
	if self.args.host:
	    data_to_print = self.json_format_dict(self.node_to_dict(self.get_instance(self.args.host)))
	else:
	    data_to_print = self.json_format_dict(self.get_instances(), True)

	print data_to_print

    def read_settings(self):
	"""Reads the settings from the proxmox.ini file"""
	config = ConfigParser.RawConfigParser()
	proxmox_default_ini_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'proxmox.ini')
	proxmox_ini_path = os.environ.get('PROXMOX_INI_PATH', proxmox_default_ini_path)
	config.read(proxmox_ini_path)

	self.proxmox_host = config.get('proxmox', 'proxmox_host')
	self.user_name = config.get('proxmox', 'user_name')
	self.password = config.get('proxmox', 'password')

    def parse_cli_args(self):
	"""Command line argument processing"""
	parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on Proxmox Cluster data')
	parser.add_argument('--list', action='store_true', default=True,
		     help='List instances in Proxmox Cluster (default: True)')
	parser.add_argument('--host', action='store',
		     help='Get all the variables about a specific node')
	self.args = parser.parse_args()

    def get_proxmox_driver(self):
	"""Return Proxmox API object"""
	try:
	    api = ProxmoxAPI(self.proxmox_host, user=self.user_name, password=self.password, verify_ssl=False)
	    return api
	except Exception, e:
	    print "ProxmoxVE API is down or check your credentials"
	    print
	    print e
	    sys.exit(1)

    def get_instances(self):
	"""Group all instances by host node"""
	groups = {}
	meta = {}
	meta["hostvars"] = {}

	for node in self.api.nodes.get():
	    for vm in self.api.nodes(node["node"]).openvz.get():
		name = vm["name"]

		meta["hostvars"][name] = self.node_to_dict(vm)

		if groups.has_key(node["node"]):
		    groups[node["node"]].append(name)
		else:
		    groups[node["node"]] = [name]

	    for vm in self.api.nodes(node["node"]).qemu.get():
		name = vm["name"]

		meta["hostvars"][name] = self.node_to_dict(vm)

		if groups.has_key(node["node"]):
		    groups[node["node"]].append(name)
		else:
		    groups[node["node"]] = [name]

	groups["_meta"] = meta

	return groups

    def get_instance(self, node_name):
	"""Return chef node object"""
	for node in self.api.nodes.get():
	    for vm in self.api.nodes(node["node"]).openvz.get():
		if vm["name"] == node_name:
		  return vm
	    for vm in self.api.nodes(node["node"]).qemu.get():
		if vm["name"] == node_name:
		  return vm

    def node_to_dict(self, instance):
	if instance is None:
	    return {}

	metadata = {}

	metadata["status"] = instance["status"]
	metadata["vmid"] = instance["vmid"]
	if instance.has_key("type"):
	    metadata["type"] = instance["type"]
	else:
	    metadata["type"] = "qemu"

	return metadata

    def json_format_dict(self, data, pretty=False):
	"""Converts a dict to a JSON object and dumps it as a formatted string."""
	if pretty:
	    return json.dumps(data, sort_keys=True, indent=2)
	else:
	    return json.dumps(data)

ProxmoxInventory()
