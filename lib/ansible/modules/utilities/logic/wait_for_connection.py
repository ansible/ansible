#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Dag Wieers <dag@wieers.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}


DOCUMENTATION = r'''
---
module: wait_for_connection
short_description: Waits until remote system is reachable/usable
description:
- Waits for a total of C(timeout) seconds.
- Retries the transport connection after a timeout of C(connect_timeout).
- Tests the transport connection every C(sleep) seconds.
- This module makes use of internal ansible transport (and configuration) and the ping/win_ping module to guarantee correct end-to-end functioning.
version_added: "2.3"
options:
  connect_timeout:
    description:
      - Maximum number of seconds to wait for a connection to happen before closing and retrying.
    default: 5
  delay:
    description:
      - Number of seconds to wait before starting to poll.
    default: 0
  sleep:
    default: 1
    description:
      - Number of seconds to sleep between checks.
  timeout:
    description:
      - Maximum number of seconds to wait for.
    default: 600
author: "Dag Wieers (@dagwieers)"
'''

EXAMPLES = r'''
- name: Wait 600 seconds for target connection to become reachable/usable
  wait_for_connection:

- name: Wait 300 seconds, but only start checking after 60 seconds
  wait_for_connection:
    delay: 60
    timeout: 300

# Wake desktops, wait for them to become ready and continue playbook
- hosts: all
  gather_facts: no
  tasks:
  - name: Send magic Wake-On-Lan packet to turn on individual systems
    wakeonlan:
      mac: '{{ mac }}'
      broadcast: 192.168.0.255
    delegate_to: localhost

  - name: Wait for system to become reachable
    wait_for_connection:

  - name: Gather facts for first time
    setup:

# Build a new VM, wait for it to become ready and continue playbook
- hosts: all
  gather_facts: no
  tasks:
  - name: Clone new VM, if missing
    vmware_guest:
      hostname: '{{ vcenter_ipaddress }}'
      name: '{{ inventory_hostname_short }}'
      template: Windows 2012R2
      customization:
        hostname: '{{ vm_shortname }}'
        runonce:
        - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert -EnableCredSSP
    delegate_to: localhost

  - name: Wait for system to become reachable over WinRM
    wait_for_connection:
      timeout: 900

  - name: Gather facts for first time
    setup:
'''

RETURN = r'''
elapsed:
  description: The number of seconds that elapsed waiting for the connection to appear.
  returned: always
  type: integer
  sample: 23
'''
