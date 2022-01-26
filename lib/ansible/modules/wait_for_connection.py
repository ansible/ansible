# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: wait_for_connection
short_description: Waits until remote system is reachable/usable
description:
- Waits for a total of C(timeout) seconds.
- Retries the transport connection after a timeout of C(connect_timeout).
- Tests the transport connection every C(sleep) seconds.
- This module makes use of internal ansible transport (and configuration) and the ping/win_ping module to guarantee correct end-to-end functioning.
- This module is also supported for Windows targets.
version_added: '2.3'
options:
  connect_timeout:
    description:
    - Maximum number of seconds to wait for a connection to happen before closing and retrying.
    type: int
    default: 5
  delay:
    description:
    - Number of seconds to wait before starting to poll.
    type: int
    default: 0
  sleep:
    description:
    - Number of seconds to sleep between checks.
    type: int
    default: 1
  timeout:
    description:
    - Maximum number of seconds to wait for.
    type: int
    default: 600
extends_documentation_fragment:
    - action_common_attributes
    - action_common_attributes.flow
attributes:
    action:
        support: full
    async:
        support: none
    bypass_host_loop:
        support: none
    check_mode:
        support: none
    diff_mode:
        support: none
    platform:
        details: As long as there is a connection plugin
        platforms: all
seealso:
- module: ansible.builtin.wait_for
- module: ansible.windows.win_wait_for
- module: community.windows.win_wait_for_process
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Wait 600 seconds for target connection to become reachable/usable
  ansible.builtin.wait_for_connection:

- name: Wait 300 seconds, but only start checking after 60 seconds
  ansible.builtin.wait_for_connection:
    delay: 60
    timeout: 300

# Wake desktops, wait for them to become ready and continue playbook
- hosts: all
  gather_facts: no
  tasks:
  - name: Send magic Wake-On-Lan packet to turn on individual systems
    community.general.wakeonlan:
      mac: '{{ mac }}'
      broadcast: 192.168.0.255
    delegate_to: localhost

  - name: Wait for system to become reachable
    ansible.builtin.wait_for_connection:

  - name: Gather facts for first time
    ansible.builtin.setup:

# Build a new VM, wait for it to become ready and continue playbook
- hosts: all
  gather_facts: no
  tasks:
  - name: Clone new VM, if missing
    community.vmware.vmware_guest:
      hostname: '{{ vcenter_ipaddress }}'
      name: '{{ inventory_hostname_short }}'
      template: Windows 2012R2
      customization:
        hostname: '{{ vm_shortname }}'
        runonce:
        - powershell.exe -ExecutionPolicy Unrestricted -File C:\Windows\Temp\ConfigureRemotingForAnsible.ps1 -ForceNewSSLCert -EnableCredSSP
    delegate_to: localhost

  - name: Wait for system to become reachable over WinRM
    ansible.builtin.wait_for_connection:
      timeout: 900

  - name: Gather facts for first time
    ansible.builtin.setup:
'''

RETURN = r'''
elapsed:
  description: The number of seconds that elapsed waiting for the connection to appear.
  returned: always
  type: float
  sample: 23.1
'''
