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
author: "Anil Kumar Muraleedharan (@amuraleedhar)"
short_description: Manage BGP resources and attributes on devices running CNOS
description:
    - This module allows you to work with Border Gateway Protocol (BGP) related
     configurations. The operators used are overloaded to ensure control over
     switch BGP configurations. This module is invoked using method with
     asNumber as one of its arguments. The first level of the BGP configuration
     allows to set up an AS number, with the following attributes going
     into various configuration operations under the context of BGP.
     After passing this level, there are eight BGP arguments that will perform
     further configurations. They are bgpArg1, bgpArg2, bgpArg3, bgpArg4,
     bgpArg5, bgpArg6, bgpArg7, and bgpArg8. For more details on how to use
     these arguments, see [Overloaded Variables].
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the
     playbook is run.
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
            - This is an overloaded bgp first argument. Usage of this argument
              can be found is the User Guide referenced above.
        required: Yes
        default: Null
        choices: [address-family,bestpath,bgp,cluster-id,confederation,
                  enforce-first-as,fast-external-failover,graceful-restart,
                  graceful-restart-helper,log-neighbor-changes,
                  maxas-limit,neighbor,router-id,shutdown,synchronization,
                  timers,vrf]
    bgpArg2:
        description:
            - This is an overloaded bgp second argument. Usage of this argument
              can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [ipv4 or ipv6, always-compare-med,compare-confed-aspath,
                  compare-routerid,dont-compare-originator-id,tie-break-on-age,
                  as-path,med,identifier,peers]
    bgpArg3:
        description:
            - This is an overloaded bgp third argument. Usage of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [aggregate-address,client-to-client,dampening,distance,
                  maximum-paths,network,nexthop,redistribute,save,
                  synchronization,ignore or multipath-relax,
                  confed or missing-as-worst or non-deterministic or
                  remove-recv-med or remove-send-med]
    bgpArg4:
        description:
            - This is an overloaded bgp fourth argument. Usage of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Aggregate prefix, Reachability Half-life time,route-map,
                  Distance for routes ext,ebgp or ibgp,IP prefix <network>,
                  IP prefix <network>/<length>, synchronization,
                  Delay value, direct, ospf, static, memory]
    bgpArg5:
        description:
            - This is an overloaded bgp fifth argument. Usage of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [as-set, summary-only, Value to start reusing a route,
                  Distance for routes internal, Supported multipath numbers,
                  backdoor, map, route-map ]
    bgpArg6:
        description:
            - This is an overloaded bgp sixth argument. Usage of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [summary-only,as-set, route-map name,
                  Value to start suppressing a route, Distance local routes,
                  Network mask, Pointer to route-map entries]
    bgpArg7:
        description:
            - This is an overloaded bgp seventh argument. Use of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Maximum duration to suppress a stable route(minutes),
                  backdoor,route-map, Name of the route map ]
    bgpArg8:
        description:
            - This is an overloaded bgp eigth argument. Usage of this argument
             can be found is the User Guide referenced above.
        required: No
        default: Null
        choices: [Un-reachability Half-life time for the penalty(minutes),
                  backdoor]
'''
EXAMPLES = '''
Tasks: The following are examples of using the module cnos_bgp. These are
 written in the main.yml file of the tasks directory.
---
- name: Test BGP  - neighbor
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
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
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "neighbor"
      bgpArg2: "10.241.107.40"
      bgpArg3: 13
      bgpArg4: "bfd"

- name: Test BGP  - address-family - dampening
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
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
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "address-family"
      bgpArg2: "ipv4"
      bgpArg3: "network"
      bgpArg4: "1.2.3.4/5"
      bgpArg5: "backdoor"

- name: Test BGP - bestpath - always-compare-med
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bestpath"
      bgpArg2: "always-compare-med"

- name: Test BGP - bestpath-compare-confed-aspat
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bestpath"
      bgpArg2: "compare-confed-aspath"

- name: Test BGP - bgp
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "bgp"
      bgpArg2: 33

- name: Test BGP  - cluster-id
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "cluster-id"
      bgpArg2: "1.2.3.4"

- name: Test BGP - confederation-identifier
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "confederation"
      bgpArg2: "identifier"
      bgpArg3: 333

- name: Test BGP - enforce-first-as
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "enforce-first-as"

- name: Test BGP - fast-external-failover
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "fast-external-failover"

- name: Test BGP  - graceful-restart
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "graceful-restart"
      bgpArg2: 333

