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
# Module to send VLAN commands to Lenovo Switches
# Overloading aspect of vlan creation in a range is pending 
# Lenovo Networking
#
#---- Documentation Start ----------------------------------------------------#
DOCUMENTATION = '''
---
module: cnos_vlan
short_description: Performs all configurations on switches pertaining to VLAN.
description: 
    - Manages network device configurations over SSH. This module allows implementors to work with the VLAN 
     configurations. The operators here are overloaded to take care of all configurations pertaining to vlan. 
     In the level one, u will be able to configure vlan RANGE, access-map, dot1q and filter. The argument value 
     in vlanArg1 will determine the way how subsequent variables folliwing that ie. vlanArg2, vlanArg3 etc are 
     evaluated. Please see the example section to understand more how this overloading functions. Results of the 
     backup operation can be viewed in results folder.

version_added: "2.3"
options:
    vlanArg1:
        description:
            - This is an overloaded vlan first argument. Usage of these overloaded variables are described in the table below.
             Value of these argument depends on the configuration context.
        required: Yes
        default: null
        choices: [access-map, dot1q, filter, <1-3999> VLAN ID 1-3999 or range]
    vlanArg2:
        description:
            - This is an overloaded vlan second argument. Usage of these overloaded variables are described in the table below.
             Value of these argument depends on the configuration context.
        required: No
        default: null
        choices: [VLAN Access Map name,egress-only,name, flood,state, ip]
    vlanArg3:
        description:
            - This is an overloaded vlan third argument. Usage of these overloaded variables are described in the table below.
             Value of these argument depends on the configuration context.
        required: No
        default: null
        choices: [action, match, statistics, enter VLAN id or range of vlan, ascii name for the VLAN, ipv4 or ipv6, active or suspend, fast-leave, 
        last-member-query-interval, mrouter, querier, querier-timeout, query-interval, query-max-response-time, report-suppression,
        robustness-variable, startup-query-count, startup-query-interval, static-group]
    vlanArg4:
        description:
            - This is an overloaded vlan fourth argument. Usage of these overloaded variables are described in the table below.
             Value of these argument depends on the configuration context.
        required: No
        default: null
        choices: [drop or forward or redirect, ip or mac,Interval in seconds,ethernet, port-aggregation, Querier IP address, 
        Querier Timeout in seconds, Query Interval in seconds, Query Max Response Time in seconds,  Robustness Variable value,
        Number of queries sent at startup, Query Interval at startup]
    vlanArg5:
        description:
            - This is an overloaded vlan fifth argument. Usage of these overloaded variables are described in the table below.
             Value of these argument depends on the configuration context.
        required: No
        default: null
        choices: [access-list name, Slot/chassis number, Port Aggregation Number]
    
Overloaded Options:
#Please find below the table with option how the overloaded variables are used in the context of VLAN. 
    vlanArg1: [access-map,access-map,access-map,dot1q,filter,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range,<1-3999> VLAN ID 1-3999 or range]
    vlanArg2: [VLAN Access Map name,VLAN Access Map name,VLAN Access Map name,egress-only,VLAN Access Map Name,name,flood,state,ip,ip,ip,ip,ip,ip,ip,ip,ip,ip,ip,ip,ip]
    vlagArg3: [drop or forward or redirect,ip or mac,~,~,~,~,~,~,~, Interval in seconds,ethernet,port-aggregation,Querier IP address,Querier Timeout in seconds,Query Interval in seconds, Query Max Response Time in seconds,~, Robustness Variable value, Number of queries sent at startup,Query Interval at startup,~]
    vlagArg4: [~,access-list name,~,~,~,~,~,~,~,~,Slot/chassis number,Port Aggregation Number,~,~,~,~,~,~,~,~,~]
    Remarks: [~,~,~,vlanArg2 is optional,~,~,vlanArg3 is optional,~,~,~,~,~,~,~,~,~,~,~,~,~,This feature is not supported. Please use runcommand option]

Notes:
    - For help in developing on modules, should you be so inclined, please read 
     Community Information & Contributing, Helping Testing PRs and Developing Modules.
    
Module Dependency :
    1. cnos_vlan.py
    2. cnos.py 
'''

