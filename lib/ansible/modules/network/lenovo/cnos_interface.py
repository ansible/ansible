#!/usr/bin/python
# -*- coding: utf-8 -*-
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
ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_interface
author: "Dave Kasberg (@dkasberg)"
short_description: Manage interface configuration on devices running Lenovo CNOS
description:
    - This module allows you to work with interface related configurations. The operators used are
     overloaded to ensure control over switch interface configurations. Apart from the regular device
     connection related attributes, there are seven interface arguments that will perform further
     configurations. They are interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5,
     interfaceArg6, and interfaceArg7. For more details on how to use these arguments, see
     [Overloaded Variables]. Interface configurations are taken care at six contexts in a regular CLI.
     They are
     1. Interface Name - Configurations
     2. Ethernet Interface - Configurations
     3. Loopback Interface Configurations
     4. Management Interface Configurations
     5. Port Aggregation - Configurations
     6. VLAN Configurations
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_interface.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
    interfaceRange:
        description:
            - This specifies the interface range in which the port aggregation is envisaged
        required: Yes
        default: Null
    interfaceOption:
        description:
            - This specifies the attribute you specify subsequent to interface command
        required: Yes
        default: Null
        choices: [None, ethernet, loopback, mgmt, port-aggregation, vlan]
    interfaceArg1:
        description:
            - This is an overloaded interface first argument. Usage of this argument can be found is the User Guide referenced above.
        required: Yes
        default: Null
        choices: [aggregation-group, bfd, bridgeport, description, duplex, flowcontrol, ip, ipv6, lacp, lldp,
        load-interval, mac, mac-address, mac-learn, microburst-detection, mtu, service, service-policy,
        shutdown, snmp, spanning-tree, speed, storm-control, vlan, vrrp, port-aggregation]
    interfaceArg2:
        description:
            - This is an overloaded interface second argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [aggregation-group number, access or mode or trunk, description, auto or full or half,
        receive or send, port-priority, suspend-individual, timeout, receive or transmit or trap-notification,
        tlv-select, Load interval delay in seconds, counter, Name for the MAC Access List, mac-address in HHHH.HHHH.HHHH format,
        THRESHOLD  Value in unit of buffer cell, <64-9216>  MTU in bytes-<64-9216> for L2 packet,<576-9216> for L3 IPv4 packet,
        <1280-9216> for L3 IPv6 packet, enter the instance id, input or output, copp-system-policy,
        type, 1000  or  10000  or   40000 or   auto, broadcast or multicast or unicast, disable or enable or egress-only,
        Virtual router identifier, destination-ip or destination-mac or destination-port or source-dest-ip or
        source-dest-mac or source-dest-port or source-interface or source-ip or source-mac or source-port]
    interfaceArg3:
        description:
            - This is an overloaded interface third argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [active or on or passive, on or off, LACP port priority, long or short, link-aggregation or
        mac-phy-status or management-address or max-frame-size or port-description or port-protocol-vlan or
        port-vlan or power-mdi or protocol-identity or system-capabilities or system-description or system-name
        or vid-management or vlan-name, counter for load interval, policy input name, all or Copp class name to attach,
        qos, queueing, Enter the allowed traffic level, ipv6]
    interfaceArg4:
        description:
            - This is an overloaded interface fourth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [key-chain, key-id, keyed-md5 or keyed-sha1 or meticulous-keyed-md5 or meticulous-keyed-sha1 or simple, Interval value in milliseconds,
         Destination IP (Both IPV4 and IPV6),in or out, MAC address, Time-out value in seconds, class-id, request, Specify the IPv4 address,
         OSPF area ID as a decimal value, OSPF area ID in IP address format, anycast or secondary, ethernet, vlan,
         MAC (hardware) address in HHHH.HHHH.HHHH format,
         Load interval delay in seconds, Specify policy input name, input or output, cost, port-priority, BFD minimum receive interval,source-interface]
    interfaceArg5:
        description:
            - This is an overloaded interface fifth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [name of key-chain,  key-Id Value, key-chain , key-id, BFD minimum receive interval, Value of Hello Multiplier,
        admin-down or multihop or non-persistent, Vendor class-identifier name, bootfile-name or host-name or log-server or ntp-server or tftp-server-name,
        Slot/chassis number, Vlan interface, Specify policy input name, Port path cost or auto, Port priority increments of 32]
    interfaceArg6:
        description:
            - This is an overloaded interface sixth argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Authentication key string, name of key-chain, key-Id Value, Value of Hello Multiplier, admin-down or non-persistent]
    interfaceArg7:
        description:
            - This is an overloaded interface seventh argument. Usage of this argument can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Authentication key string, admin-down]

