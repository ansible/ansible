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
# Module to send BGP commands to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: cnos_bgp
author: "Dave Kasberg (@dkasberg)"
short_description: Manage BGP resources and attributes on devices running Lenovo CNOS
description:
    - This module allows you to work with Border Gateway Protocol (BGP) related configurations.
     The operators used are overloaded to ensure control over switch BGP configurations. This
     module is invoked using method with asNumber as one of its arguments. The first level of
     the BGP configuration allows to set up an AS number, with the following attributes going
     into various configuration operations under the context of BGP. After passing this level,
     there are eight BGP arguments that will perform further configurations. They are bgpArg1,
     bgpArg2, bgpArg3, bgpArg4, bgpArg5, bgpArg6, bgpArg7, and bgpArg8. For more details on
     how to use these arguments, see [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_bgp.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    asNum:
        description:
            - AS number
        required: Yes
        default: Null
    bgpArg1:
        description:
            - This is an overloaded bgp first argument. Usage of this argument can be found is the User Guide referenced above.
        required: Yes
        default: Null
        choices: [address-family,bestpath,bgp,cluster-id,confederation,enforce-first-as,fast-external-failover,
        graceful-restart,graceful-restart-helper,log-neighbor-changes,maxas-limit,neighbor,router-id,shutdown,
        synchronization,timers,vrf]
    bgpArg2:
        description:
            - This is an overloaded bgp second argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [ipv4 or ipv6, always-compare-med,compare-confed-aspath,compare-routerid,dont-compare-originator-id,tie-break-on-age,
        as-path,med,identifier,peers]
    bgpArg3:
        description:
            - This is an overloaded bgp third argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [aggregate-address,client-to-client,dampening,distance,maximum-paths,network,nexthop,redistribute,save,synchronization,
        ignore or multipath-relax, confed or missing-as-worst or non-deterministic or remove-recv-med or remove-send-med]
    bgpArg4:
        description:
            - This is an overloaded bgp fourth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Aggregate prefix, Reachability Half-life time,route-map, Distance for routes external,ebgp or ibgp,
        IP prefix <network>,IP prefix <network>/<length>, synchronization, Delay value, direct, ospf, static, memory]
    bgpArg5:
        description:
            - This is an overloaded bgp fifth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [as-set, summary-only, Value to start reusing a route, Distance for routes internal, Supported multipath numbers,
        backdoor, map, route-map ]
    bgpArg6:
        description:
            - This is an overloaded bgp sixth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [summary-only,as-set, route-map name, Value to start suppressing a route, Distance for local routes,  Network mask,
        Pointer to route-map entries]
    bgpArg7:
        description:
            - This is an overloaded bgp seventh argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [ Maximum duration to suppress a stable route(minutes), backdoor,route-map, Name of the route map ]
    bgpArg8:
        description:
            - This is an overloaded bgp eigth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [ Un-reachability Half-life time for the penalty(minutes), backdoor]
'''
EXAMPLES = '''
Tasks: The following are examples of using the module cnos_bgp. These are written in the main.yml file of the tasks directory.
---
- name: Test BGP  - neighbor
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "neighbor"
      bgpArg2: "10.241.107.40"
      bgpArg3: 13
      bgpArg4: "address-family"
      bgpArg5: "ipv4"
      bgpArg6: "next-hop-self"

- name: Test BGP  - BFD
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "neighbor"
      bgpArg2: "10.241.107.40"
      bgpArg3: 13
      bgpArg4: "bfd"

- name: Test BGP  - address-family - dampening
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "address-family"
      bgpArg2: "ipv4"
      bgpArg3: "dampening"
      bgpArg4: 13
      bgpArg5: 233
      bgpArg6: 333
      bgpArg7: 15
      bgpArg8: 33

- name: Test BGP  - address-family - network
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "address-family"
      bgpArg2: "ipv4"
      bgpArg3: "network"
      bgpArg4: "1.2.3.4/5"
      bgpArg5: "backdoor"

- name: Test BGP - bestpath - always-compare-med
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bestpath"
      bgpArg2: "always-compare-med"

- name: Test BGP - bestpath-compare-confed-aspat
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bestpath"
      bgpArg2: "compare-confed-aspath"

- name: Test BGP - bgp
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bgp"
      bgpArg2: 33

- name: Test BGP  - cluster-id
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "cluster-id"
      bgpArg2: "1.2.3.4"

- name: Test BGP - confederation-identifier
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "confederation"
      bgpArg2: "identifier"
      bgpArg3: 333

- name: Test BGP - enforce-first-as
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "enforce-first-as"

- name: Test BGP - fast-external-failover
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "fast-external-failover"

- name: Test BGP  - graceful-restart
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "graceful-restart"
      bgpArg2: 333

- name: Test BGP - graceful-restart-helper
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "graceful-restart-helper"

- name: Test BGP - maxas-limit
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "maxas-limit"
      bgpArg2: 333

- name: Test BGP  - neighbor
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "neighbor"
      bgpArg2: "10.241.107.40"
      bgpArg3: 13
      bgpArg4: "address-family"
      bgpArg5: "ipv4"
      bgpArg6: "next-hop-self"

- name: Test BGP - router-id
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "router-id"
      bgpArg2: "1.2.3.4"

- name: Test BGP - synchronization
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "synchronization"

- name: Test BGP - timers
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "timers"
      bgpArg2: 333
      bgpArg3: 3333

- name: Test BGP - vrf
  cnos_bgp:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "vrf"

'''
RETURN = '''
msg:
  description: Success or failure message. Upon any failure, the method returns an error display string.
  returned: always
  type: string
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
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            bgpArg1=dict(required=True),
            bgpArg2=dict(required=False),
            bgpArg3=dict(required=False),
            bgpArg4=dict(required=False),
            bgpArg5=dict(required=False),
            bgpArg6=dict(required=False),
            bgpArg7=dict(required=False),
            bgpArg8=dict(required=False),
            asNum=dict(required=True),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    bgpArg1 = module.params['bgpArg1']
    bgpArg2 = module.params['bgpArg2']
    bgpArg3 = module.params['bgpArg3']
    bgpArg4 = module.params['bgpArg4']
    bgpArg5 = module.params['bgpArg5']
    bgpArg6 = module.params['bgpArg6']
    bgpArg7 = module.params['bgpArg7']
    bgpArg8 = module.params['bgpArg8']
    asNum = module.params['asNum']
    outputfile = module.params['outputfile']
    hostIP = module.params['host']
    deviceType = module.params['deviceType']
    output = ""

    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')
    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(hostIP, username=username, password=password)
    time.sleep(2)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)

    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)

    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    # Go to config mode
    output = output + cnos.waitForDeviceResponse("configure d\n", "(config)#", 2, remote_conn)

    # Send the CLi command
    output = output + cnos.routerConfig(remote_conn, deviceType, "(config)#", 2, "bgp", asNum,
                                        bgpArg1, bgpArg2, bgpArg3, bgpArg4, bgpArg5, bgpArg6, bgpArg7, bgpArg8)

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="BGP configurations accomplished")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
