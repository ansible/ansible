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
short_description: Manage VLAN resources and attributes on devices running
 Lenovo CNOS
description:
    - This module allows you to work with VLAN related configurations. The
     operators used are overloaded to ensure control over switch VLAN
     configurations. The first level of VLAN configuration allows to set up the
     VLAN range, the VLAN tag persistence, a VLAN access map and access map
     filter. After passing this level, there are five VLAN arguments that will
     perform further configurations. They are vlanArg1, vlanArg2, vlanArg3,
     vlanArg4, and vlanArg5. The value of vlanArg1 will determine the way
     following arguments will be evaluated. This module uses SSH to manage
     network device configuration. The results of the operation will be placed
     in a directory named 'results' that must be created by the user in their
     local directory to where the playbook is run. For more information about
     this module from Lenovo and customizing it usage for your use cases,
     please visit
     U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_vlan.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
  vlanArg1:
    description:
      - This is an overloaded vlan first argument. Usage of this argument can
        be found is the User Guide referenced above.
    required: true
    choices: [access-map, dot1q, filter, <1-3999> VLAN ID 1-3999 or range]
  vlanArg2:
    description:
      - This is an overloaded vlan second argument. Usage of this argument can
        be found is the User Guide referenced above.
    choices: [VLAN Access Map name,egress-only,name, flood,state, ip]
  vlanArg3:
    description:
      - This is an overloaded vlan third argument. Usage of this argument can
        be found is the User Guide referenced above.
    choices: [action, match, statistics, enter VLAN id or range of vlan,
              ascii name for the VLAN, ipv4 or ipv6, active or suspend,
              fast-leave, last-member-query-interval, mrouter, querier,
              querier-timeout, query-interval, query-max-response-time,
              report-suppression, robustness-variable, startup-query-count,
              startup-query-interval, static-group]
  vlanArg4:
    description:
      - This is an overloaded vlan fourth argument. Usage of this argument can
        be found is the User Guide referenced above.
    choices: [drop or forward or redirect, ip or mac,Interval in seconds,
              ethernet, port-aggregation, Querier IP address,
              Querier Timeout in seconds, Query Interval in seconds,
              Query Max Response Time in seconds,  Robustness Variable value,
              Number of queries sent at startup, Query Interval at startup]
  vlanArg5:
    description:
      - This is an overloaded vlan fifth argument. Usage of this argument can
        be found is the User Guide referenced above.
    choices: [access-list name, Slot/chassis number, Port Aggregation Number]

'''
EXAMPLES = '''

Tasks: The following are examples of using the module cnos_vlan. These are
       written in the main.yml file of the tasks directory.
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


def vlanAccessMapConfig(module, cmd):
    retVal = ''
    # Wait time to get response from server
    command = ''
    vlanArg3 = module.params['vlanArg3']
    vlanArg4 = module.params['vlanArg4']
    vlanArg5 = module.params['vlanArg5']
    deviceType = module.params['deviceType']
    if(vlanArg3 == "action"):
        command = command + vlanArg3 + ' '
        value = cnos.checkSanityofVariable(
            deviceType, "vlan_accessmap_action", vlanArg4)
        if(value == "ok"):
            command = command + vlanArg4
        else:
            retVal = "Error-135"
            return retVal
    elif(vlanArg3 == "match"):
        command = command + vlanArg3 + ' '
        if(vlanArg4 == "ip" or vlanArg4 == "mac"):
            command = command + vlanArg4 + ' address '
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_access_map_name", vlanArg5)
            if(value == "ok"):
                command = command + vlanArg5
            else:
                retVal = "Error-136"
                return retVal
        else:
            retVal = "Error-137"
            return retVal
    elif(vlanArg3 == "statistics"):
        command = vlanArg3 + " per-entry"
    else:
        retVal = "Error-138"
        return retVal

    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    # debugOutput(command)
    return retVal
# EOM