EXAMPLES = '''
#The task/main.yml will look like this

---

- name: Test Vlan - Create a vlan, name it
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}'
  with_items: "{{test_vlan_data1}}"

- name: Test Vlan - Create a vlan, Flood configuration
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}}  password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}'
  with_items: "{{test_vlan_data2}}"

- name: Test Vlan - Create a vlan, State configuration
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}'
  with_items: "{{test_vlan_data3}}"

- name: Test Vlan - VLAN Access map1
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}'
  with_items: "{{test_vlan_data4}}"

- name: Test Vlan - VLAN Accep Map2
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}' vlanArg4='{{item.vlanArg4}}'
  with_items: "{{test_vlan_data5}}"

- name: Test Vlan - ip igmp snooping query interval
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}' vlanArg4='{{item.vlanArg4}}'
  with_items: "{{test_vlan_data6}}"

- name: Test Vlan - ip igmp snooping mrouter interface port-aggregation23
  cnos_vlan:  host={{ inventory_hostname }} username={{ hostvars[inventory_hostname]['username']}} password={{ hostvars[inventory_hostname]['password']}} deviceType={{ hostvars[inventory_hostname]['deviceType']}} enablePassword={{ hostvars[inventory_hostname]['enablePassword']}} outputfile=./results/test_vlan_{{ inventory_hostname }}_output.txt vlanArg1='{{item.vlanArg1}}' vlanArg2='{{item.vlanArg2}}' vlanArg3='{{item.vlanArg3}}' vlanArg4='{{item.vlanArg4}}'  vlanArg5='{{item.vlanArg5}}'
  with_items: "{{test_vlan_data7}}"

#In the vars/main.yml will look like this

---
demo_template_data:
  - {vlanid1: 13, slot_chassis_number1: "1/1-2", portchannel_interface_number1: 100, portchannel_mode1: "active"}
test_vlan_data1:
  - {vlanArg1: 13, vlanArg2: "name", vlanArg3: "anil"}
test_vlan_data2:
  - {vlanArg1: 13, vlanArg2: "flood", vlanArg3: "ipv4"}
test_vlan_data3:
  - {vlanArg1: 13, vlanArg2: "state", vlanArg3: "active"}
test_vlan_data4:
  - {vlanArg1: "access-map", vlanArg2: "anil", vlanArg3: "statistics"}
test_vlan_data5:
  - {vlanArg1: "access-map", vlanArg2: "anil", vlanArg3: "action", vlanArg4: "forward"}
test_vlan_data6:
  - {vlanArg1: 13, vlanArg2: "ip", vlanArg3: "query-interval", vlanArg4: 1313}
test_vlan_data7:
  - {vlanArg1: 13, vlanArg2: "ip", vlanArg3: "mrouter", vlanArg4: "port-aggregation", vlanArg5: 23}

#In the inventory file u specify like this
inventory sample: |
    [cnos_vlan_sample]
    10.241.107.39  username=<username> password=<password> deviceType=g8272_cnos enablePassword: anil 
    10.241.107.40  username=<username> password=<password> deviceType=g8272_cnos 

'''

RETURN = '''
return value: |
    On successful execution, the method returns and empty string with a message "VLAN configurations are successful" 
    in json format. But upon any failure, the output will be the error display string. You may have to rectify the 
    error and try again..

'''
#---- Documentation Ends ----------------------------------------------------#
#---- Logic Start ------------------------------------------------------------###
#

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
    import cnos
    HAS_LIB=True
except:
    HAS_LIB=False

#
# load Ansible module
#
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict

#
def  main():
    #
    # Define parameters for vlan creation entry
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True,no_log=True),
            enablePassword=dict(required=False,no_log=True),
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
    vlanArg1= module.params['vlanArg1']
    vlanArg2 = module.params['vlanArg2']
    vlanArg3= module.params['vlanArg3']
    vlanArg4 = module.params['vlanArg4']
    vlanArg5 = module.params['vlanArg5']
    outputfile =  module.params['outputfile']
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
    output = output + cnos.waitForDeviceResponse("\n",">", 2, remote_conn)
    
    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)
        
    #Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n","#", 2, remote_conn)
        
    #Go to config mode
    output = output + cnos.waitForDeviceResponse("configure d\n","(config)#", 2, remote_conn)
    
    #Send the CLi command
    #output = output + cnos.createVlan(vlanid,vlanname,"(config)#", 2, remote_conn)
    output = output + cnos.vlanConfig(remote_conn, deviceType, "(config)#", 2, vlanArg1, vlanArg2, vlanArg3, vlanArg4, vlanArg5)
    
    #Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()
    
    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg == None):
        module.exit_json(changed=True, msg="VLAN configuration is accomplished ")
    else:
        module.fail_json(msg=errorMsg)
    

if __name__ == '__main__':
        main()
                                   
