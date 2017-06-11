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
- name: "add interface to ospf"
  quagga_command:
    commands:
      - "interface {{ item }}"
      - "ip ospf authentication message-digest"
      - "ip ospf message-digest-key 1 md5 xxxx"
      - "ip ospf hello-interval 10"
      - "ip ospf dead-interval 40"
      - "ip ospf priority 99"
      - "ip ospf cost 40"
      - "ip ospf network broadcast"
  with_items:
    - "{{ ansible_interfaces }}"
  when: "'wg_' in item"

- name: "add router to ospf"
  quagga_command:
    commands:
      - "router ospf"
      - "log-adjacency-changes"
      - "network 10.1.16.0/24 area 0"
      - "network 10.254.222.0/24 area 0"
      - "area 0 authentication message-digest"
      - "exit"
      - "router-id 10.10.10.1"

'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule

def run_cmd(module, cmd, check_rc=True, split_lines=True):
    try:
        (rc, out, err) = module.run_command(cmd, check_rc=check_rc)
    except Exception, e:
        module.fail_json(msg=e.strerror)
    return out

def set_commands(module):
    command = ["vtysh", "'configure terminal'", "'end'", "'write memory'"]
    for raw in module.params['commands']:
        command.insert(-2, "'{}'".format(raw))
    run_cmd(module, ' -c '.join(command))

def main():

    module = AnsibleModule(
        argument_spec = dict(
            commands = dict(type='list', required=True),
        ),
    )

    before_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")

    set_commands(module)

    after_status = run_cmd(module, "vtysh -c 'show run' -c 'end'")
    module.exit_json(changed=before_status!=after_status)

if __name__ == '__main__':
    main()
