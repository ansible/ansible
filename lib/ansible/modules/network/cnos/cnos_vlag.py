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
# Module to send VLAG commands to Lenovo Switches
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_vlag
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage VLAG resources and attributes on devices running
 Lenovo CNOS
description:
    - This module allows you to work with virtual Link Aggregation Groups
     (vLAG) related configurations. The operators used are overloaded to ensure
     control over switch vLAG configurations. Apart from the regular device
     connection related attributes, there are four vLAG arguments which are
     overloaded variables that will perform further configurations. They are
     vlagArg1, vlagArg2, vlagArg3, and vlagArg4. For more details on how to use
     these arguments, see [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the
     playbook is run.
version_added: "2.3"
extends_documentation_fragment: cnos
options:
  vlagArg1:
    description:
      - This is an overloaded vlag first argument. Usage of this argument can
        be found is the User Guide referenced above.
    required: Yes
    default: Null
    choices: [enable, auto-recovery,config-consistency,isl,mac-address-table,
              peer-gateway,priority,startup-delay,tier-id,vrrp,instance,hlthchk]
  vlagArg2:
    description:
      - This is an overloaded vlag second argument. Usage of this argument can
        be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [Interval in seconds,disable or strict,Port Aggregation Number,
              VLAG priority,Delay time in seconds,VLAG tier-id value,
              VLAG instance number,keepalive-attempts,keepalive-interval,
              retry-interval,peer-ip]
  vlagArg3:
    description:
      - This is an overloaded vlag third argument. Usage of this argument can
        be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [enable or port-aggregation,Number of keepalive attempts,
              Interval in seconds,Interval in seconds,
              VLAG health check peer IP4 address]
  vlagArg4:
    description:
      - This is an overloaded vlag fourth argument. Usage of this argument can
        be found is the User Guide referenced above.
    required: No
    default: Null
    choices: [Port Aggregation Number,default or management]

'''
EXAMPLES = '''

Tasks : The following are examples of using the module cnos_vlag. These are
        written in the main.yml file of the tasks directory.
---
- name: Test Vlag  - enable
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "enable"

- name: Test Vlag - autorecovery
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "auto-recovery"
      vlagArg2: 266

- name: Test Vlag - config-consistency
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "config-consistency"
      vlagArg2: "strict"

- name: Test Vlag - isl
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "isl"
      vlagArg2: 23

- name: Test Vlag  - mac-address-table
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "mac-address-table"

- name: Test Vlag - peer-gateway
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "peer-gateway"

- name: Test Vlag - priority
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "priority"
      vlagArg2: 1313

- name: Test Vlag - startup-delay
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "startup-delay"
      vlagArg2: 323

- name: Test Vlag  - tier-id
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "tier-id"
      vlagArg2: 313

- name: Test Vlag - vrrp
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "vrrp"

- name: Test Vlag - instance
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "instance"
      vlagArg2: 33
      vlagArg3: 333

- name: Test Vlag - instance2
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "instance"
      vlagArg2: "33"

- name: Test Vlag  - keepalive-attempts
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "keepalive-attempts"
      vlagArg3: 13

- name: Test Vlag - keepalive-interval
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "keepalive-interval"
      vlagArg3: 131

- name: Test Vlag - retry-interval
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "retry-interval"
      vlagArg3: 133

- name: Test Vlag - peer ip
  cnos_vlag:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType']}}"
      outputfile: "./results/cnos_vlag_{{ inventory_hostname }}_output.txt"
      vlagArg1: "hlthchk"
      vlagArg2: "peer-ip"
      vlagArg3: "1.2.3.4"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "vLAG configurations accomplished"
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
except Exception:
    HAS_LIB = False

from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def vlagConfig(module, prompt, answer):

    retVal = ''
    # vlag config command happens here.
    command = 'vlag '

    vlagArg1 = module.params['vlagArg1']
    vlagArg2 = module.params['vlagArg2']
    vlagArg3 = module.params['vlagArg3']
    vlagArg4 = module.params['vlagArg4']
    deviceType = module.params['deviceType']

    if(vlagArg1 == "enable"):
        # debugOutput("enable")
        command = command + vlagArg1 + " "

    elif(vlagArg1 == "auto-recovery"):
        # debugOutput("auto-recovery")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "vlag_auto_recovery", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-160"
            return retVal

    elif(vlagArg1 == "config-consistency"):
        # debugOutput("config-consistency")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "vlag_config_consistency", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-161"
            return retVal

    elif(vlagArg1 == "isl"):
        # debugOutput("isl")
        command = command + vlagArg1 + " port-channel "
        value = cnos.checkSanityofVariable(
            deviceType, "vlag_port_aggregation", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-162"
            return retVal

    elif(vlagArg1 == "mac-address-table"):
        # debugOutput("mac-address-table")
        command = command + vlagArg1 + " refresh"

    elif(vlagArg1 == "peer-gateway"):
        # debugOutput("peer-gateway")
        command = command + vlagArg1 + " "

    elif(vlagArg1 == "priority"):
        # debugOutput("priority")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlag_priority",
                                           vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-163"
            return retVal

    elif(vlagArg1 == "startup-delay"):
        # debugOutput("startup-delay")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "vlag_startup_delay", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-164"
            return retVal

    elif(vlagArg1 == "tier-id"):
        # debugOutput("tier-id")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlag_tier_id", vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
        else:
            retVal = "Error-165"
            return retVal

    elif(vlagArg1 == "vrrp"):
        # debugOutput("vrrp")
        command = command + vlagArg1 + " active"

    elif(vlagArg1 == "instance"):
        # debugOutput("instance")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "vlag_instance",
                                           vlagArg2)
        if(value == "ok"):
            command = command + vlagArg2
            if(vlagArg3 is not None):
                command = command + " port-channel "
                value = cnos.checkSanityofVariable(
                    deviceType, "vlag_port_aggregation", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg3
                else:
                    retVal = "Error-162"
                    return retVal
            else:
                command = command + " enable "
        else:
            retVal = "Error-166"
            return retVal

    elif(vlagArg1 == "hlthchk"):
        # debugOutput("hlthchk")
        command = command + vlagArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "vlag_hlthchk_options", vlagArg2)
        if(value == "ok"):
            if(vlagArg2 == "keepalive-attempts"):
                value = cnos.checkSanityofVariable(
                    deviceType, "vlag_keepalive_attempts", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-167"
                    return retVal
            elif(vlagArg2 == "keepalive-interval"):
                value = cnos.checkSanityofVariable(
                    deviceType, "vlag_keepalive_interval", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-168"
                    return retVal
            elif(vlagArg2 == "retry-interval"):
                value = cnos.checkSanityofVariable(
                    deviceType, "vlag_retry_interval", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                else:
                    retVal = "Error-169"
                    return retVal
            elif(vlagArg2 == "peer-ip"):
                # Here I am not taking care of IPV6 option.
                value = cnos.checkSanityofVariable(
                    deviceType, "vlag_peerip", vlagArg3)
                if(value == "ok"):
                    command = command + vlagArg2 + " " + vlagArg3
                    if(vlagArg4 is not None):
                        value = cnos.checkSanityofVariable(
                            deviceType, "vlag_peerip_vrf", vlagArg4)
                        if(value == "ok"):
                            command = command + " vrf " + vlagArg4
                        else:
                            retVal = "Error-170"
                            return retVal
        else:
            retVal = "Error-171"
            return retVal

    else:
        retVal = "Error-172"
        return retVal

    # debugOutput(command)
    cmd = [{'command': command, 'prompt': None, 'answer': None}]
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    return retVal
# EOM


def main():
    #
    # Define parameters for vlag creation entry
    #
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=False),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            vlagArg1=dict(required=True),
            vlagArg2=dict(required=False),
            vlagArg3=dict(required=False),
            vlagArg4=dict(required=False),),
        supports_check_mode=False)

    outputfile = module.params['outputfile']
    output = ""

    # Send the CLi command
    output = output + str(vlagConfig(module, '(config)#', None))

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="VLAG configurations accomplished")
    else:
        module.fail_json(msg=errorMsg)


if __name__ == '__main__':
    main()
