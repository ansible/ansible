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
version_added: "2.3"
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
    stime:
      description: The start time of the killed process.
      type: string
      sample: Thu Apr 21 17:30:16 2016
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'committer',
                    'version': '1.0'}

import re
import os
import platform
from subprocess import Popen, PIPE
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception

def netStatParse(raw):
    results = list()
    for line in iter(raw.splitlines()):
        listening_search = re.search('[^ ]+:[0-9]+', line)
        if listening_search:
            splitted = line.split()
            conns = re.search('[^ ]+:([0-9]+)', splitted[3])
            pidstr = ''
            if 'tcp' in splitted[0]:
                proto = 'tcp'
                pidstr = splitted[6]
            elif 'udp' in splitted[0]:
                proto = 'udp'
                pidstr = splitted[5]
            pids = re.search('([0-9]+)/(.*)', pidstr)
            if conns and pids:
                port = conns.group(1)
                pid = pids.group(1)
                name = pids.group(2)
                result = dict(pid=int(pid), port=int(port), proto=proto, name=name)
                if result not in results:
                    results.append(result)
            elif not pids:
                raise EnvironmentError('Could not get the pids for the listening ports - possibly a permission issue')
    return results

def applyWhitelist(portspids, whitelist=list()):
    kill_pids = list()
    for p in portspids:
        if int(p['port']) not in whitelist and str(p['port']) not in whitelist:
            to_kill = dict(pid=p['pid'], port=p['port'], proto=p['proto'], name=p['name'], stime=p['stime'])
            if to_kill not in kill_pids:
                kill_pids.append(to_kill)
    return kill_pids

def main():

    module = AnsibleModule(
        argument_spec = dict(
            whitelist_tcp = dict(required=False, type='list', default=list()),
            whitelist_udp = dict(required=False, type='list', default=list())
        ),
        supports_check_mode=True
    )

    if platform.system() != 'Linux':
        module.fail_json(msg='This module requires Linux.')

    if not module.params['whitelist_tcp'] and not module.params['whitelist_udp']:
        module.fail_json(msg="You must supply either a 'whitelist_tcp' or 'whitelist_udp' argument.")

    def getPidSTime(pid):
        ps_cmd = module.get_bin_path('ps', True)
        p1 = Popen([ps_cmd, '-o', 'lstart', '-p', str(pid)], stdout=PIPE, stderr=PIPE)
        ps_output = p1.communicate()[0]
        stime = ''
        for line in iter(ps_output.splitlines()):
            if 'started' not in line:
                stime = line
        return stime

    result = {}
    result['changed'] = False
    result['killed'] = list()

    try:
        netstat_cmd = module.get_bin_path('netstat', True)

        # which TCP ports are listening for connections?
        p1 = Popen([netstat_cmd, '-plnt'], stdout=PIPE, stderr=PIPE)
        output_tcp = p1.communicate()[0]
        kill_tcp = netStatParse(output_tcp)
        for i, p in enumerate(kill_tcp):
            p['stime'] = getPidSTime(p['pid'])
            kill_tcp[i] = p

        # which UDP ports are listening for connections?
        p1 = Popen([netstat_cmd, '-plnu'], stdout=PIPE, stderr=PIPE)
        output_udp = p1.communicate()[0]
        kill_udp = netStatParse(output_udp)
        for i, p in enumerate(kill_udp):
            p['stime'] = getPidSTime(p['pid'])
            kill_udp[i] = p

    except EnvironmentError:
        err = get_exception()
        module.fail_json(msg=str(err))

    # gather details of the pids to kill
    kill_pids_tcp = applyWhitelist(kill_tcp, module.params['whitelist_tcp'])
    kill_pids_udp = applyWhitelist(kill_udp, module.params['whitelist_udp'])
    kill_all = list(kill_pids_tcp)
    kill_all.extend(x for x in kill_pids_udp if x not in kill_pids_tcp)

    # get just the pids to avoid duplicates across protocols
    kill_unique = list()
    pids_seen = list()
    for p in kill_all:
        if p['pid'] not in pids_seen:
            pids_seen.append(p['pid'])
            kill_unique.append(p)

    # kill! kill!
    if not module.check_mode:
        for p in kill_unique:
            if p['stime'] == getPidSTime(p['pid']):
                os.kill(p['pid'], 15)

    if kill_all:
        result['changed'] = True
        result['killed'] = kill_all

    module.exit_json(**result)

# import module snippets
if __name__ == '__main__':
    main()
