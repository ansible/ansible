#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
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
- This module makes use of internal ansible transport (and configuration) and the ping/win_ping or raw module to guarantee correct end-to-end functioning.
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
  raw_cmd:
    description:
    - the command use to test end-to-end connectivity, it's exit code must be 0 (eg. `/bin/true`, `systemctl is-system-running`).
    - if unset the module use ping/win_ping to test end-to-end functioning.
    type: str
    default: null
    version_added: '2.9'
  raw_executable:
    description:
    - C(executable) parameter to pass to raw module (if used).
    type: str
    version_added: '2.9'
notes:
- This module is also supported for Windows targets.
seealso:
- module: wait_for
- module: win_wait_for
- module: win_wait_for_process
author:
- Dag Wieers (@dagwieers)
'''

EXAMPLES = r'''
- name: Wait 600 seconds for target connection to become reachable/usable
  wait_for_connection:

- name: Wait 300 seconds, but only start checking after 60 seconds
  wait_for_connection:
    delay: 60
    timeout: 300

- name: Wait for the machine to be reachable, and the boot process to finish (machine may not have python installed)
  wait_for_connection:
    # beware, if a service fail during boot, this command will always fail, so the machine will never be considered `ready`
    raw_cmd: /bin/systemctl is-system-running
    delay: 30

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
  type: float
  sample: 23.1
'''
