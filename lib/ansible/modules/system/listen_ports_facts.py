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
module: listen_ports_facts
author:
    - '"Nathan Davison (@ndavison)" <ndavison85@gmail.com>'
version_added: "2.4"
description:
    - Gather facts on processes listening on TCP and UDP ports. Optionally provide whitelists to gather facts on violations ofthe whitelist.
short_description: Gather facts on processes listening on TCP and UDP ports.
options:
  whitelist_tcp:
    description:
      - A list of TCP port numbers that are expected to have processes listening.
  whitelist_udp:
    description:
      - A list of UDP port numbers that are expected to have processes listening.
'''

EXAMPLES = '''
- name: gather facts on listening ports, and populate the tcp_listen_violations fact with processes listening on TCP ports that are not 22, 80, or 443.
  listen_ports_facts:
    whitelist_tcp:
      - 22
      - 80
      - 443

- name: TCP whitelist violation
  debug:
    msg: "TCP port {{item.port}} by pid {{item.pid}} violates the whitelist"
  with_items: "{{ tcp_listen_violations }}"
  when: tcp_listen_violations
'''

RETURN = '''
tcp_listen:
  description: A list of processes that are listening on a TCP port.
  type: list
  contains:
    address:
      description: The address (IPv4 or IPv6) of the process.
      type: string
      sample: '0.0.0.0'
    name:
      description: The name of the process.
      type: string
      sample: 'mysqld'
    pid:
      description: The pid of the process.
      type: int
      sample: 1223
    port:
      description: The port the pid was listening on.
      type: int
      sample: 3306
    protocol:
      description: The protocol, TCP or UDP, of the listening connection.
      type: string
      sample: 'tcp'
    stime:
      description: The start time of the process.
      type: string
      sample: 'Thu Feb  2 13:29:45 2017'
    user:
      description: The user running the process.
      type: string
      sample: 'mysql'

udp_listen:
  description: A list of processes that are listening on a UDP port.
  type: list
  contains:
    address:
      description: The address (IPv4 or IPv6) of the process.
      type: string
      sample: '0.0.0.0'
    name:
      description: The name of the process.
      type: string
      sample: 'rsyslogd'
    pid:
      description: The pid of the process.
      type: int
      sample: 609
    port:
      description: The port the pid was listening on.
      type: int
      sample: 514
    protocol:
      description: The protocol, TCP or UDP, of the listening connection.
      type: string
      sample: 'udp'
    stime:
      description: The start time of the process.
      type: string
      sample: 'Thu Feb  2 13:29:45 2017'
    user:
      description: The user running the process.
      type: string
      sample: 'root'

tcp_listen_violations:
  description: A list of processes that are listening on a TCP port that violated the whitelist_tcp argument.
  type: list
  contains:
    address:
      description: The address (IPv4 or IPv6) of the process.
      type: string
      sample: '0.0.0.0'
    name:
      description: The name of the process.
      type: string
      sample: 'mysqld'
    pid:
      description: The pid of the process.
      type: int
      sample: 1223
    port:
      description: The port the pid was listening on.
      type: int
      sample: 3306
    protocol:
      description: The protocol, TCP or UDP, of the listening connection.
      type: string
      sample: 'tcp'
    stime:
      description: The start time of the process.
      type: string
      sample: 'Thu Feb  2 13:29:45 2017'
    user:
      description: The user running the process.
      type: string
      sample: 'mysql'

udp_listen_violations:
  description: A list of processes that are listening on a UDP port that violated the whitelist_udp argument.
  type: list
  contains:
    address:
      description: The address (IPv4 or IPv6) of the process.
      type: string
      sample: '0.0.0.0'
    name:
      description: The name of the process.
      type: string
      sample: 'rsyslogd'
    pid:
      description: The pid of the process.
      type: int
      sample: 609
    port:
      description: The port the pid was listening on.
      type: int
      sample: 514
    protocol:
      description: The protocol, TCP or UDP, of the listening connection.
      type: string
      sample: 'udp'
    stime:
      description: The start time of the process.
      type: string
      sample: 'Thu Feb  2 13:29:45 2017'
    user:
      description: The user running the process.
      type: string
      sample: 'root'
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'committer',
                    'version': '1.0'}

