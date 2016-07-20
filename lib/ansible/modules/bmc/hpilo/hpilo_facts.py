#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
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

DOCUMENTATION = '''
---
author: Dag Wieers
module: hpilo_facts
requirements: [ python hpilo ]
short_description: Gather facts through an HP iLO interface
description:
    - This module gathers facts for a specific system using its HP iLO interface.
      These facts include hardware and network related information useful
      for provisioning (e.g. macaddress, uuid).
    - This module requires the hpilo python module.
version_added: "2.2"
options:
    host:
        description:
            - The HP iLO hostname/address that is linked to the physical system.
        required: true
    login:
        description:
            - The login name to authenticate to the HP iLO interface.
        default: Administrator
    password:
        description:
            - The password to authenticate to the HP iLO interface.
        default: admin
notes:
    - This module ought to be run from a system that can access the HP iLO
      interface directly, either by using local_action or
      using delegate_to.
'''

EXAMPLES = '''
# Task to gather facts from a HP iLO interface only if the system is an HP server
- hpilo_facts:
    host: YOUR_ILO_ADDRESS
    login: YOUR_ILO_LOGIN
    password: YOUR_ILO_PASSWORD
  when: cmdb_hwmodel.startswith('HP ')
  delegate_to: localhost

- fail:
    msg: 'CMDB serial ({{ cmdb_serialno }}) does not match hardware serial ({{ hw_system_serial }}) !'
    when: cmdb_serialno != hw_system_serial
'''

RETURN = '''

- hw_bios_date: "05/05/2011"
  hw_bios_version: "P68"
  hw_eth0:
- macaddress: "00:11:22:33:44:55"
  macaddress_dash: "00-11-22-33-44-55"
  hw_eth1:
- macaddress: "00:11:22:33:44:57"
  macaddress_dash: "00-11-22-33-44-57"
  hw_eth2:
- macaddress: "00:11:22:33:44:5A"
  macaddress_dash: "00-11-22-33-44-5A"
  hw_eth3:
- macaddress: "00:11:22:33:44:5C"
  macaddress_dash: "00-11-22-33-44-5C"
  hw_eth_ilo:
- macaddress: "00:11:22:33:44:BA"
  macaddress_dash: "00-11-22-33-44-BA"
  hw_product_name: "ProLiant DL360 G7"
  hw_product_uuid: "ef50bac8-2845-40ff-81d9-675315501dac"
  hw_system_serial: "ABC12345D6"
  hw_uuid: "123456ABC78901D2"
'''

import re
import warnings
try:
    import hpilo
    HAS_HPILO = True
except ImportError:
    HAS_HPILO = False

# Surpress warnings from hpilo
warnings.simplefilter('ignore')

def parse_flat_interface(entry, non_numeric='hw_eth_ilo'):
    try:
        factname = 'hw_eth' + str(int(entry['Port']) - 1)
    except:
        factname = non_numeric

        facts = {
            'macaddress': entry['MAC'].replace('-', ':'),
            'macaddress_dash': entry['MAC']
        }
        return (factname, facts)

def main():
    argument_spec = dict(
        host     = dict(default=None, required=True, type='str', aliases=['ilo_host']),
        login    = dict(default='Administrator', type='str', aliases=['user']),
        password = dict(default='admin', type='str', aliases=['pass'])
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
    )

    host = module.params.get('host')
    login = module.params.get('login')
    password = module.params.get('password')

    if not HAS_HPILO:
        module.fail_json(msg="hpilo python module is required.")

    ilo = hpilo.Ilo(host, login=login, password=password)

    # TODO: Count number of CPUs, DIMMs and total memory
    data = ilo.get_host_data()

    facts = {
        'module_hw': True,
    }

    for entry in data:
        if not entry.has_key('type'):
            continue
        if entry['type'] == 0: # BIOS Information
            facts['hw_bios_version'] = entry['Family']
            facts['hw_bios_date'] = entry['Date']
        elif entry['type'] == 1: # System Information
            facts['hw_uuid'] = entry['UUID']
            facts['hw_system_serial'] = entry['Serial Number'].rstrip()
            facts['hw_product_name'] = entry['Product Name']
            facts['hw_product_uuid'] = entry['cUUID']
        elif entry['type'] == 209: # Embedded NIC MAC Assignment
            if entry.has_key('fields'):
                for (name, value) in [ (e['name'], e['value']) for e in entry['fields'] ]:
                    if name.startswith('Port'):
                        try:
                            factname = 'hw_eth' + str(int(value) - 1)
                        except:
                            factname = 'hw_eth_ilo'
                    elif name.startswith('MAC'):
                        facts[factname] = {
                            'macaddress': value.replace('-', ':'),
                            'macaddress_dash': value
                        }
                    else:
                        (factname, entry_facts) = parse_flat_interface(entry, 'hw_eth_ilo')
                        facts[factname] = entry_facts
        elif entry['type'] == 209:  # HPQ NIC iSCSI MAC Info
            for (name, value) in [(e['name'], e['value']) for e in entry['fields']]:
                if name.startswith('Port'):
                    try:
                        factname = 'hw_iscsi' + str(int(value) - 1)
                    except:
                        factname = 'hw_iscsi_ilo'
                elif name.startswith('MAC'):
                    facts[factname] = {
                    'macaddress': value.replace('-', ':'),
                    'macaddress_dash': value
                    }
                elif entry['type'] == 233:  # Embedded NIC MAC Assignment (Alternate data format)
                    (factname, entry_facts) = parse_flat_interface(entry, 'hw_eth_ilo')
                    facts[factname] = entry_facts

    # collect health (RAM/CPU data)
    health = ilo.get_embedded_health()
    facts['hw_health'] = health
    memory_details_summary = health.get('memory', {}).get('memory_details_summary')

    # RAM as reported by iLO 2.10 on ProLiant BL460c Gen8
    if memory_details_summary:
        facts['hw_memory_details_summary'] = memory_details_summary
        facts['hw_memory_total'] = 0
        for cpu, details in memory_details_summary.iteritems():
            cpu_total_memory_size = details.get('total_memory_size')
            if cpu_total_memory_size:
                ram = re.search('(\d+)\s+(\w+)', cpu_total_memory_size)
                if ram:
                    if ram.group(2) == 'GB':
                        facts['hw_memory_total'] = int(facts['hw_memory_total']) + int(ram.group(1))

    facts['hw_memory_total'] = "{0} GB".format(facts['hw_memory_total'])

    module.exit_json(ansible_facts=facts)

# import module snippets
from ansible.module_utils.basic import *

if __name__ == "__main__":
    main()