def checkVlanNameNotAssigned(module, prompt, answer):
    retVal = "ok"
    vlanId = module.params['vlanArg1']
    vlanName = module.params['vlanArg3']
    command = "show vlan id " + vlanId
    cmd = [{'command': command, 'prompt': None, 'answer': None}]
    retVal = str(cnos.run_cnos_commands(module, cmd))
    if(retVal.find('Error') != -1):
        command = "display vlan id " + vlanId
        retVal = str(cnos.run_cnos_commands(module, cmd))
    if(retVal.find(vlanName) != -1):
        return "Nok"
    else:
        return "ok"
# EOM


# Utility Method to create vlan
def createVlan(module, prompt, answer):

    # vlan config command happens here. It creates if not present
    vlanArg1 = module.params['vlanArg1']
    vlanArg2 = module.params['vlanArg2']
    vlanArg3 = module.params['vlanArg3']
    vlanArg4 = module.params['vlanArg4']
    vlanArg5 = module.params['vlanArg5']
    deviceType = module.params['deviceType']
    retVal = ''
    command = 'vlan ' + vlanArg1
    # debugOutput(command)
    cmd = [{'command': command, 'prompt': None, 'answer': None}]
    command = ""
    if(vlanArg2 == "name"):
        # debugOutput("name")
        command = vlanArg2 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlan_name", vlanArg3)
        if(value == "ok"):
            value = checkVlanNameNotAssigned(module, prompt, answer)
            if(value == "ok"):
                command = command + vlanArg3
            else:
                retVal = retVal + 'VLAN Name is already assigned \n'
                command = "\n"
        else:
            retVal = "Error-139"
            return retVal
    elif (vlanArg2 == "flood"):
        # debugOutput("flood")
        command = vlanArg2 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlan_flood", vlanArg3)
        if(value == "ok"):
            command = command + vlanArg3
        else:
            retVal = "Error-140"
            return retVal

    elif(vlanArg2 == "state"):
        # debugOutput("state")
        command = vlanArg2 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlan_state", vlanArg3)
        if(value == "ok"):
            command = command + vlanArg3
        else:
            retVal = "Error-141"
            return retVal

    elif(vlanArg2 == "ip"):
        # debugOutput("ip")
        command = vlanArg2 + " igmp snooping "
        # debugOutput("vlanArg3")
        if(vlanArg3 is None or vlanArg3 == ""):
            # debugOutput("None or empty")
            command = command.strip()
        elif(vlanArg3 == "fast-leave"):
            # debugOutput("fast-leave")
            command = command + vlanArg3

        elif (vlanArg3 == "last-member-query-interval"):
            # debugOutput("last-member-query-interval")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_last_member_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-142"
                return retVal

        elif (vlanArg3 == "querier"):
            # debugOutput("querier")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(deviceType,
                                               "vlan_querier", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-143"
                return retVal
        elif (vlanArg3 == "querier-timeout"):
            # debugOutput("querier-timeout")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_querier_timeout", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-144"
                return retVal
        elif (vlanArg3 == "query-interval"):
            # debugOutput("query-interval")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-145"
                return retVal
        elif (vlanArg3 == "query-max-response-time"):
            # debugOutput("query-max-response-time")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_query_max_response_time", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-146"
                return retVal
        elif (vlanArg3 == "report-suppression"):
            # debugOutput("report-suppression")
            command = command + vlanArg3

        elif (vlanArg3 == "robustness-variable"):
            # debugOutput("robustness-variable")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_startup_query_count", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-148"
                return retVal
        elif (vlanArg3 == "startup-query-interval"):
            # debugOutput("startup-query-interval")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_startup_query_interval", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-149"
                return retVal
        elif (vlanArg3 == "static-group"):
            retVal = "Error-102"
            return retVal
        elif (vlanArg3 == "version"):
            # debugOutput("version")
            command = command + vlanArg3 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_snooping_version", vlanArg4)
            if(value == "ok"):
                command = command + vlanArg4
            else:
                retVal = "Error-150"
                return retVal
        elif (vlanArg3 == "mrouter"):
            # debugOutput("mrouter")
            command = command + vlanArg3 + " interface "
            if(vlanArg4 == "ethernet"):
                command = command + vlanArg4 + " "
                value = cnos.checkSanityofVariable(
                    deviceType, "vlan_ethernet_interface", vlanArg5)
                if(value == "ok"):
                    command = command + vlanArg5
                else:
                    retVal = "Error-151"
                    return retVal
            elif(vlanArg4 == "port-aggregation"):
                command = command + vlanArg4 + " "
                value = cnos.checkSanityofVariable(
                    deviceType, "vlan_portagg_number", vlanArg5)
                if(value == "ok"):
                    command = command + vlanArg5
                else:
                    retVal = "Error-152"
                    return retVal
            else:
                retVal = "Error-153"
                return retVal
        else:
            command = command + vlanArg3

    else:
        retVal = "Error-154"
        return retVal
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    # debugOutput(command)
    return retVal
