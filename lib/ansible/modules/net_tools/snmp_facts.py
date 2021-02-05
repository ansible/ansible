#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of Networklore's snmp library for Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: snmp_facts
version_added: "1.9"
author:
- Patrick Ogenstad (@ogenstad)
short_description: Retrieve facts for a device using SNMP
description:
    - Retrieve facts for a device using SNMP, the facts will be
      inserted to the ansible_facts key.
requirements:
    - pysnmp
options:
    host:
        description:
            - Set to target snmp server (normally C({{ inventory_hostname }})).
        type: str
        required: true
    version:
        description:
            - SNMP Version to use, v2/v2c or v3.
        type: str
        required: true
        choices: [ v2, v2c, v3 ]
    community:
        description:
            - The SNMP community string, required if version is v2/v2c.
        type: str
    level:
        description:
            - Authentication level.
            - Required if version is v3.
        type: str
        choices: [ authNoPriv, authPriv ]
    username:
        description:
            - Username for SNMPv3.
            - Required if version is v3.
        type: str
    integrity:
        description:
            - Hashing algorithm.
            - Required if version is v3.
        type: str
        choices: [ md5, sha ]
    authkey:
        description:
            - Authentication key.
            - Required if version is v3.
        type: str
    privacy:
        description:
            - Encryption algorithm.
            - Required if level is authPriv.
        type: str
        choices: [ aes, des ]
    privkey:
        description:
            - Encryption key.
            - Required if version is authPriv.
        type: str
'''

EXAMPLES = r'''
- name: Gather facts with SNMP version 2
  snmp_facts:
    host: '{{ inventory_hostname }}'
    version: v2c
    community: public
  delegate_to: local

- name: Gather facts using SNMP version 3
  snmp_facts:
    host: '{{ inventory_hostname }}'
    version: v3
    level: authPriv
    integrity: sha
    privacy: aes
    username: snmp-user
    authkey: abc12345
    privkey: def6789
  delegate_to: localhost
'''

RETURN = r'''
ansible_sysdescr:
  description: A textual description of the entity.
  returned: success
  type: str
  sample: Linux ubuntu-user 4.4.0-93-generic #116-Ubuntu SMP Fri Aug 11 21:17:51 UTC 2017 x86_64
ansible_sysobjectid:
  description: The vendor's authoritative identification of the network management subsystem contained in the entity.
  returned: success
  type: str
  sample: 1.3.6.1.4.1.8072.3.2.10
ansible_sysuptime:
  description: The time (in hundredths of a second) since the network management portion of the system was last re-initialized.
  returned: success
  type: int
  sample: 42388
ansible_syscontact:
  description: The textual identification of the contact person for this managed node, together with information on how to contact this person.
  returned: success
  type: str
  sample: Me <me@example.org>
ansible_sysname:
  description: An administratively-assigned name for this managed node.
  returned: success
  type: str
  sample: ubuntu-user
