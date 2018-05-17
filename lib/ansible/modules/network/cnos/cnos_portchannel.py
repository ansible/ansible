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
# Module to send Port channel commands to Lenovo Switches
# Lenovo Networking
#
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_portchannel
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage portchannel (port aggregation) configuration on devices running Lenovo CNOS
description:
    - This module allows you to work with port aggregation related configurations. The operators
     used are overloaded to ensure control over switch port aggregation configurations. Apart
     from the regular device connection related attributes, there are five LAG arguments which are
     overloaded variables that will perform further configurations. They are interfaceArg1, interfaceArg2,
     interfaceArg3, interfaceArg4, and interfaceArg5. For more details on how to use these arguments, see
     [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_portchannel.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    interfaceRange:
        description:
            - This specifies the interface range in which the port aggregation is envisaged
        required: Yes
        default: Null
    interfaceArg1:
        description:
            - This is an overloaded Port Channel first argument. Usage of this argument can be found is the User Guide referenced above.
        required: Yes
        default: Null
        choices: [aggregation-group, bfd, bridgeport, description, duplex, flowcontrol, ip, ipv6, lacp, lldp,
        load-interval, mac, mac-address, mac-learn, microburst-detection, mtu, service, service-policy,
        shutdown, snmp, spanning-tree, speed, storm-control, vlan, vrrp, port-aggregation]
    interfaceArg2:
        description:
            - This is an overloaded Port Channel second argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [aggregation-group number, access or mode or trunk, description, auto or full or half,
        receive or send, port-priority, suspend-individual, timeout,     receive or transmit or trap-notification,
        tlv-select, Load interval delay in seconds, counter, Name for the MAC Access List, mac-address in HHHH.HHHH.HHHH format,
        THRESHOLD  Value in unit of buffer cell, <64-9216>  MTU in bytes-<64-9216> for L2 packet,<576-9216> for
        L3 IPv4 packet, <1280-9216> for L3 IPv6 packet, enter the instance id, input or output, copp-system-policy,
        type, 1000  or  10000  or   40000 or   auto, broadcast or multicast or unicast, disable or enable or egress-only,
        Virtual router identifier, destination-ip or destination-mac or destination-port or source-dest-ip or
        source-dest-mac or source-dest-port or source-interface or source-ip or source-mac or source-port]
    interfaceArg3:
        description:
            - This is an overloaded Port Channel third argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [active or on or passive, on or off, LACP port priority, long or short, link-aggregation or
        mac-phy-status or management-address or max-frame-size or port-description or port-protocol-vlan or
        port-vlan or power-mdi or protocol-identity or system-capabilities or system-description or system-name
        or vid-management or vlan-name, counter for load interval, policy input name, all or Copp class name to attach,
        qos, queueing, Enter the allowed traffic level, ipv6]
    interfaceArg4:
        description:
            - This is an overloaded Port Channel fourth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [key-chain, key-id, keyed-md5 or keyed-sha1 or meticulous-keyed-md5 or meticulous-keyed-sha1 or simple, Interval value in milliseconds,
         Destination IP (Both IPV4 and IPV6),in or out, MAC address, Time-out value in seconds, class-id, request, Specify the IPv4 address,
         OSPF area ID as a decimal value, OSPF area ID in IP address format, anycast or secondary, ethernet, vlan,
         MAC (hardware) address in HHHH.HHHH.HHHH format,
         Load interval delay in seconds, Specify policy input name, input or output, cost, port-priority, BFD minimum receive interval,source-interface]
    interfaceArg5:
        description:
            - This is an overloaded Port Channel fifth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [name of key-chain,  key-Id Value, key-chain , key-id, BFD minimum receive interval, Value of Hello Multiplier,
        admin-down or multihop or non-persistent, Vendor class-identifier name, bootfile-name or host-name or log-server or ntp-server or tftp-server-name,
        Slot/chassis number, Vlan interface, Specify policy input name, Port path cost or auto, Port priority increments of 32]
    interfaceArg6:
        description:
            - This is an overloaded Port Channel sixth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Authentication key string, name of key-chain, key-Id Value, Value of Hello Multiplier, admin-down or non-persistent]
    interfaceArg7:
        description:
            - This is an overloaded Port Channel seventh argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Authentication key string, admin-down]
'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_portchannel. These are written in the main.yml file of the tasks directory.
---
- name: Test Port Channel - aggregation-group
  cnos_portchannel:
    host: "{{ inventory_hostname }}"
    username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
    password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
    deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
    outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
    interfaceRange: 33
    interfaceArg1: "aggregation-group"
    interfaceArg2: 33
    interfaceArg3: "on"

- name: Test Port Channel - aggregation-group - Interface Range
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: "1/1-2"
  interfaceArg1: "aggregation-group"
  interfaceArg2: 33
  interfaceArg3: "on"

- name: Test Port Channel - bridge-port
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "bridge-port"
  interfaceArg2: "access"
  interfaceArg3: 33

