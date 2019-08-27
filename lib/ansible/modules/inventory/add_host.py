# -*- mode: python -*-

# Copyright: (c) 2012, Seth Vidal (@skvidal)
# Copyright: Ansible Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: add_host
short_description: Add a host (and alternatively a group) to the ansible-playbook in-memory inventory
description:
- Use variables to create new hosts and groups in inventory for use in later plays of the same playbook.
- Takes variables so you can define the new hosts more fully.
- This module is also supported for Windows targets.
version_added: "0.9"
options:
  name:
    description:
    - The hostname/ip of the host to add to the inventory, can include a colon and a port number.
    type: str
    required: true
    aliases: [ host, hostname ]
  groups:
    description:
    - The groups to add the hostname to.
    type: list
    aliases: [ group, groupname ]
notes:
- This module bypasses the play host loop and only runs once for all the hosts in the play, if you need it
  to iterate use a with-loop construct.
- The alias C(host) of the parameter C(name) is only available on Ansible 2.4 and newer.
- Since Ansible 2.4, the C(inventory_dir) variable is now set to C(None) instead of the 'global inventory source',
  because you can now have multiple sources.  An example was added that shows how to partially restore the previous behaviour.
- Windows targets are supported by this module.
seealso:
- module: group_by
author:
- Ansible Core Team
- Seth Vidal (@skvidal)
'''

EXAMPLES = r'''
- name: Add host to group 'just_created' with variable foo=42
  add_host:
    name: '{{ ip_from_ec2 }}'
    groups: just_created
    foo: 42

- name: Add host to multiple groups
  add_host:
    hostname: '{{ new_ip }}'
    groups:
    - group1
    - group2

- name: Add a host with a non-standard port local to your machines
  add_host:
    name: '{{ new_ip }}:{{ new_port }}'

- name: Add a host alias that we reach through a tunnel (Ansible 1.9 and older)
  add_host:
    hostname: '{{ new_ip }}'
    ansible_ssh_host: '{{ inventory_hostname }}'
    ansible_ssh_port: '{{ new_port }}'

- name: Add a host alias that we reach through a tunnel (Ansible 2.0 and newer)
  add_host:
    hostname: '{{ new_ip }}'
    ansible_host: '{{ inventory_hostname }}'
    ansible_port: '{{ new_port }}'

- name: Ensure inventory vars are set to the same value as the inventory_hostname has (close to pre Ansible 2.4 behaviour)
  add_host:
    hostname: charlie
    inventory_dir: '{{ inventory_dir }}'
'''
