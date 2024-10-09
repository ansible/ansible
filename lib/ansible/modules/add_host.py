# -*- mode: python -*-

# Copyright: (c) 2012, Seth Vidal (@skvidal)
# Copyright: Ansible Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations


DOCUMENTATION = r"""
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
    elements: str
    aliases: [ group, groupname ]
extends_documentation_fragment:
  - action_common_attributes
  - action_common_attributes.conn
  - action_common_attributes.flow
  - action_core
attributes:
    action:
        support: full
    core:
      details: While parts of this action are implemented in core, other parts are still available as normal plugins and can be partially overridden
      support: partial
    become:
      support: none
    bypass_host_loop:
        support: full
    bypass_task_loop:
        support: none
    check_mode:
        details: While this makes no changes to target systems the 'in memory' inventory will still be altered
        support: partial
    connection:
        support: none
    delegation:
        support: none
    diff_mode:
        support: none
    platform:
        platforms: all
notes:
- The alias O(host) of the parameter O(name) is only available on Ansible 2.4 and newer.
- Since Ansible 2.4, the C(inventory_dir) variable is now set to V(None) instead of the 'global inventory source',
  because you can now have multiple sources.  An example was added that shows how to partially restore the previous behaviour.
- Though this module does not change the remote host, we do provide C(changed) status as it can be useful for those trying to track inventory changes.
- The hosts added will not bypass the C(--limit) from the command line, so both of those need to be in agreement to make them available as play targets.
  They are still available from hostvars and for delegation as a normal part of the inventory.
seealso:
- module: ansible.builtin.group_by
author:
- Ansible Core Team
- Seth Vidal (@skvidal)
"""

EXAMPLES = r"""
- name: Add host to group 'just_created' with variable foo=42
  ansible.builtin.add_host:
    name: '{{ ip_from_ec2 }}'
    groups: just_created
    foo: 42

- name: Add host to multiple groups
  ansible.builtin.add_host:
    hostname: '{{ new_ip }}'
    groups:
    - group1
    - group2

- name: Add a host with a non-standard port local to your machines
  ansible.builtin.add_host:
    name: '{{ new_ip }}:{{ new_port }}'

- name: Add a host alias that we reach through a tunnel (Ansible 1.9 and older)
  ansible.builtin.add_host:
    hostname: '{{ new_ip }}'
    ansible_ssh_host: '{{ inventory_hostname }}'
    ansible_ssh_port: '{{ new_port }}'

- name: Add a host alias that we reach through a tunnel (Ansible 2.0 and newer)
  ansible.builtin.add_host:
    hostname: '{{ new_ip }}'
    ansible_host: '{{ inventory_hostname }}'
    ansible_port: '{{ new_port }}'

- name: Ensure inventory vars are set to the same value as the inventory_hostname has (close to pre Ansible 2.4 behaviour)
  ansible.builtin.add_host:
    hostname: charlie
    inventory_dir: '{{ inventory_dir }}'

- name: Add all hosts running this playbook to the done group
  ansible.builtin.add_host:
    name: '{{ item }}'
    groups: done
  loop: "{{ ansible_play_hosts }}"
"""
