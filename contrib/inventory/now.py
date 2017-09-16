#!/usr/bin/env python

# Copyright 2017 Reuben Stump, Alex Mittell

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing
# permissions and limitations under the License.

import os, sys, requests, base64, json, re, configparser, time
from cookielib import LWPCookieJar

class NowInventory(object):
	
	def __init__(self, hostname, username, password, fields=[], groups=[]):
		self.hostname = hostname

		# requests session
		self.session = requests.Session()

		self.auth = requests.auth.HTTPBasicAuth(username, password)
		# request headers
		self.headers = {
			"Accept": "application/json",
			"Content-Type": "application/json",
		}

		# request cookies
		self.cookies = LWPCookieJar(os.getenv("HOME") + "/.sn_api_session") 
		try:
			self.cookies.load(ignore_discard=True)
		except IOError:
			pass
		self.session.cookies = self.cookies

		# extra fields (table columns)
		self.fields = fields

		# extra groups (table columns)
		self.groups = groups

		# initialize inventory
		self.inventory = {'_meta': {'hostvars': { }}}

		return


    	def _put_cache(self, name, value):
        	cache_dir = os.environ.get('SN_CACHE_DIR')
        	if not cache_dir and config.has_option('defaults', 'cache_dir'):
            		cache_dir = os.path.expanduser(config.get('defaults', 'cache_dir'))
		if cache_dir:
            		if not os.path.exists(cache_dir):
                		os.makedirs(cache_dir)
            		cache_file = os.path.join(cache_dir, name)
            		with open(cache_file, 'w') as cache:
                		json.dump(value, cache)

    	def _get_cache(self, name, default=None):
		cache_dir = os.environ.get('SN_CACHE_DIR')
                if not cache_dir and config.has_option('defaults', 'cache_dir'):
            		cache_dir = config.get('defaults', 'cache_dir')
		if cache_dir:
            		cache_file = os.path.join(cache_dir, name)
            		if os.path.exists(cache_file):
				cache_max_age = int(os.environ.get('SN_CACHE_MAX_AGE'))
                		if not cache_max_age:
					if config.has_option('defaults', 'cache_max_age'):
                    				cache_max_age = config.getint('defaults', 'cache_max_age')
                			else:
                    				cache_max_age = 0
                		cache_stat = os.stat(cache_file)
                		if (cache_stat.st_mtime + cache_max_age) >= time.time():
                    			with open(cache_file) as cache:
        					return json.load(cache)
        	return default

	def __del__(self):
		self.cookies.save(ignore_discard=True)

	def _invoke(self, verb, path, data):

		cache_name = '__snow_inventory__'
		inventory = self._get_cache(cache_name, None)
        	if inventory is not None:
            		return inventory

		# build url
		url = "https://%s/%s" % (self.hostname, path)

		# perform REST operation
		response = self.session.get(url, auth=self.auth, headers=self.headers)
		if response.status_code != 200:
			print >> sys.stderr, "http error (%s): %s" % (response.status_code, response.text)

		self._put_cache(cache_name, response.json())
		return response.json()

	def add_group(self, target, group):
		
		''' Transform group names:
			1. lower()
			2. non-alphanumerical characters to '_'
		'''

		group = group.lower()
		group = re.sub('\W', '_', group)

		# Ignore empty group names
		if group == '':
			return

		self.inventory.setdefault(group, {'hosts': [ ]})
		self.inventory[group]['hosts'].append(target)
		return

	def add_var(self, target, key, val):
		if not target in self.inventory['_meta']['hostvars']:
			self.inventory['_meta']['hostvars'][target] = { }
		
		
		self.inventory['_meta']['hostvars'][target]["sn_" + key] = val
		return

	def generate(self):

		table  = 'cmdb_ci_server'
		base_fields = ['name','host_name','fqdn','ip_address','sys_class_name']
		base_groups = ['sys_class_name']
		options = "?sysparm_exclude_reference_link=true&sysparm_display_value=true"
		
		columns = list(set(base_fields + base_groups + self.fields + self.groups))
		path = '/api/now/table/' + table + options + "&sysparm_fields=" + ','.join(columns)
		
		# Default, mandatory group 'sys_class_name'
		groups = list(set(base_groups + self.groups))

		content = self._invoke('GET', path, None)

		for record in content['result']:
			''' Ansible host target selection order:
				1. ip_address
				2. fqdn
				3. host_name

				TODO: environment variable configuration flags to modify selection order
			'''
			target = None
			selection = ['host_name', 'fqdn', 'ip_address']

			for k in selection:
				if record[k] != '':
					target = record[k]

			# Skip if no target available
			if target == None:
				continue

			# hostvars
			for k in record.keys():
				self.add_var(target, k, record[k])

			# groups
			for k in groups:
				self.add_group(target, record[k])

		return

	def json(self):
		return json.dumps(self.inventory)

def main(args):

	# instance = os.environ['SN_INSTANCE']
	# username = os.environ['SN_USERNAME']
	# password = os.environ['SN_PASSWORD']
	global config 
	config = configparser.SafeConfigParser()

        if os.environ.get('NOW_INI', ''):
                config_files = [os.environ['NOW_INI']]
        else:
                config_files = [os.path.abspath(sys.argv[0]).rstrip('.py') + '.ini', 'now.ini']

        for config_file in config_files:
                if os.path.exists(config_file):
	                config.read(config_file)
                        break

        # Read authentication information from environment variables (if set), otherwise from INI file.
        instance = os.environ.get('SN_INSTANCE')
        if not instance and config.has_option('auth', 'instance'):
                instance = config.get('auth', 'instance')

        username = os.environ.get('SN_USERNAME')
        if not username and config.has_option('auth', 'user'):
                username = config.get('auth', 'user')

        password = os.environ.get('SN_PASSWORD')
        if not password and config.has_option('auth', 'password'):
                password = config.get('auth', 'password')

	# SN_GROUPS
	groups = os.environ.get("SN_GROUPS", [ ])
        if not groups and config.has_option('config', 'groups'):
                groups = config.get('config', 'groups')
	if isinstance(groups, basestring):
		groups = groups.split(',')

	# SN_FIELDS
	fields = os.environ.get("SN_FIELDS", [ ])
        if not fields and config.has_option('config', 'fields'):
                fields = config.get('config', 'fields')
	if isinstance(fields, basestring):
		fields = fields.split(',')

	inventory = NowInventory(hostname=instance, username=username, password=password, fields=fields, groups=groups)
	inventory.generate()
	print inventory.json()

if __name__ == "__main__":
	main(sys.argv)


