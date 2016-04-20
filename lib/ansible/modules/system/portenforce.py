#!/usr/bin/python
# encoding: utf-8

# (c) 2016, Nathan Davison <ndavison85@gmail.com>
#
# This file is part of Ansible
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

DOCUMENTATION = '''
---
module: portenforce
author:
    - '"Nathan Davison (@ndavison)" <ndavison85@gmail.com>'
version_added: "2.1"
description:
    - Kill processes listening on TCP and UDP ports not defined in the whitelists.
short_description: Kill processes listening on TCP and UDP ports not defined in the whitelists.
options:
  whitelist_tcp:
    description:
      - A list of TCP ports to allow.
    required: false
    type: "list"
  whitelist_udp:
    description:
      - A list of UDP ports to allow.
    required: false
    type: "list"
'''

EXAMPLES = '''
- name: only allow TCP 80, 443, and 22
  portenforce:
    whitelist_tcp:
      - 22
      - 80
      - 443
'''

RETURN = '''
killed:
  description: A list of pids that were killed.
  type: list
  contains:
    pid:
      description: The pid of a killed process.
      type: int
      sample: 1223
    port:
      description: The port the killed pid was listening on.
      type: int
      sample: 443
    proto:
      description: The protocol, TCP or UDP, of the listening connection.
      type: string
      sample: 'tcp'
'''

import re
from subprocess import Popen, PIPE

def netStatParse(raw):
	results = list()
	for line in iter(raw.splitlines()):
		listening_search = re.search('[^ ]+:[^ ]+', line)
		if listening_search:
			splitted = line.split()
			conns = re.search('[^ ]+:([^ ]+)', splitted[3])
			if 'tcp' in splitted[0]:
				proto = 'tcp'
			else:
				proto = 'udp'
			pidstr = splitted[6] if proto == 'tcp' else splitted[5]
			pids = re.search('([0-9]+)/', pidstr)
			if conns and pids:
				port = conns.group(1)
				pid = pids.group(1)
				result = dict(pid=int(pid), port=int(port), proto=proto)
				if result not in results:
					results.append(result)
			elif not pids:
				raise EnvironmentError('Could not get the pids for the listening ports - possibly a permission issue')
	return results

def applyWhitelist(portspids, whitelist=list()):
	kill_pids = list()
	for p in portspids:
		if int(p['port']) not in whitelist and str(p['port']) not in whitelist:
			if dict(pid=p['pid'], port=p['port'], proto=p['proto']) not in kill_pids:
				kill_pids.append(dict(pid=p['pid'], port=p['port'], proto=p['proto']))
	return kill_pids

def main():

	module = AnsibleModule(
		argument_spec = dict(
			whitelist_tcp = dict(required=False, type='list', default=list()),
			whitelist_udp = dict(required=False, type='list', default=list())
		),
		supports_check_mode=True
	)

	result = {}
	result['changed'] = False
	result['killed'] = list()

	try:
		# which TCP ports are listening for connections?
		p1 = Popen(['netstat', '-plnt'], stdout=PIPE, stderr=PIPE)
		output_tcp = p1.communicate()[0]
		kill_tcp = netStatParse(output_tcp)

		# which UDP ports are listening for connections?
		p1 = Popen(['netstat', '-plnu'], stdout=PIPE, stderr=PIPE)
		output_udp = p1.communicate()[0]
		kill_udp = netStatParse(output_udp)
	except EnvironmentError as err:
		module.fail_json(msg=str(err))

	# gather all the pids to kill
	kill_pids_tcp = applyWhitelist(kill_tcp, module.params['whitelist_tcp'])
	kill_pids_udp = applyWhitelist(kill_udp, module.params['whitelist_udp'])
	killed = list(kill_pids_tcp)
	killed.extend(x for x in kill_pids_udp if x not in kill_pids_tcp)

	# kill! kill!
	if not module.check_mode:
		for p in killed:
			p1 = Popen(['kill', str(p['pid'])], stdout=PIPE)

	if killed:
		result['changed'] = True
		result['killed'] = killed

	module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()