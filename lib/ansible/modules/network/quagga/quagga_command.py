#!/usr/bin/python
# -*- coding: utf-8 -*-

# {c} 2017, Aleksey Gavrilov <le9i0nx+ansible@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: quagga_command
version_added: 2.4
short_description: Provides configuring quaggas
description:
    - The M(quagga_command) module takes the command name followed by a list of space-delimited arguments.
    - The given command will be executed on all selected nodes.
    - Documentation for M (quagga) can be found U(http://www.nongnu.org/quagga/docs.html)
options:
    raw:
        description:
            - vtysh command after 'configure terminal'
author:
    - Aleksey Gavrilov (@le9i0nx)
'''

EXAMPLES = '''
# Example for Ansible Playbooks.

- name: "log syslog"
  quagga_command:
    commands:
      - "log syslog"

- name: "security"
  quagga_command:
    commands:
      - "access-list localhost-in-only permit 127.0.0.1/32"
      - "line vty"
      - "access-class localhost-in-only"

- name: "router-id"
  quagga_command:
    commands:
      - "router-id {{ quagga_router_id }}"
      - "interface lo"
      - "ip address {{ quagga_router_id }}/32"
      - "exit"
      - "router ospf"
      - "network {{ quagga_router_id }}/32 area 0"
      - "router-id {{ quagga_router_id }}"
  notify:
    - 'quagga restarted'

- name: "router ospf"
  quagga_command:
    commands:
      - "router ospf"
      - "log-adjacency-changes"
      - "area 0 authentication message-digest"

- name: "interface ospf"
  quagga_command:
    commands:
      - "interface {{ item }}"
      - "ip ospf area 0.0.0.0"
      - "ip ospf network broadcast"
      - "ip ospf authentication message-digest"
      - "ip ospf message-digest-key 2 md5 xxxxxxxxxxxxxxxx"
  with_items:
    - "{{ ansible_interfaces }}"

'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule


def run_cmd(module, cmd, check_rc=True):
    rc, out, err = module.run_command(cmd, check_rc=check_rc)
    return out


def set_commands(module):
    command = ["vtysh", "'configure terminal'", "'end'", "'write memory'"]
    for raw in module.params['commands']:
        command.insert(-2, "'{}'".format(raw))
    run_cmd(module, ' -c '.join(command))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            commands=dict(type='list', required=True)))

    before_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")
    set_commands(module)
    after_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")
    module.exit_json(changed=before_status != after_status)


if __name__ == '__main__':
    main()
