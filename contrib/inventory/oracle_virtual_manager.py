#!/usr/bin/env python

# (c) 2015, Dave Snigier <dsnigier@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

# Dynamic inventory script which pulls targets and variables from
# Oracle Virtual Manager's API. Results from OVM are cached to avoid
# sending too many requests to OVM. Default cache lifetime is one hour,
# but this is configurable. Delete the cache file named
# oracle_virtual_manager.py.cache to manually clear the cache.
#
# Targets are grouped by tag, the name of the VM in OVM is used
# as the target name.
#
# The following special groups are generated for you:
#     ovm_bad_name: Any targets named improperly (invalid hostname)
#     ovm: All VMs in OVM
#
# group_vars are prefixed with 'ovm_'. For instance: ovm_cpuCount, ovm_memory, ovm_osType
#
# Requires the following python modules:
#     pyyaml
#     requests
#     filecache 

# configuration is done in YAML format
###======= Start of Configuration =======###
config = """
# Base URL where the OVM API resides
url: https://<your.uri.here>:7002/ovm/core/wsapi/rest

# OVM user account information
user: <user>
password: <password>

# how long should we cache the output of the OVM server? (in seconds)
cache_lifetime: 3600

# properties which shouldn't be included as hostvars
ovm_property_blacklist:
  - affinityGroupIds
  - bootOrder
  - id
  - resourceGroupIds
  - virtualNicIds
  - vmDiskMappingIds
  - networkInstallPath
  - origin
  - vmCloneDefinitionIds

# properties which should use their name instead of the value of the key
use_name_instead:
  - repositoryId
  - serverPoolId
  - serverId
"""

### ======= End of Configuration =======###

import argparse, time, os.path, re, sys
import requests, json, yaml
from filecache import filecache

# TODO virtualNicIds --> uri lookup for network

# Use directory this script resides in to look for config and store caches
configuration = os.path.realpath(__file__) + '.conf'

conf = yaml.load(config)

# suppress stupid insecure warnings... our boxes don't have the proper certs
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings()


# let's parse some arguments
parser = argparse.ArgumentParser(description='Provides Ansible inventory from Oracle VM')
parser.add_argument('--list', action='store_true',  help='Outputs list of all groups')
parser.add_argument('--host', nargs=1, action='store', help='Outputs list of variables for a host')
parser.add_argument('--pretty', action='store_true', help='Outputs human readable json')
args = parser.parse_args()


# create session to ovm. waits until OVM is in a safe running state
# returns session object
def ovm_session(url, user, password):
	session=requests.session()
	session.auth=(user, password)
	session.headers.update({'Accept': 'application/json', 'Content-Type': 'application/json'})

	while True:
		res = session.get(conf['url'] + '/Manager', verify=False)
		res = res.json()
		ovm_state = res[0]['managerRunState']
		if ovm_state.upper() == 'RUNNING':
			break
		print 'Waiting on OVM to be ready... current state is ' + ovm_state
		time.sleep(5)

	return session


# returns correctly formatted json
@filecache(conf['cache_lifetime'])
def parse_ovm_vms():
	# create an ovm session
	session = ovm_session(conf['url'], conf['user'], conf['password'])
	data = session.get(conf['url'] + '/Vm')
	data = data.json()
	return data

# takes a vm object, returns hostvars object for that vm
def parse_hostvars_ovm(vm):
	vm_hostvars = {}
	for element in vm:
  		if element in conf['ovm_property_blacklist']:
  			pass
  		elif element in conf['use_name_instead']:
			try:
  				vm_hostvars['ovm_' + element] = vm[element]['name']
  			except TypeError:
  				vm_hostvars['ovm_' + element] = None
  		else:
  			vm_hostvars['ovm_' + element] = vm[element]
  	return vm_hostvars


def list_output_ovm():
	vms = parse_ovm_vms()
	output = {}
	output['ovm'] = []
	output['_meta'] = { 'hostvars': {} }

	output['ovm_bad_name'] = []
	valid_hostname = re.compile('^[A-Za-z0-9\.\-]+$')

	for vm in vms:
		# add all VMs to a group even without a tag
		vm_name = vm['name']
		output['ovm'].append(vm_name)

		# call out all vms improperly named (invalid hostname)
		if not valid_hostname.match(vm_name):
			output['ovm_bad_name'].append(vm_name)

		# create groups for each tag and add members to them
		for tag in vm['resourceGroupIds']:
			try:
				output[tag['name']].append(vm_name)
			except(KeyError, IndexError):
				output[tag['name']] = [vm_name]

  		# create hostvars
  		output['_meta']['hostvars'][vm_name] = parse_hostvars_ovm(vm)

	return output


def host_output_ovm():
	all_vms = parse_ovm_vms()
	for vm in all_vms:
		if vm['name'].upper() == args.host[0].upper():
			return parse_hostvars_ovm(vm)


# artisanally crafted output
if args.host and args.list:
	print 'Please select --list OR --host, not both.'
	print parser.print_help()
	sys.exit(2)
elif args.host and args.pretty:
	print json.dumps(host_output_ovm(), indent=4, sort_keys=True)
elif args.host:
	print json.dumps(host_output_ovm())
elif args.list and args.pretty:
	print json.dumps(list_output_ovm(), indent=4, sort_keys=True)
elif args.list:
	print json.dumps(list_output_ovm())
else:
	parser.print_help()
	sys.exit(2)