import re
import platform
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception


def netStatParse(raw):
    results = list()
    for line in iter(raw.splitlines()):
        listening_search = re.search('[^ ]+:[0-9]+', line)
        if listening_search:
            splitted = line.split()
            conns = re.search('([^ ]+):([0-9]+)', splitted[3])
            pidstr = ''
            if 'tcp' in splitted[0]:
                protocol = 'tcp'
                pidstr = splitted[6]
            elif 'udp' in splitted[0]:
                protocol = 'udp'
                pidstr = splitted[5]
            pids = re.search('(([0-9]+)/(.*)|-)', pidstr)
            if conns and pids:
                address = conns.group(1)
                port = conns.group(2)
                if (pids.group(2)):
                    pid = pids.group(2)
                else:
                    pid = 0
                if (pids.group(3)):
                    name = pids.group(3)
                else:
                    name = ''
                result = dict(pid=int(pid), address=address, port=int(port), protocol=protocol, name=name)
                if result not in results:
                    results.append(result)
            else:
                raise EnvironmentError('Could not get process information for the listening ports.')
    return results


def applyWhitelist(portspids, whitelist=list()):
    processes = list()
    for p in portspids:
        if int(p['port']) not in whitelist and str(p['port']) not in whitelist:
            process = dict(pid=p['pid'], address=p['address'], port=p['port'], protocol=p['protocol'], name=p['name'], stime=p['stime'], user=p['user'])
            if process not in processes:
                processes.append(process)
    return processes


def main():

    module = AnsibleModule(
        argument_spec=dict(
            whitelist_tcp=dict(required=False, type='list', default=list()),
            whitelist_udp=dict(required=False, type='list', default=list())
        ),
        supports_check_mode=True
    )

    if platform.system() != 'Linux':
        module.fail_json(msg='This module requires Linux.')

    def getPidSTime(pid):
        ps_cmd = module.get_bin_path('ps', True)
        rc, ps_output, stderr = module.run_command([ps_cmd, '-o', 'lstart', '-p', str(pid)])
        stime = ''
        if rc == 0:
            for line in iter(ps_output.splitlines()):
                if 'started' not in line:
                    stime = line
        return stime

    def getPidUser(pid):
        ps_cmd = module.get_bin_path('ps', True)
        rc, ps_output, stderr = module.run_command([ps_cmd, '-o', 'user', '-p', str(pid)])
        user = ''
        if rc == 0:
            for line in iter(ps_output.splitlines()):
                if line != 'USER':
                    user = line
        return user

    result = {}
    result['changed'] = False
    result['ansible_facts'] = dict(tcp_listen_violations=list(), udp_listen_violations=list(), tcp_listen=list(), udp_listen=list())

    try:
        netstat_cmd = module.get_bin_path('netstat', True)

        # which ports are listening for connections?
        rc, stdout, stderr = module.run_command([netstat_cmd, '-plunt'])
        if rc == 0:
            netstatOut = netStatParse(stdout)
            for i, p in enumerate(netstatOut):
                p['stime'] = getPidSTime(p['pid'])
                p['user'] = getPidUser(p['pid'])
                if p['protocol'] == 'tcp':
                    result['ansible_facts']['tcp_listen'].append(p)
                elif p['protocol'] == 'udp':
                    result['ansible_facts']['udp_listen'].append(p)

    except:
        e = get_exception()
        module.fail_json(msg=str(e))

    # if a TCP whitelist was supplied, determine which if any pids violate it
    if module.params['whitelist_tcp'] and result['ansible_facts']['tcp_listen']:
        tcp_violations = applyWhitelist(result['ansible_facts']['tcp_listen'], module.params['whitelist_tcp'])
        if tcp_violations:
            result['ansible_facts']['tcp_listen_violations'] = tcp_violations

    # if a UDP whitelist was supplied, determine which if any pids violate it
    if module.params['whitelist_udp'] and result['ansible_facts']['udp_listen']:
        udp_violations = applyWhitelist(result['ansible_facts']['udp_listen'], module.params['whitelist_udp'])
        if udp_violations:
            result['ansible_facts']['udp_listen_violations'] = udp_violations

    module.exit_json(**result)

if __name__ == '__main__':
    main()