ansible_syslocation:
  description: The physical location of this node (e.g., `telephone closet, 3rd floor').
  returned: success
  type: str
  sample: Sitting on the Dock of the Bay
ansible_all_ipv4_addresses:
  description: List of all IPv4 addresses.
  returned: success
  type: list
  sample: ["127.0.0.1", "172.17.0.1"]
ansible_interfaces:
  description: Dictionary of each network interface and its metadata.
  returned: success
  type: dict
  sample: {
    "1": {
        "adminstatus": "up",
        "description": "",
        "ifindex": "1",
        "ipv4": [
            {
                "address": "127.0.0.1",
                "netmask": "255.0.0.0"
            }
        ],
        "mac": "",
        "mtu": "65536",
        "name": "lo",
        "operstatus": "up",
        "speed": "65536"
    },
    "2": {
        "adminstatus": "up",
        "description": "",
        "ifindex": "2",
        "ipv4": [
            {
                "address": "192.168.213.128",
                "netmask": "255.255.255.0"
            }
        ],
        "mac": "000a305a52a1",
        "mtu": "1500",
        "name": "Intel Corporation 82545EM Gigabit Ethernet Controller (Copper)",
        "operstatus": "up",
        "speed": "1500"
    }
  }
'''

import binascii
import traceback
from collections import defaultdict

PYSNMP_IMP_ERR = None
try:
    from pysnmp.entity.rfc3413.oneliner import cmdgen
    has_pysnmp = True
except Exception:
    PYSNMP_IMP_ERR = traceback.format_exc()
    has_pysnmp = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_text


class DefineOid(object):

    def __init__(self, dotprefix=False):
        if dotprefix:
            dp = "."
        else:
            dp = ""

        # From SNMPv2-MIB
        self.sysDescr = dp + "1.3.6.1.2.1.1.1.0"
        self.sysObjectId = dp + "1.3.6.1.2.1.1.2.0"
        self.sysUpTime = dp + "1.3.6.1.2.1.1.3.0"
        self.sysContact = dp + "1.3.6.1.2.1.1.4.0"
        self.sysName = dp + "1.3.6.1.2.1.1.5.0"
        self.sysLocation = dp + "1.3.6.1.2.1.1.6.0"

        # From IF-MIB
        self.ifIndex = dp + "1.3.6.1.2.1.2.2.1.1"
        self.ifDescr = dp + "1.3.6.1.2.1.2.2.1.2"
        self.ifMtu = dp + "1.3.6.1.2.1.2.2.1.4"
        self.ifSpeed = dp + "1.3.6.1.2.1.2.2.1.5"
        self.ifPhysAddress = dp + "1.3.6.1.2.1.2.2.1.6"
        self.ifAdminStatus = dp + "1.3.6.1.2.1.2.2.1.7"
        self.ifOperStatus = dp + "1.3.6.1.2.1.2.2.1.8"
        self.ifAlias = dp + "1.3.6.1.2.1.31.1.1.1.18"

        # From IP-MIB
        self.ipAdEntAddr = dp + "1.3.6.1.2.1.4.20.1.1"
        self.ipAdEntIfIndex = dp + "1.3.6.1.2.1.4.20.1.2"
        self.ipAdEntNetMask = dp + "1.3.6.1.2.1.4.20.1.3"


def decode_hex(hexstring):

    if len(hexstring) < 3:
        return hexstring
    if hexstring[:2] == "0x":
        return to_text(binascii.unhexlify(hexstring[2:]))
    else:
        return hexstring


def decode_mac(hexstring):

    if len(hexstring) != 14:
        return hexstring
    if hexstring[:2] == "0x":
        return hexstring[2:]
    else:
        return hexstring


def lookup_adminstatus(int_adminstatus):
    adminstatus_options = {
        1: 'up',
        2: 'down',
        3: 'testing'
    }
    if int_adminstatus in adminstatus_options:
        return adminstatus_options[int_adminstatus]
    else:
        return ""


def lookup_operstatus(int_operstatus):
    operstatus_options = {
        1: 'up',
        2: 'down',
        3: 'testing',
        4: 'unknown',
        5: 'dormant',
        6: 'notPresent',
        7: 'lowerLayerDown'
    }
    if int_operstatus in operstatus_options:
        return operstatus_options[int_operstatus]
    else:
        return ""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            version=dict(type='str', required=True, choices=['v2', 'v2c', 'v3']),
            community=dict(type='str'),
            username=dict(type='str'),
            level=dict(type='str', choices=['authNoPriv', 'authPriv']),
            integrity=dict(type='str', choices=['md5', 'sha']),
            privacy=dict(type='str', choices=['aes', 'des']),
            authkey=dict(type='str', no_log=True),
            privkey=dict(type='str', no_log=True),
        ),
        required_together=(
            ['username', 'level', 'integrity', 'authkey'],
            ['privacy', 'privkey'],
        ),
        supports_check_mode=False,
    )

    m_args = module.params

    if not has_pysnmp:
        module.fail_json(msg=missing_required_lib('pysnmp'), exception=PYSNMP_IMP_ERR)

    cmdGen = cmdgen.CommandGenerator()

    # Verify that we receive a community when using snmp v2
    if m_args['version'] == "v2" or m_args['version'] == "v2c":
        if m_args['community'] is None:
            module.fail_json(msg='Community not set when using snmp version 2')

    if m_args['version'] == "v3":
        if m_args['username'] is None:
            module.fail_json(msg='Username not set when using snmp version 3')

        if m_args['level'] == "authPriv" and m_args['privacy'] is None:
            module.fail_json(msg='Privacy algorithm not set when using authPriv')

        if m_args['integrity'] == "sha":
            integrity_proto = cmdgen.usmHMACSHAAuthProtocol
        elif m_args['integrity'] == "md5":
            integrity_proto = cmdgen.usmHMACMD5AuthProtocol

        if m_args['privacy'] == "aes":
            privacy_proto = cmdgen.usmAesCfb128Protocol
        elif m_args['privacy'] == "des":
            privacy_proto = cmdgen.usmDESPrivProtocol

    # Use SNMP Version 2
    if m_args['version'] == "v2" or m_args['version'] == "v2c":
        snmp_auth = cmdgen.CommunityData(m_args['community'])

    # Use SNMP Version 3 with authNoPriv
    elif m_args['level'] == "authNoPriv":
        snmp_auth = cmdgen.UsmUserData(m_args['username'], authKey=m_args['authkey'], authProtocol=integrity_proto)

    # Use SNMP Version 3 with authPriv
    else:
        snmp_auth = cmdgen.UsmUserData(m_args['username'], authKey=m_args['authkey'], privKey=m_args['privkey'], authProtocol=integrity_proto,
                                       privProtocol=privacy_proto)

    # Use p to prefix OIDs with a dot for polling
    p = DefineOid(dotprefix=True)
    # Use v without a prefix to use with return values
    v = DefineOid(dotprefix=False)

    def Tree():
        return defaultdict(Tree)

    results = Tree()

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(
        snmp_auth,
        cmdgen.UdpTransportTarget((m_args['host'], 161)),
        cmdgen.MibVariable(p.sysDescr,),
        cmdgen.MibVariable(p.sysObjectId,),
        cmdgen.MibVariable(p.sysUpTime,),
        cmdgen.MibVariable(p.sysContact,),
        cmdgen.MibVariable(p.sysName,),
        cmdgen.MibVariable(p.sysLocation,),
        lookupMib=False
    )

    if errorIndication:
        module.fail_json(msg=str(errorIndication))

    for oid, val in varBinds:
        current_oid = oid.prettyPrint()
        current_val = val.prettyPrint()
        if current_oid == v.sysDescr:
            results['ansible_sysdescr'] = decode_hex(current_val)
        elif current_oid == v.sysObjectId:
            results['ansible_sysobjectid'] = current_val
        elif current_oid == v.sysUpTime:
            results['ansible_sysuptime'] = current_val
        elif current_oid == v.sysContact:
            results['ansible_syscontact'] = current_val
        elif current_oid == v.sysName:
            results['ansible_sysname'] = current_val
        elif current_oid == v.sysLocation:
            results['ansible_syslocation'] = current_val

    errorIndication, errorStatus, errorIndex, varTable = cmdGen.nextCmd(
        snmp_auth,
        cmdgen.UdpTransportTarget((m_args['host'], 161)),
        cmdgen.MibVariable(p.ifIndex,),
        cmdgen.MibVariable(p.ifDescr,),
        cmdgen.MibVariable(p.ifMtu,),
        cmdgen.MibVariable(p.ifSpeed,),
        cmdgen.MibVariable(p.ifPhysAddress,),
        cmdgen.MibVariable(p.ifAdminStatus,),
        cmdgen.MibVariable(p.ifOperStatus,),
        cmdgen.MibVariable(p.ipAdEntAddr,),
        cmdgen.MibVariable(p.ipAdEntIfIndex,),
        cmdgen.MibVariable(p.ipAdEntNetMask,),

        cmdgen.MibVariable(p.ifAlias,),
        lookupMib=False
    )

    if errorIndication:
        module.fail_json(msg=str(errorIndication))

    interface_indexes = []

    all_ipv4_addresses = []
    ipv4_networks = Tree()

    for varBinds in varTable:
        for oid, val in varBinds:
            current_oid = oid.prettyPrint()
            current_val = val.prettyPrint()
            if v.ifIndex in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['ifindex'] = current_val
                interface_indexes.append(ifIndex)
            if v.ifDescr in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['name'] = current_val
            if v.ifMtu in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['mtu'] = current_val
            if v.ifSpeed in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['speed'] = current_val
            if v.ifPhysAddress in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['mac'] = decode_mac(current_val)
            if v.ifAdminStatus in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['adminstatus'] = lookup_adminstatus(int(current_val))
            if v.ifOperStatus in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['operstatus'] = lookup_operstatus(int(current_val))
            if v.ipAdEntAddr in current_oid:
                curIPList = current_oid.rsplit('.', 4)[-4:]
                curIP = ".".join(curIPList)
                ipv4_networks[curIP]['address'] = current_val
                all_ipv4_addresses.append(current_val)
            if v.ipAdEntIfIndex in current_oid:
                curIPList = current_oid.rsplit('.', 4)[-4:]
                curIP = ".".join(curIPList)
                ipv4_networks[curIP]['interface'] = current_val
            if v.ipAdEntNetMask in current_oid:
                curIPList = current_oid.rsplit('.', 4)[-4:]
                curIP = ".".join(curIPList)
                ipv4_networks[curIP]['netmask'] = current_val

            if v.ifAlias in current_oid:
                ifIndex = int(current_oid.rsplit('.', 1)[-1])
                results['ansible_interfaces'][ifIndex]['description'] = current_val

    interface_to_ipv4 = {}
    for ipv4_network in ipv4_networks:
        current_interface = ipv4_networks[ipv4_network]['interface']
        current_network = {
            'address': ipv4_networks[ipv4_network]['address'],
            'netmask': ipv4_networks[ipv4_network]['netmask']
        }
        if current_interface not in interface_to_ipv4:
            interface_to_ipv4[current_interface] = []
            interface_to_ipv4[current_interface].append(current_network)
        else:
            interface_to_ipv4[current_interface].append(current_network)

    for interface in interface_to_ipv4:
        results['ansible_interfaces'][int(interface)]['ipv4'] = interface_to_ipv4[interface]

    results['ansible_all_ipv4_addresses'] = all_ipv4_addresses

    module.exit_json(ansible_facts=results)


if __name__ == '__main__':
    main()