# EOM


def vlanConfig(module, prompt, answer):

    retVal = ''
    # Wait time to get response from server
    vlanArg1 = module.params['vlanArg1']
    vlanArg2 = module.params['vlanArg2']
    vlanArg3 = module.params['vlanArg3']
    vlanArg4 = module.params['vlanArg4']
    vlanArg5 = module.params['vlanArg5']
    deviceType = module.params['deviceType']
    # vlan config command happens here.
    command = 'vlan '

    if(vlanArg1 == "access-map"):
        # debugOutput("access-map ")
        command = command + vlanArg1 + ' '
        value = cnos.checkSanityofVariable(
            deviceType, "vlan_access_map_name", vlanArg2)
        if(value == "ok"):
            command = command + vlanArg2
            # debugOutput(command)
            cmd = [{'command': command, 'prompt': None, 'answer': None}]
            retVal = retVal + vlanAccessMapConfig(module, cmd)
            return retVal
        else:
            retVal = "Error-130"
            return retVal

    elif(vlanArg1 == "dot1q"):
        # debugOutput("dot1q")
        command = command + vlanArg1 + " tag native "
        if(vlanArg2 is not None):
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_dot1q_tag", vlanArg2)
            if(value == "ok"):
                command = command + vlanArg2
            else:
                retVal = "Error-131"
                return retVal

    elif(vlanArg1 == "filter"):
        # debugOutput( "filter")
        command = command + vlanArg1 + " "
        if(vlanArg2 is not None):
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_filter_name", vlanArg2)
            if(value == "ok"):
                command = command + vlanArg2 + " vlan-list "
                value = cnos.checkSanityofVariable(deviceType, "vlan_id",
                                                   vlanArg3)
                if(value == "ok"):
                    command = command + vlanArg3
                else:
                    value = cnos.checkSanityofVariable(
                        deviceType, "vlan_id_range", vlanArg3)
                    if(value == "ok"):
                        command = command + vlanArg3
                    else:
                        retVal = "Error-133"
                    return retVal
            else:
                retVal = "Error-132"
                return retVal

    else:
        value = cnos.checkSanityofVariable(deviceType, "vlan_id", vlanArg1)
        if(value == "ok"):
            retVal = createVlan(module, '(config-vlan)#', None)
            return retVal
        else:
            value = cnos.checkSanityofVariable(
                deviceType, "vlan_id_range", vlanArg1)
            if(value == "ok"):
                retVal = createVlan(module, '(config-vlan)#', None)
                return retVal
            retVal = "Error-133"
            return retVal

    # debugOutput(command)
    cmd = [{'command': command, 'prompt': None, 'answer': None}]
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    return retVal
# EOM


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

    outputfile = module.params['outputfile']

    output = ""

    # Send the CLi command
    output = output + str(vlanConfig(module, "(config)#", None))

    # Save it operation details into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True,
                         msg="VLAN configuration is accomplished")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
