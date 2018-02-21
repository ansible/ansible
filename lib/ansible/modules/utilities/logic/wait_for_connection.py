#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Dag Wieers <dag@wieers.com>
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
- This module makes use of internal ansible transport (and configuration) and the ping/win_ping module to guarantee correct end-to-end functioning.
- This module is also supported for Windows targets.
- This module does not support delegation (see the last example on how to overcome this).
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
      - Number of seconds to sleep between checks.
    description:
  timeout:
    description:
      - Maximum number of seconds to wait for.
    default: 600
notes:
- This module is also supported for Windows targets.
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

# Build a new VM, wait for it to become ready and continue playbook (playbook
# runs against remote host from inventory)
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

# Build an online instance, wait for it to become ready and continue (playbook
# runs against localhost).
- hosts: localhost
  tasks:
    - name: Create instance on Google Cloud
      gce:
        name: instance-name
        zone: europe-west1-b
        network: default
        subnet: subnet-name
        machine-type: n1-highcpu-4
        image-family: windows-2016
      register: instance
    - add_host: &windows
        hostname: win_instance
        ansible_host: "{{ instance.instance_data[0].public_ip }}"
        ansible_connection: winrm
        ansible_port: 5986
        ansible_winrm_server_cert_validation: ignore
        ansible_winrm_transport: ntl
        ansible_password: password
    - wait_for_connection:
      vars: *windows
'''

RETURN = r'''
elapsed:
  description: The number of seconds that elapsed waiting for the connection to appear.
  returned: always
  type: int
  sample: 23
'''
