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
version_added: "2.3"
description:
    - Gather facts on processes listening on TCP and UDP ports. Optionally provide a whitelist of TCP and/or UDP ports to gather facts on processes that
    violate the whitelists.
short_description: Gather facts on processes listening on TCP and UDP ports.
options:
  whitelist_tcp:
    description:
      - A list of TCP port numbers that are expected to have processes listening.
    required: false
    type: "list"
  whitelist_udp:
    description:
      - A list of UDP port numbers that are expected to have processes listening.
    required: false
    type: "list"
'''

EXAMPLES = '''
- name: gather facts on listening ports, and populate the tcp_listen_violations fact with processes listening on TCP ports that are not 22, 80, or 443.
  listen_ports_facts:
    whitelist_tcp:
      - 22
      - 80
      - 443
'''

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'committer',
                    'version': '1.0'}

import re
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
            conns = re.search('([^ ]+):([0-9]+)', splitted[3])
            pidstr = ''
            if 'tcp' in splitted[0]:
                protocol = 'tcp'
                pidstr = splitted[6]
            elif 'udp' in splitted[0]:
                protocol = 'udp'
                pidstr = splitted[5]
            pids = re.search('([0-9]+)/(.*)', pidstr)
            if conns and pids:
                address = conns.group(1)
                port = conns.group(2)
                pid = pids.group(1)
                name = pids.group(2)
                result = dict(pid=int(pid), address=address, port=int(port), protocol=protocol, name=name)
                if result not in results:
                    results.append(result)
            elif not pids:
                raise EnvironmentError('Could not get the pids for the listening ports - possibly a permission issue')
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
        argument_spec = dict(
            whitelist_tcp = dict(required=False, type='list', default=list()),
            whitelist_udp = dict(required=False, type='list', default=list())
        ),
        supports_check_mode=False
    )

    if platform.system() != 'Linux':
        module.fail_json(msg='This module requires Linux.')

    def getPidSTime(pid):
        ps_cmd = module.get_bin_path('ps', True)
        p1 = Popen([ps_cmd, '-o', 'lstart', '-p', str(pid)], stdout=PIPE, stderr=PIPE)
        ps_output = p1.communicate()[0]
        stime = ''
        for line in iter(ps_output.splitlines()):
            if 'started' not in line:
                stime = line
        return stime

    def getPidUser(pid):
        ps_cmd = module.get_bin_path('ps', True)
        p1 = Popen([ps_cmd, '-o', 'user', '-p', str(pid)], stdout=PIPE, stderr=PIPE)
        ps_output = p1.communicate()[0]
        user = ''
        for line in iter(ps_output.splitlines()):
            if line != 'USER':
                user = line
        return user

    result = {}
    result['changed'] = False
    result['ansible_facts'] = dict(tcp_listen_violations=list(), udp_listen_violations=list(), tcp_listen=list(), udp_listen=list())

    try:
        netstat_cmd = module.get_bin_path('netstat', True)

        # which TCP ports are listening for connections?
        p1 = Popen([netstat_cmd, '-plnt'], stdout=PIPE, stderr=PIPE)
        output_tcp = p1.communicate()[0]
        tcp_ports = netStatParse(output_tcp)
        for i, p in enumerate(tcp_ports):
            p['stime'] = getPidSTime(p['pid'])
            p['user'] = getPidUser(p['pid'])
            tcp_ports[i] = p
        if tcp_ports:
            result['ansible_facts']['tcp_listen'] = tcp_ports

        # which UDP ports are listening for connections?
        p1 = Popen([netstat_cmd, '-plnu'], stdout=PIPE, stderr=PIPE)
        output_udp = p1.communicate()[0]
        udp_ports = netStatParse(output_udp)
        for i, p in enumerate(udp_ports):
            p['stime'] = getPidSTime(p['pid'])
            p['user'] = getPidUser(p['pid'])
            udp_ports[i] = p
        if udp_ports:
            result['ansible_facts']['udp_listen'] = udp_ports

    except EnvironmentError:
        err = get_exception()
        module.fail_json(msg=str(err))

    # if a TCP whitelist was supplied, determine which if any pids violate it
    if module.params['whitelist_tcp'] and tcp_ports:
        tcp_violations = applyWhitelist(tcp_ports, module.params['whitelist_tcp'])
        if tcp_violations:
            result['ansible_facts']['tcp_listen_violations'] = tcp_violations

    # if a UDP whitelist was supplied, determine which if any pids violate it
    if module.params['whitelist_udp'] and udp_ports:
        udp_violations = applyWhitelist(udp_ports, module.params['whitelist_udp'])
        if udp_violations:
            result['ansible_facts']['udp_listen_violations'] = udp_violations

    module.exit_json(**result)

if __name__ == '__main__':
    main()
