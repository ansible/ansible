#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2017, Nathan Davison <ndavison85@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: listen_ports_facts

author:
    - Nathan Davison (@ndavison)

version_added: "2.8"

description:
    - Gather facts on processes listening on TCP and UDP ports.
    - Optionally provide whitelists to gather facts on violations of the whitelist.

short_description: Gather facts on processes listening on TCP and UDP ports.

options:
  whitelist_tcp:
    description:
      - A list of TCP port numbers that are expected to have processes listening.
    type: list
    default: []
  whitelist_udp:
    description:
      - A list of UDP port numbers that are expected to have processes listening.
    type: list
    default: []
'''

EXAMPLES = r'''
- name: Gather facts on listening ports, and populate the tcp_listen_violations fact with processes listening on TCP ports that are not 22, 80, or 443.
  listen_ports_facts:
    whitelist_tcp:
      - 22
      - 80
      - 443

- name: TCP whitelist violation
  debug:
    msg: TCP port {{ item.port }} by pid {{ item.pid }} violates the whitelist
  with_items: "{{ tcp_listen_violations }}"
  when: tcp_listen_violations
'''

RETURN = r'''
ansible_facts:
  description: Dictionary containing details of TCP and UDP ports with listening servers and any violations not found in the optional whitelists
  returned: always
  type: complex
  contains:
    tcp_listen:
      description: A list of processes that are listening on a TCP port.
      returned: if TCP servers were found
      type: list
      contains:
        address:
          description: The address the server is listening on.
          returned: always
          type: str
          sample: "0.0.0.0"
        name:
          description: The name of the listening process.
          returned: if user permissions allow
          type: str
          sample: "mysqld"
        pid:
          description: The pid of the listening process.
          returned: always
          type: int
          sample: 1223
        port:
          description: The port the server is listening on.
          returned: always
          type: int
          sample: 3306
        protocol:
          description: The network protocol of the server.
          returned: always
          type: str
          sample: "tcp"
        stime:
          description: The start time of the listening process.
          returned: always
          type: str
          sample: "Thu Feb  2 13:29:45 2017"
        user:
          description: The user who is running the listening process.
          returned: always
          type: str
          sample: "mysql"
    udp_listen:
      description: A list of processes that are listening on a UDP port.
      returned: if UDP servers were found
      type: list
      contains:
        address:
          description: The address the server is listening on.
          returned: always
          type: str
          sample: "0.0.0.0"
        name:
          description: The name of the listening process.
          returned: if user permissions allow
          type: str
          sample: "rsyslogd"
        pid:
          description: The pid of the listening process.
          returned: always
          type: int
          sample: 609
        port:
          description: The port the server is listening on.
          returned: always
          type: int
          sample: 514
        protocol:
          description: The network protocol of the server.
          returned: always
          type: str
          sample: "udp"
        stime:
          description: The start time of the listening process.
          returned: always
          type: str
          sample: "Thu Feb  2 13:29:45 2017"
        user:
          description: The user who is running the listening process.
          returned: always
          type: str
          sample: "root"
    tcp_listen_violations:
      description: A list of processes that are listening on a TCP port that was not in the whitelist_tcp argument.
      returned: if a TCP whitelist was supplied and violations were found
      type: list
      contains:
        address:
          description: The address the server is listening on.
          returned: always
          type: str
          sample: "0.0.0.0"
        name:
          description: The name of the listening process.
          returned: if user permissions allow
          type: str
          sample: "mysqld"
        pid:
          description: The pid of the listening process.
          returned: always
          type: int
          sample: 1223
        port:
          description: The port the server is listening on.
          returned: always
          type: int
          sample: 3306
        protocol:
          description: The network protocol of the server.
          returned: always
          type: str
          sample: "tcp"
        stime:
          description: The start time of the listening process.
          returned: always
          type: str
          sample: "Thu Feb  2 13:29:45 2017"
        user:
          description: The user who is running the listening process.
          returned: always
          type: str
          sample: "mysql"
    udp_listen_violations:
      description: A list of processes that are listening on a UDP port that was not in the whitelist_udp argument.
      returned: if a UDP whitelist was supplied and violations were found
      type: list
      contains:
        address:
          description: The address the server is listening on.
          returned: always
          type: str
          sample: "0.0.0.0"
        name:
          description: The name of the listening process.
          returned: if user permissions allow
          type: str
          sample: "rsyslogd"
        pid:
          description: The pid of the listening process.
          returned: always
          type: int
          sample: 609
        port:
          description: The port the server is listening on.
          returned: always
          type: int
          sample: 514
        protocol:
          description: The network protocol of the server.
          returned: always
          type: str
          sample: "udp"
        stime:
          description: The start time of the listening process.
          returned: always
          type: str
          sample: "Thu Feb  2 13:29:45 2017"
        user:
          description: The user who is running the listening process.
          returned: always
          type: str
          sample: "root"
'''

import re
import platform
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule


def netStatParse(raw):
    results = list()
    for line in raw.splitlines():
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


def applyWhitelist(portspids, whitelist=None):
    if whitelist is None:
        whitelist = list()
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
            whitelist_tcp=dict(type='list', default=list()),
            whitelist_udp=dict(type='list', default=list()),
        ),
        supports_check_mode=True,
    )

    if platform.system() != 'Linux':
        module.fail_json(msg='This module requires Linux.')

    def getPidSTime(pid):
        ps_cmd = module.get_bin_path('ps', True)
        rc, ps_output, stderr = module.run_command([ps_cmd, '-o', 'lstart', '-p', str(pid)])
        stime = ''
        if rc == 0:
            for line in ps_output.splitlines():
                if 'started' not in line:
                    stime = line
        return stime

    def getPidUser(pid):
        ps_cmd = module.get_bin_path('ps', True)
        rc, ps_output, stderr = module.run_command([ps_cmd, '-o', 'user', '-p', str(pid)])
        user = ''
        if rc == 0:
            for line in ps_output.splitlines():
                if line != 'USER':
                    user = line
        return user

    result = dict(
        changed=False,
        ansible_facts=dict(
            tcp_listen_violations=list(),
            udp_listen_violations=list(),
            tcp_listen=list(),
            udp_listen=list(),
        ),
    )

    try:
        netstat_cmd = module.get_bin_path('netstat', True)

        # which ports are listening for connections?
        rc, stdout, stderr = module.run_command([netstat_cmd, '-plunt'])
        if rc == 0:
            netstatOut = netStatParse(stdout)
            for p in netstatOut:
                p['stime'] = getPidSTime(p['pid'])
                p['user'] = getPidUser(p['pid'])
                if p['protocol'] == 'tcp':
                    result['ansible_facts']['tcp_listen'].append(p)
                elif p['protocol'] == 'udp':
                    result['ansible_facts']['udp_listen'].append(p)
    except KeyError as e:
        module.fail_json(msg=to_native(e))

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