- name: Test Port Channel - bridgeport mode
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "bridge-port"
  interfaceArg2: "mode"
  interfaceArg3: "access"

- name: Test Port Channel  - Description
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "description"
  interfaceArg2: "Hentammoo "

- name: Test Port Channel - Duplex
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "duplex"
  interfaceArg2: "auto"

- name: Test Port Channel - flowcontrol
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "flowcontrol"
  interfaceArg2: "send"
  interfaceArg3: "off"

- name: Test Port Channel - lacp
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "lacp"
  interfaceArg2: "port-priority"
  interfaceArg3: 33

- name: Test Port Channel  - lldp
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "lldp"
  interfaceArg2: "tlv-select"
  interfaceArg3: "max-frame-size"

- name: Test Port Channel - load-interval
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "load-interval"
  interfaceArg2: "counter"
  interfaceArg3: 2
  interfaceArg4: 33

#- name: Test Port Channel - mac
#  cnos_portchannel:
#  host: "{{ inventory_hostname }}"
#  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
#  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
#  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
#  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
#  interfaceRange: 33,
#  interfaceArg1: "mac"
#  interfaceArg2: "copp-system-acl-vlag-hc"

- name: Test Port Channel - microburst-detection
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "microburst-detection"
  interfaceArg2: 25

- name: Test Port Channel  - mtu
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "mtu"
  interfaceArg2: 66

- name: Test Port Channel - service-policy
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "service-policy"
  interfaceArg2: "input"
  interfaceArg3: "Anil"

- name: Test Port Channel - speed
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "speed"
  interfaceArg2: "auto"

- name: Test Port Channel - storm
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "storm-control"
  interfaceArg2: "broadcast"
  interfaceArg3: 12.5

#- name: Test Port Channel - vlan
#  cnos_portchannel:
#  host: "{{ inventory_hostname }}"
#  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
#  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
#  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
#  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
#  interfaceRange: 33
#  interfaceArg1: "vlan"
#  interfaceArg2: "disable"

- name: Test Port Channel - vrrp
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "vrrp"
  interfaceArg2: 33

- name: Test Port Channel - spanning tree1
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "spanning-tree"
  interfaceArg2: "bpduguard"
  interfaceArg3: "enable"

- name: Test Port Channel - spanning tree 2
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "spanning-tree"
  interfaceArg2: "mst"
  interfaceArg3: "33-35"
  interfaceArg4: "cost"
  interfaceArg5: 33

- name: Test Port Channel - ip1
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "ip"
  interfaceArg2: "access-group"
  interfaceArg3: "anil"
  interfaceArg4: "in"

- name: Test Port Channel - ip2
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "ip"
  interfaceArg2: "port"
  interfaceArg3: "anil"

- name: Test Port Channel - bfd
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "bfd"
  interfaceArg2: "interval"
  interfaceArg3: 55
  interfaceArg4: 55
  interfaceArg5: 33

- name: Test Port Channel - bfd
  cnos_portchannel:
  host: "{{ inventory_hostname }}"
  username: "{{ hostvars[inventory_hostname]['ansible_ssh_user'] }}"
  password: "{{ hostvars[inventory_hostname]['ansible_ssh_pass'] }}"
  deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
  outputfile: "./results/test_portchannel_{{ inventory_hostname }}_output.txt"
  interfaceRange: 33
  interfaceArg1: "bfd"
  interfaceArg2: "ipv4"
  interfaceArg3: "authentication"
  interfaceArg4: "meticulous-keyed-md5"
  interfaceArg5: "key-chain"
  interfaceArg6: "mychain"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "Port Channel configurations accomplished"
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
            interfaceRange=dict(required=False),
            interfaceArg1=dict(required=True),
            interfaceArg2=dict(required=False),
            interfaceArg3=dict(required=False),
            interfaceArg4=dict(required=False),
            interfaceArg5=dict(required=False),
            interfaceArg6=dict(required=False),
            interfaceArg7=dict(required=False),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    interfaceRange = module.params['interfaceRange']
    interfaceArg1 = module.params['interfaceArg1']
    interfaceArg2 = module.params['interfaceArg2']
    interfaceArg3 = module.params['interfaceArg3']
    interfaceArg4 = module.params['interfaceArg4']
    interfaceArg5 = module.params['interfaceArg5']
    interfaceArg6 = module.params['interfaceArg6']
    interfaceArg7 = module.params['interfaceArg7']
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
    output = output + cnos.waitForDeviceResponse("configure device\n", "(config)#", 2, remote_conn)

    # Send the CLi command
    if(interfaceArg1 == "port-aggregation"):
        output = output + cnos.portChannelConfig(remote_conn, deviceType, "(config)#", 2, interfaceArg1,
                                                 interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    else:
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "port-aggregation", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Port Aggregation configuration is done")
    else:
        module.fail_json(msg=errorMsg)

if __name__ == '__main__':
    main()
