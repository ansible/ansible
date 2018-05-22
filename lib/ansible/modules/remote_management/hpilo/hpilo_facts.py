#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: hpilo_facts
version_added: "2.3"
author: Dag Wieers (@dagwieers)
short_description: Gather facts through an HP iLO interface
description:
- This module gathers facts for a specific system using its HP iLO interface.
  These facts include hardware and network related information useful
  for provisioning (e.g. macaddress, uuid).
- This module requires the hpilo python module.
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
  ssl_version:
    description:
      - Change the ssl_version used.
    default: TLSv1
    choices: [ "SSLv3", "SSLv23", "TLSv1", "TLSv1_1", "TLSv1_2" ]
    version_added: '2.4'
requirements:
- hpilo
notes:
- This module ought to be run from a system that can access the HP iLO
  interface directly, either by using C(local_action) or using C(delegate_to).
'''

EXAMPLES = r'''
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

RETURN = r'''
# Typical output of HP iLO_facts for a physical system
hw_bios_date:
    description: BIOS date
    returned: always
    type: string
    sample: 05/05/2011

hw_bios_version:
    description: BIOS version
    returned: always
    type: string
    sample: P68

hw_ethX:
    description: Interface information (for each interface)
    returned: always
    type: dictionary
    sample:
      - macaddress: 00:11:22:33:44:55
        macaddress_dash: 00-11-22-33-44-55

hw_eth_ilo:
    description: Interface information (for the iLO network interface)
    returned: always
    type: dictionary
    sample:
      - macaddress: 00:11:22:33:44:BA
      - macaddress_dash: 00-11-22-33-44-BA

hw_product_name:
    description: Product name
    returned: always
    type: string
    sample: ProLiant DL360 G7

hw_product_uuid:
    description: Product UUID
    returned: always
    type: string
    sample: ef50bac8-2845-40ff-81d9-675315501dac

hw_system_serial:
    description: System serial number
    returned: always
    type: string
    sample: ABC12345D6

hw_uuid:
    description: Hardware UUID
    returned: always
    type: string
    sample: 123456ABC78901D2
'''

import re
import warnings

try:
    import hpilo
    HAS_HPILO = True
except ImportError:
    HAS_HPILO = False

from ansible.module_utils.basic import AnsibleModule


# Suppress warnings from hpilo
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

    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            login=dict(type='str', default='Administrator'),
            password=dict(type='str', default='admin', no_log=True),
            ssl_version=dict(type='str', default='TLSv1', choices=['SSLv3', 'SSLv23', 'TLSv1', 'TLSv1_1', 'TLSv1_2']),
        ),
        supports_check_mode=True,
    )

    if not HAS_HPILO:
        module.fail_json(msg='The hpilo python module is required')

    host = module.params['host']
    login = module.params['login']
    password = module.params['password']
    ssl_version = getattr(hpilo.ssl, 'PROTOCOL_' + module.params.get('ssl_version').upper().replace('V', 'v'))

    ilo = hpilo.Ilo(host, login=login, password=password, ssl_version=ssl_version)

    facts = {
        'module_hw': True,
    }

    # TODO: Count number of CPUs, DIMMs and total memory
    data = ilo.get_host_data()
    for entry in data:
        if 'type' not in entry:
            continue
        elif entry['type'] == 0:  # BIOS Information
            facts['hw_bios_version'] = entry['Family']
            facts['hw_bios_date'] = entry['Date']
        elif entry['type'] == 1:  # System Information
            facts['hw_uuid'] = entry['UUID']
            facts['hw_system_serial'] = entry['Serial Number'].rstrip()
            facts['hw_product_name'] = entry['Product Name']
            facts['hw_product_uuid'] = entry['cUUID']
        elif entry['type'] == 209:  # Embedded NIC MAC Assignment
            if 'fields' in entry:
                for (name, value) in [(e['name'], e['value']) for e in entry['fields']]:
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

    # Collect health (RAM/CPU data)
    health = ilo.get_embedded_health()
    facts['hw_health'] = health

    memory_details_summary = health.get('memory', {}).get('memory_details_summary')
    # RAM as reported by iLO 2.10 on ProLiant BL460c Gen8
    if memory_details_summary:
        facts['hw_memory_details_summary'] = memory_details_summary
        facts['hw_memory_total'] = 0
        for cpu, details in memory_details_summary.items():
            cpu_total_memory_size = details.get('total_memory_size')
            if cpu_total_memory_size:
                ram = re.search(r'(\d+)\s+(\w+)', cpu_total_memory_size)
                if ram:
                    if ram.group(2) == 'GB':
                        facts['hw_memory_total'] = facts['hw_memory_total'] + int(ram.group(1))

        # reformat into a text friendly format
        facts['hw_memory_total'] = "{0} GB".format(facts['hw_memory_total'])

    module.exit_json(ansible_facts=facts)

if __name__ == '__main__':
    main()
