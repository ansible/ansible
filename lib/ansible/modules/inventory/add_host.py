# -*- mode: python -*-
#
# Copyright: Ansible Team
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = '''
---
module: add_host
short_description: add a host (and alternatively a group) to the ansible-playbook in-memory inventory
description:
  - Use variables to create new hosts and groups in inventory for use in later plays of the same playbook.
    Takes variables so you can define the new hosts more fully.
  - This module is also supported for Windows targets.
version_added: "0.9"
options:
  name:
    aliases: [ 'hostname', 'host' ]
    description:
    - The hostname/ip of the host to add to the inventory, can include a colon and a port number.
    required: true
  groups:
    aliases: [ 'groupname', 'group' ]
    description:
    - The groups to add the hostname to, comma separated.
    required: false
notes:
    - This module bypasses the play host loop and only runs once for all the hosts in the play, if you need it
      to iterate use a with\_ directive.
    - This module is also supported for Windows targets.
    - The alias 'host' of the parameter 'name' is only available on >=2.4
author:
    - "Ansible Core Team"
    - "Seth Vidal"
'''

EXAMPLES = '''
# add host to group 'just_created' with variable foo=42
- add_host:
    name: "{{ ip_from_ec2 }}"
    groups: just_created
    foo: 42

# add a host with a non-standard port local to your machines
- add_host:
    name: "{{ new_ip }}:{{ new_port }}"

# add a host alias that we reach through a tunnel (Ansible <= 1.9)
- add_host:
    hostname: "{{ new_ip }}"
    ansible_ssh_host: "{{ inventory_hostname }}"
    ansible_ssh_port: "{{ new_port }}"

# add a host alias that we reach through a tunnel (Ansible >= 2.0)
- add_host:
    hostname: "{{ new_ip }}"
    ansible_host: "{{ inventory_hostname }}"
    ansible_port: "{{ new_port }}"
'''