- name: Test BGP - graceful-restart-helper
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "graceful-restart-helper"

- name: Test BGP - maxas-limit
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "maxas-limit"
      bgpArg2: 333

- name: Test BGP  - neighbor
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
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
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "router-id"
      bgpArg2: "1.2.3.4"

- name: Test BGP - synchronization
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "synchronization"

- name: Test BGP - timers
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "timers"
      bgpArg2: 333
      bgpArg3: 3333

- name: Test BGP - vrf
  cnos_bgp:
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      outputfile: "./results/test_bgp_{{ inventory_hostname }}_output.txt"
      asNum: 33
      bgpArg1: "vrf"

'''
RETURN = '''
msg:
  description: Success or failure message. Upon any failure, the method returns
   an error display string.
  returned: always
  type: str
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


def bgpNeighborConfig(module, cmd, prompt, answer):
    retVal = ''
    command = ''
    bgpNeighborArg1 = module.params['bgpArg4']
    bgpNeighborArg2 = module.params['bgpArg5']
    bgpNeighborArg3 = module.params['bgpArg6']
    bgpNeighborArg4 = module.params['bgpArg7']
    bgpNeighborArg5 = module.params['bgpArg8']
    deviceType = module.params['deviceType']

    if(bgpNeighborArg1 == "address-family"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_address_family", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " unicast"
            # debugOutput(command)
            inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
            cmd.extend(inner_cmd)
            retVal = retVal + bgpNeighborAFConfig(module, cmd, '(config-router-neighbor-af)#', answer)
            return retVal
        else:
            retVal = "Error-316"
            return retVal

    elif(bgpNeighborArg1 == "advertisement-interval"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "bfd"):
        command = command + bgpNeighborArg1 + " "
        if(bgpNeighborArg2 is not None and bgpNeighborArg2 == "mutihop"):
            command = command + bgpNeighborArg2

    elif(bgpNeighborArg1 == "connection-retry-time"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_connection_retrytime", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-315"
            return retVal

    elif(bgpNeighborArg1 == "description"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_description", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-314"
            return retVal

    elif(bgpNeighborArg1 == "disallow-infinite-holdtime"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "dont-capability-negotiate"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "dynamic-capability"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "ebgp-multihop"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_maxhopcount", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-313"
            return retVal

    elif(bgpNeighborArg1 == "interface"):
        command = command + bgpNeighborArg1 + " "
        # TBD

    elif(bgpNeighborArg1 == "local-as"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_local_as", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " "
            if(bgpNeighborArg3 is not None and
                    bgpNeighborArg3 == "no-prepend"):
                command = command + bgpNeighborArg3 + " "
                if(bgpNeighborArg4 is not None and
                        bgpNeighborArg4 == "replace-as"):
                    command = command + bgpNeighborArg4 + " "
                    if(bgpNeighborArg5 is not None and
                            bgpNeighborArg5 == "dual-as"):
                        command = command + bgpNeighborArg5
                    else:
                        command = command.strip()
                else:
                    command = command.strip()
            else:
                command = command.strip()
        else:
            retVal = "Error-312"
            return retVal

    elif(bgpNeighborArg1 == "maximum-peers"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_maxpeers", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-311"
            return retVal

    elif(bgpNeighborArg1 == "password"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_password", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-310"
            return retVal

    elif(bgpNeighborArg1 == "remove-private-AS"):
        command = command + bgpNeighborArg1

    elif(bgpNeighborArg1 == "timers"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_timers_Keepalive", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "bgp_neighbor_timers_holdtime", bgpNeighborArg3)
            if(value == "ok"):
                command = command + bgpNeighborArg3
            else:
                retVal = "Error-309"
                return retVal
        else:
            retVal = "Error-308"
            return retVal

    elif(bgpNeighborArg1 == "transport"):
        command = command + bgpNeighborArg1 + " connection-mode passive "

    elif(bgpNeighborArg1 == "ttl-security"):
        command = command + bgpNeighborArg1 + " hops "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_ttl_hops", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-307"
            return retVal

    elif(bgpNeighborArg1 == "update-source"):
        command = command + bgpNeighborArg1 + " "
        if(bgpNeighborArg2 is not None):
            value = cnos.checkSanityofVariable(
                deviceType, "bgp_neighbor_update_options", bgpNeighborArg2)
            if(value == "ok"):
                command = command + bgpNeighborArg2 + " "
                if(bgpNeighborArg2 == "ethernet"):
                    value = cnos.checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_ethernet",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-304"
                        return retVal
                elif(bgpNeighborArg2 == "loopback"):
                    value = cnos.checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_loopback",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-305"
                        return retVal
                else:
                    value = cnos.checkSanityofVariable(
                        deviceType, "bgp_neighbor_update_vlan",
                        bgpNeighborArg3)
                    if(value == "ok"):
                        command = command + bgpNeighborArg3
                    else:
                        retVal = "Error-306"
                        return retVal
            else:
                command = command + bgpNeighborArg2
        else:
            retVal = "Error-303"
            return retVal

    elif(bgpNeighborArg1 == "weight"):
        command = command + bgpNeighborArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_weight", bgpNeighborArg2)
        if(value == "ok"):
            command = command + bgpNeighborArg2
        else:
            retVal = "Error-302"
            return retVal

    else:
        retVal = "Error-301"
        return retVal

    # debugOutput(command)
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    command = "exit \n"
    return retVal
# EOM


def bgpNeighborAFConfig(module, cmd, prompt, answer):
    retVal = ''
    command = ''
    bgpNeighborAFArg1 = module.params['bgpArg6']
    bgpNeighborAFArg2 = module.params['bgpArg7']
    bgpNeighborAFArg3 = module.params['bgpArg8']
    deviceType = module.params['deviceType']
    if(bgpNeighborAFArg1 == "allowas-in"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None):
            value = cnos.checkSanityofVariable(
                deviceType, "bgp_neighbor_af_occurances", bgpNeighborAFArg2)
            if(value == "ok"):
                command = command + bgpNeighborAFArg2
            else:
                retVal = "Error-325"
                return retVal

    elif(bgpNeighborAFArg1 == "default-originate"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None and bgpNeighborAFArg2 == "route-map"):
            command = command + bgpNeighborAFArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
            if(value == "ok"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-324"
                return retVal

    elif(bgpNeighborAFArg1 == "filter-list"):
        command = command + bgpNeighborAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_af_filtername", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 == "in" or bgpNeighborAFArg3 == "out"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-323"
                return retVal
        else:
            retVal = "Error-322"
            return retVal

    elif(bgpNeighborAFArg1 == "maximum-prefix"):
        command = command + bgpNeighborAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_af_maxprefix", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 is not None):
                command = command + bgpNeighborAFArg3
            else:
                command = command.strip()
        else:
            retVal = "Error-326"
            return retVal

    elif(bgpNeighborAFArg1 == "next-hop-self"):
        command = command + bgpNeighborAFArg1

    elif(bgpNeighborAFArg1 == "prefix-list"):
        command = command + bgpNeighborAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_af_prefixname", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2 + " "
            if(bgpNeighborAFArg3 == "in" or bgpNeighborAFArg3 == "out"):
                command = command + bgpNeighborAFArg3
            else:
                retVal = "Error-321"
                return retVal
        else:
            retVal = "Error-320"
            return retVal

    elif(bgpNeighborAFArg1 == "route-map"):
        command = command + bgpNeighborAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2
        else:
            retVal = "Error-319"
            return retVal
    elif(bgpNeighborAFArg1 == "route-reflector-client"):
        command = command + bgpNeighborAFArg1

    elif(bgpNeighborAFArg1 == "send-community"):
        command = command + bgpNeighborAFArg1 + " "
        if(bgpNeighborAFArg2 is not None and bgpNeighborAFArg2 == "extended"):
            command = command + bgpNeighborAFArg2

    elif(bgpNeighborAFArg1 == "soft-reconfiguration"):
        command = command + bgpNeighborAFArg1 + " inbound"

    elif(bgpNeighborAFArg1 == "unsuppress-map"):
        command = command + bgpNeighborAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_neighbor_af_routemap", bgpNeighborAFArg2)
        if(value == "ok"):
            command = command + bgpNeighborAFArg2
        else:
            retVal = "Error-318"
            return retVal

    else:
        retVal = "Error-317"
        return retVal

    # debugOutput(command)
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    return retVal
# EOM


def bgpAFConfig(module, cmd, prompt, answer):
    retVal = ''
    command = ''
    bgpAFArg1 = module.params['bgpArg3']
    bgpAFArg2 = module.params['bgpArg4']
    bgpAFArg3 = module.params['bgpArg5']
    bgpAFArg4 = module.params['bgpArg6']
    bgpAFArg5 = module.params['bgpArg7']
    bgpAFArg6 = module.params['bgpArg8']
    deviceType = module.params['deviceType']
    if(bgpAFArg1 == "aggregate-address"):
        command = command + bgpAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_aggregate_prefix", bgpAFArg2)
        if(value == "ok"):
            if(bgpAFArg2 is None):
                command = command.strip()
            elif(bgpAFArg2 == "as-set" or bgpAFArg2 == "summary-only"):
                command = command + bgpAFArg2 + " "
                if((bgpAFArg3 is not None) and (bgpAFArg2 == "as-set")):
                    command = command + "summary-only"
            else:
                retVal = "Error-297"
                return retVal
        else:
            retVal = "Error-296"
            return retVal

    elif(bgpAFArg1 == "client-to-client"):
        command = command + bgpAFArg1 + " reflection "

    elif(bgpAFArg1 == "dampening"):
        command = command + bgpAFArg1 + " "
        if(bgpAFArg2 == "route-map"):
            command = command + bgpAFArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "addrfamily_routemap_name", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3
            else:
                retVal = "Error-196"
                return retVal
        elif(bgpAFArg2 is not None):
            value = cnos.checkSanityofVariable(
                deviceType, "reachability_half_life", bgpAFArg2)
            if(value == "ok"):
                command = command + bgpAFArg2 + " "
                if(bgpAFArg3 is not None):
                    value1 = cnos.checkSanityofVariable(
                        deviceType, "start_reuse_route_value", bgpAFArg3)
                    value2 = cnos.checkSanityofVariable(
                        deviceType, "start_suppress_route_value", bgpAFArg4)
                    value3 = cnos.checkSanityofVariable(
                        deviceType, "max_duration_to_suppress_route",
                        bgpAFArg5)
                    if(value1 == "ok" and value2 == "ok" and value3 == "ok"):
                        command = command + bgpAFArg3 + " " + bgpAFArg4 + \
                            " " + bgpAFArg5 + " "
                        if(bgpAFArg6 is not None):
                            value = cnos.checkSanityofVariable(
                                deviceType,
                                "unreachability_halftime_for_penalty",
                                bgpAFArg6)
                            if(value == "ok"):
                                command = command + bgpAFArg6
                    else:
                        retVal = "Error-295"
                        return retVal
                else:
                    command = command.strip()
            else:
                retVal = "Error-294"
                return retVal

    elif(bgpAFArg1 == "distance"):
        command = command + bgpAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "distance_external_AS", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "distance_internal_AS", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3 + " "
                value = cnos.checkSanityofVariable(
                    deviceType, "distance_local_routes", bgpAFArg4)
                if(value == "ok"):
                    command = command + bgpAFArg4
                else:
                    retVal = "Error-291"
                    return retVal
            else:
                retVal = "Error-292"
                return retVal
        else:
            retVal = "Error-293"
            return retVal

    elif(bgpAFArg1 == "maximum-paths"):
        command = command + bgpAFArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "maxpath_option", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "maxpath_numbers", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3
            else:
                retVal = "Error-199"
                return retVal
        else:
            retVal = "Error-290"
            return retVal

    elif(bgpAFArg1 == "network"):
        command = command + bgpAFArg1 + " "
        if(bgpAFArg2 == "synchronization"):
            command = command + bgpAFArg2
        else:
            value = cnos.checkSanityofVariable(
                deviceType, "network_ip_prefix_with_mask", bgpAFArg2)
            if(value == "ok"):
                command = command + bgpAFArg2 + " "
                if(bgpAFArg3 is not None and bgpAFArg3 == "backdoor"):
                    command = command + bgpAFArg3
                elif(bgpAFArg3 is not None and bgpAFArg3 == "route-map"):
                    command = command + bgpAFArg3
                    value = cnos.checkSanityofVariable(
                        deviceType, "addrfamily_routemap_name", bgpAFArg4)
                    if(value == "ok"):
                        command = command + bgpAFArg4 + " "
                        if(bgpAFArg5 is not None and bgpAFArg5 == "backdoor"):
                            command = command + bgpAFArg5
                        else:
                            retVal = "Error-298"
                            return retVal
                    else:
                        retVal = "Error-196"
                        return retVal
                else:
                    command = command.strip()
            else:
                value = cnos.checkSanityofVariable(
                    deviceType, "network_ip_prefix_value", bgpAFArg2)
                if(value == "ok"):
                    command = command + bgpAFArg2 + " "
                    if(bgpAFArg3 is not None and bgpAFArg3 == "backdoor"):
                        command = command + bgpAFArg3
                    elif(bgpAFArg3 is not None and bgpAFArg3 == "route-map"):
                        command = command + bgpAFArg3
                        value = cnos.checkSanityofVariable(
                            deviceType, "addrfamily_routemap_name", bgpAFArg4)
                        if(value == "ok"):
                            command = command + bgpAFArg4 + " "
                            if(bgpAFArg5 is not None and
                                    bgpAFArg5 == "backdoor"):
                                command = command + bgpAFArg5
                            else:
                                retVal = "Error-298"
                                return retVal
                        else:
                            retVal = "Error-196"
                            return retVal
                    elif(bgpAFArg3 is not None and bgpAFArg3 == "mask"):
                        command = command + bgpAFArg3
                        value = cnos.checkSanityofVariable(
                            deviceType, "network_ip_prefix_mask", bgpAFArg4)
                        if(value == "ok"):
                            command = command + bgpAFArg4 + " "
                        else:
                            retVal = "Error-299"
                            return retVal
                    else:
                        command = command.strip()
                else:
                    retVal = "Error-300"
                    return retVal

    elif(bgpAFArg1 == "nexthop"):
        command = command + bgpAFArg1 + " trigger-delay critical "
        value = cnos.checkSanityofVariable(
            deviceType, "nexthop_crtitical_delay", bgpAFArg2)
        if(value == "ok"):
            command = command + bgpAFArg2 + " "
            value = cnos.checkSanityofVariable(
                deviceType, "nexthop_noncrtitical_delay", bgpAFArg3)
            if(value == "ok"):
                command = command + bgpAFArg3 + " "
            else:
                retVal = "Error-198"
                return retVal
        else:
            retVal = "Error-197"
            return retVal

    elif(bgpAFArg1 == "redistribute"):
        command = command + bgpAFArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "addrfamily_redistribute_option", bgpAFArg2)
        if(value == "ok"):
            if(bgpAFArg2 is not None):
                command = command + bgpAFArg2 + " " + "route-map "
                value = cnos.checkSanityofVariable(
                    deviceType, "addrfamily_routemap_name", bgpAFArg3)
                if(value == "ok"):
                    command = command + bgpAFArg3
                else:
                    retVal = "Error-196"
                    return retVal
        else:
            retVal = "Error-195"
            return retVal

    elif(bgpAFArg1 == "save" or bgpAFArg1 == "synchronization"):
        command = command + bgpAFArg1

    else:
        retVal = "Error-194"
        return retVal
    # debugOutput(command)
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    command = "exit \n"
    return retVal
# EOM


def bgpConfig(module, cmd, prompt, answer):
    retVal = ''
    command = ''
    bgpArg1 = module.params['bgpArg1']
    bgpArg2 = module.params['bgpArg2']
    bgpArg3 = module.params['bgpArg3']
    bgpArg4 = module.params['bgpArg4']
    bgpArg5 = module.params['bgpArg5']
    bgpArg6 = module.params['bgpArg6']
    bgpArg7 = module.params['bgpArg7']
    bgpArg8 = module.params['bgpArg8']
    asNum = module.params['asNum']
    deviceType = module.params['deviceType']
    # cnos.debugOutput(bgpArg1)
    if(bgpArg1 == "address-family"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_address_family", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2 + " " + "unicast \n"
            # debugOutput(command)
            inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
            cmd.extend(inner_cmd)
            retVal = retVal + bgpAFConfig(module, cmd, prompt, answer)
            return retVal
        else:
            retVal = "Error-178"
            return retVal

    elif(bgpArg1 == "bestpath"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        if(bgpArg2 == "always-compare-med"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "compare-confed-aspath"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "compare-routerid"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "dont-compare-originator-id"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "tie-break-on-age"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2
        elif(bgpArg2 == "as-path"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2 + " "
            if(bgpArg3 == "ignore" or bgpArg3 == "multipath-relax"):
                command = command + bgpArg3
            else:
                retVal = "Error-179"
                return retVal
        elif(bgpArg2 == "med"):
            # debugOutput(bgpArg2)
            command = command + bgpArg2 + " "
            if(bgpArg3 == "confed" or
               bgpArg3 == "missing-as-worst" or
               bgpArg3 == "non-deterministic" or
               bgpArg3 == "remove-recv-med" or
               bgpArg3 == "remove-send-med"):
                command = command + bgpArg3
            else:
                retVal = "Error-180"
                return retVal
        else:
            retVal = "Error-181"
            return retVal

    elif(bgpArg1 == "bgp"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " as-local-count "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_bgp_local_count", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-182"
            return retVal

    elif(bgpArg1 == "cluster-id"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "cluster_id_as_ip", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            value = cnos.checkSanityofVariable(
                deviceType, "cluster_id_as_number", bgpArg2)
            if(value == "ok"):
                command = command + bgpArg2
            else:
                retVal = "Error-183"
                return retVal

    elif(bgpArg1 == "confederation"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        if(bgpArg2 == "identifier"):
            value = cnos.checkSanityofVariable(
                deviceType, "confederation_identifier", bgpArg3)
            if(value == "ok"):
                command = command + bgpArg2 + " " + bgpArg3 + "\n"
            else:
                retVal = "Error-184"
                return retVal
        elif(bgpArg2 == "peers"):
            value = cnos.checkSanityofVariable(
                deviceType, "confederation_peers_as", bgpArg3)
            if(value == "ok"):
                command = command + bgpArg2 + " " + bgpArg3
            else:
                retVal = "Error-185"
                return retVal
        else:
            retVal = "Error-186"
            return retVal

    elif(bgpArg1 == "enforce-first-as"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "fast-external-failover"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "graceful-restart"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " stalepath-time "
        value = cnos.checkSanityofVariable(
            deviceType, "stalepath_delay_value", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-187"
            return retVal

    elif(bgpArg1 == "graceful-restart-helper"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "log-neighbor-changes"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "maxas-limit"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "maxas_limit_as", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-188"
            return retVal

    elif(bgpArg1 == "neighbor"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = cnos.checkSanityofVariable(
            deviceType, "neighbor_ipaddress", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
            if(bgpArg3 is not None):
                command = command + " remote-as "
                value = cnos.checkSanityofVariable(
                    deviceType, "neighbor_as", bgpArg3)
                if(value == "ok"):
                    # debugOutput(command)
                    command = command + bgpArg3
                    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
                    cmd.extend(inner_cmd)
                    retVal = retVal + bgpNeighborConfig(module, cmd, prompt, answer)
                    return retVal
        else:
            retVal = "Error-189"
            return retVal

    elif(bgpArg1 == "router-id"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " "
        value = cnos.checkSanityofVariable(deviceType, "router_id", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-190"
            return retVal

    elif(bgpArg1 == "shutdown"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "synchronization"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1

    elif(bgpArg1 == "timers"):
        # cnos.debugOutput(bgpArg3)
        command = command + bgpArg1 + " bgp "
        value = cnos.checkSanityofVariable(
            deviceType, "bgp_keepalive_interval", bgpArg2)
        if(value == "ok"):
            command = command + bgpArg2
        else:
            retVal = "Error-191"
            return retVal
        if(bgpArg3 is not None):
            value = cnos.checkSanityofVariable(deviceType, "bgp_holdtime", bgpArg3)
            if(value == "ok"):
                command = command + " " + bgpArg3
            else:
                retVal = "Error-192"
                return retVal
        else:
            retVal = "Error-192"
            return retVal

    elif(bgpArg1 == "vrf"):
        # debugOutput(bgpArg1)
        command = command + bgpArg1 + " default"
    else:
        # debugOutput(bgpArg1)
        retVal = "Error-192"
        return retVal
    # debugOutput(command)
    inner_cmd = [{'command': command, 'prompt': None, 'answer': None}]
    cmd.extend(inner_cmd)
    retVal = retVal + str(cnos.run_cnos_commands(module, cmd))
    command = "exit \n"
    # debugOutput(command)
    return retVal
# EOM


def main():
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=False),
            username=dict(required=False),
            password=dict(required=False, no_log=True),
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

    asNum = module.params['asNum']
    outputfile = module.params['outputfile']
    deviceType = module.params['deviceType']
    output = ''
    command = 'router bgp '
    value = cnos.checkSanityofVariable(deviceType, "bgp_as_number", asNum)
    if(value == "ok"):
        # BGP command happens here. It creates if not present
        command = command + asNum
        cmd = [{'command': command, 'prompt': None, 'answer': None}]
        output = output + bgpConfig(module, cmd, '(config)#', None)
    else:
        output = "Error-176"
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