'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_interface. These are written in the main.yml file of the tasks directory.
---
- name: Test Interface Ethernet - aggregation-group
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 1
      interfaceArg1: "aggregation-group"
      interfaceArg2: 33
      interfaceArg3: "on"

- name: Test Interface Ethernet - bridge-port
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "bridge-port"
      interfaceArg2: "access"
      interfaceArg3: 33

- name: Test Interface Ethernet - bridgeport mode
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "bridge-port"
      interfaceArg2: "mode"
      interfaceArg3: "access"

- name: Test Interface Ethernet  - Description
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "description"
      interfaceArg2: "Hentammoo "

- name: Test Interface Ethernet - Duplex
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 1
      interfaceArg1: "duplex"
      interfaceArg2: "auto"

- name: Test Interface Ethernet - flowcontrol
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "flowcontrol"
      interfaceArg2: "send"
      interfaceArg3: "off"

- name: Test Interface Ethernet - lacp
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "lacp"
      interfaceArg2: "port-priority"
      interfaceArg3: 33

- name: Test Interface Ethernet  - lldp
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "lldp"
      interfaceArg2: "tlv-select"
      interfaceArg3: "max-frame-size"

- name: Test Interface Ethernet - load-interval
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "load-interval"
      interfaceArg2: "counter"
      interfaceArg3: 2
      interfaceArg4: 33

- name: Test Interface Ethernet - mac
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "mac"
      interfaceArg2: "copp-system-acl-vlag-hc"

- name: Test Interface Ethernet - microburst-detection
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "microburst-detection"
      interfaceArg2: 25

- name: Test Interface Ethernet  - mtu
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "mtu"
      interfaceArg2: 66

- name: Test Interface Ethernet - service-policy
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "service-policy"
      interfaceArg2: "input"
      interfaceArg3: "Anil"

- name: Test Interface Ethernet - speed
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 1
      interfaceArg1: "speed"
      interfaceArg2: "auto"

- name: Test Interface Ethernet - storm
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "storm-control"
      interfaceArg2: "broadcast"
      interfaceArg3: 12.5

- name: Test Interface Ethernet - vlan
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "vlan"
      interfaceArg2: "disable"

- name: Test Interface Ethernet - vrrp
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "vrrp"
      interfaceArg2: 33

- name: Test Interface Ethernet - spanning tree1
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "spanning-tree"
      interfaceArg2: "bpduguard"
      interfaceArg3: "enable"

- name: Test Interface Ethernet - spanning tree 2
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "spanning-tree"
      interfaceArg2: "mst"
      interfaceArg3: "33-35"
      interfaceArg4: "cost"
      interfaceArg5: 33

- name: Test Interface Ethernet - ip1
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "ip"
      interfaceArg2: "access-group"
      interfaceArg3: "anil"
      interfaceArg4: "in"

- name: Test Interface Ethernet - ip2
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "ip"
      interfaceArg2: "port"
      interfaceArg3: "anil"

- name: Test Interface Ethernet - bfd
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
      interfaceRange: 33
      interfaceArg1: "bfd"
      interfaceArg2: "interval"
      interfaceArg3: 55
      interfaceArg4: 55
      interfaceArg5: 33

- name: Test Interface Ethernet - bfd
  cnos_interface:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_interface_{{ inventory_hostname }}_output.txt"
      interfaceOption: 'ethernet'
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
  sample: "Interface configurations accomplished."
'''

import sys
import paramiko
import time
import argparse
import socket
import array
import json
import time
import re
try:
    from ansible.module_utils import cnos
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
            interfaceOption=dict(required=False),
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
    interfaceOption = module.params['interfaceOption']
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
    if(interfaceOption is None or interfaceOption == ""):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, None, interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    elif(interfaceOption == "ethernet"):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "ethernet", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    elif(interfaceOption == "loopback"):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "loopback", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    elif(interfaceOption == "mgmt"):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "mgmt", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    elif(interfaceOption == "port-aggregation"):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "port-aggregation", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    elif(interfaceOption == "vlan"):
        output = output + cnos.interfaceConfig(remote_conn, deviceType, "(config)#", 2, "vlan", interfaceRange,
                                               interfaceArg1, interfaceArg2, interfaceArg3, interfaceArg4, interfaceArg5, interfaceArg6, interfaceArg7)
    else:
        output = "Invalid interface option \n"
    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # Logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Interface Configuration is done")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
        main()
