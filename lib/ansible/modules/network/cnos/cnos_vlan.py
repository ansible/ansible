#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2017 Lenovo, Inc.
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
#
# Module to send VLAN commands to Lenovo Switches
# Overloading aspect of vlan creation in a range is pending
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_vlan
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage VLAN resources and attributes on devices running Lenovo CNOS
description:
    - This module allows you to work with VLAN related configurations. The
     operators used are overloaded to ensure control over switch VLAN
     configurations. The first level of VLAN configuration allows to set up the
     VLAN range, the VLAN tag persistence, a VLAN access map and access map
     filter. After passing this level, there are five VLAN arguments that will
     perform further configurations. They are vlanArg1, vlanArg2, vlanArg3,
     vlanArg4, and vlanArg5. The value of vlanArg1 will determine the way
     following arguments will be evaluated. For more details on how to use these
     arguments, see [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_vlan.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
  vlanArg1:
    description:
      - This is an overloaded vlan first argument. Usage of this argument can be found is the User Guide referenced above.
    required: true
    choices: [access-map, dot1q, filter, <1-3999> VLAN ID 1-3999 or range]
  vlanArg2:
    description:
      - This is an overloaded vlan second argument. Usage of this argument can be found is the User Guide referenced above.
    choices: [VLAN Access Map name,egress-only,name, flood,state, ip]
  vlanArg3:
    description:
      - This is an overloaded vlan third argument. Usage of this argument can be found is the User Guide referenced above.
    choices: [action, match, statistics, enter VLAN id or range of vlan, ascii name for the VLAN, ipv4 or ipv6, active or suspend, fast-leave,
    last-member-query-interval, mrouter, querier, querier-timeout, query-interval, query-max-response-time, report-suppression,
    robustness-variable, startup-query-count, startup-query-interval, static-group]
  vlanArg4:
    description:
      - This is an overloaded vlan fourth argument. Usage of this argument can be found is the User Guide referenced above.
    choices: [drop or forward or redirect, ip or mac,Interval in seconds,ethernet, port-aggregation, Querier IP address,
    Querier Timeout in seconds, Query Interval in seconds, Query Max Response Time in seconds,  Robustness Variable value,
    Number of queries sent at startup, Query Interval at startup]
  vlanArg5:
    description:
      - This is an overloaded vlan fifth argument. Usage of this argument can be found is the User Guide referenced above.
    choices: [access-list name, Slot/chassis number, Port Aggregation Number]

'''
EXAMPLES = '''

Tasks: The following are examples of using the module cnos_vlan. These are written in the main.yml file of the tasks directory.
---
- name: Test Vlan - Create a vlan, name it
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: 13
      vlanArg2: "name"
      vlanArg3: "Anil"

- name: Test Vlan - Create a vlan, Flood configuration
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: 13
      vlanArg2: "flood"
      vlanArg3: "ipv4"

- name: Test Vlan - Create a vlan, State configuration
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: 13
      vlanArg2: "state"
      vlanArg3: "active"

- name: Test Vlan - VLAN Access map1
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: "access-map"
      vlanArg2: "Anil"
      vlanArg3: "statistics"

- name: Test Vlan - VLAN Accep Map2
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: "access-map"
      vlanArg2: "Anil"
      vlanArg3: "action"
      vlanArg4: "forward"

- name: Test Vlan - ip igmp snooping query interval
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: 13
      vlanArg2: "ip"
      vlanArg3: "query-interval"
      vlanArg4: 1313

- name: Test Vlan - ip igmp snooping mrouter interface port-aggregation 23
  cnos_vlan:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
      password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_vlan_{{ inventory_hostname }}_output.txt"
      vlanArg1: 13
      vlanArg2: "ip"
      vlanArg3: "mrouter"
      vlanArg4: "port-aggregation"
      vlanArg5: 23

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "VLAN configuration is accomplished"
'''

import sys
try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
import time
import socket
import array
import json
import time
import re

try:
    from ansible.module_utils.network.cnos import cnos
    HAS_LIB = True
except:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def main():
    #
    # Define parameters for vlan creation entry
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            vlanArg1=dict(required=True),
            vlanArg2=dict(required=False),
            vlanArg3=dict(required=False),
            vlanArg4=dict(required=False),
            vlanArg5=dict(required=False),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    vlanArg1 = module.params['vlanArg1']
    vlanArg2 = module.params['vlanArg2']
    vlanArg3 = module.params['vlanArg3']
    vlanArg4 = module.params['vlanArg4']
    vlanArg5 = module.params['vlanArg5']
    outputfile = module.params['outputfile']
    hostIP = module.params['host']
    deviceType = module.params['deviceType']

    output = ""
    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in
    # your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(hostIP, username=username, password=password)
    time.sleep(2)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)

    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)

    output = output + \
        cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + \
        cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    # Go to config mode
    output = output + \
        cnos.waitForDeviceResponse("configure device\n", "(config)#", 2, remote_conn)

    # Send the CLi command
    output = output + \
        cnos.vlanConfig(
            remote_conn, deviceType, "(config)#", 2, vlanArg1, vlanArg2,
            vlanArg3, vlanArg4, vlanArg5)

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="VLAN configuration is accomplished")
    else:
        module.fail_json(msg=errorMsg)

if __name__ == '__main__':
    main()
