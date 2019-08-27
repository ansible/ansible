#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright: (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: udm_dns_zone
version_added: "2.2"
author:
- Tobias Rüetschi (@keachi)
short_description: Manage dns zones on a univention corporate server
description:
    - "This module allows to manage dns zones on a univention corporate server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the dns zone is present or not.
    type:
        required: true
        choices: [ forward_zone, reverse_zone ]
        description:
            - Define if the zone is a forward or reverse DNS zone.
    zone:
        required: true
        description:
            - DNS zone name, e.g. C(example.com).
    nameserver:
        required: false
        description:
            - List of appropriate name servers. Required if C(state=present).
    interfaces:
        required: false
        description:
            - List of interface IP addresses, on which the server should
              response this zone. Required if C(state=present).

    refresh:
        required: false
        default: 3600
        description:
            - Interval before the zone should be refreshed.
    retry:
        required: false
        default: 1800
        description:
            - Interval that should elapse before a failed refresh should be retried.
    expire:
        required: false
        default: 604800
        description:
            - Specifies the upper limit on the time interval that can elapse before the zone is no longer authoritative.
    ttl:
        required: false
        default: 600
        description:
            - Minimum TTL field that should be exported with any RR from this zone.

    contact:
        required: false
        default: ''
        description:
            - Contact person in the SOA record.
    mx:
        required: false
        default: []
        description:
            - List of MX servers. (Must declared as A or AAAA records).
'''


EXAMPLES = '''
# Create a DNS zone on a UCS
- udm_dns_zone:
    zone: example.com
    type: forward_zone
    nameserver:
      - ucs.example.com
    interfaces:
      - 192.0.2.1
'''


RETURN = '''# '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
)


def convert_time(time):
    """Convert a time in seconds into the biggest unit"""
    units = [
        (24 * 60 * 60, 'days'),
        (60 * 60, 'hours'),
        (60, 'minutes'),
        (1, 'seconds'),
    ]

    if time == 0:
        return ('0', 'seconds')
    for unit in units:
        if time >= unit[0]:
            return ('{0}'.format(time // unit[0]), unit[1])


def main():
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(required=True,
                      type='str'),
            zone=dict(required=True,
                      aliases=['name'],
                      type='str'),
            nameserver=dict(default=[],
                            type='list'),
            interfaces=dict(default=[],
                            type='list'),
            refresh=dict(default=3600,
                         type='int'),
            retry=dict(default=1800,
                       type='int'),
            expire=dict(default=604800,
                        type='int'),
            ttl=dict(default=600,
                     type='int'),
            contact=dict(default='',
                         type='str'),
            mx=dict(default=[],
                    type='list'),
            state=dict(default='present',
                       choices=['present', 'absent'],
                       type='str')
        ),
        supports_check_mode=True,
        required_if=([
            ('state', 'present', ['nameserver', 'interfaces'])
        ])
    )
    type = module.params['type']
    zone = module.params['zone']
    nameserver = module.params['nameserver']
    interfaces = module.params['interfaces']
    refresh = module.params['refresh']
    retry = module.params['retry']
    expire = module.params['expire']
    ttl = module.params['ttl']
    contact = module.params['contact']
    mx = module.params['mx']
    state = module.params['state']
    changed = False
    diff = None

    obj = list(ldap_search(
        '(&(objectClass=dNSZone)(zoneName={0}))'.format(zone),
        attr=['dNSZone']
    ))

    exists = bool(len(obj))
    container = 'cn=dns,{0}'.format(base_dn())
    dn = 'zoneName={0},{1}'.format(zone, container)
    if contact == '':
        contact = 'root@{0}.'.format(zone)

    if state == 'present':
        try:
            if not exists:
                obj = umc_module_for_add('dns/{0}'.format(type), container)
            else:
                obj = umc_module_for_edit('dns/{0}'.format(type), dn)
            obj['zone'] = zone
            obj['nameserver'] = nameserver
            obj['a'] = interfaces
            obj['refresh'] = convert_time(refresh)
            obj['retry'] = convert_time(retry)
            obj['expire'] = convert_time(expire)
            obj['ttl'] = convert_time(ttl)
            obj['contact'] = contact
            obj['mx'] = mx
            diff = obj.diff()
            if exists:
                for k in obj.keys():
                    if obj.hasChanged(k):
                        changed = True
            else:
                changed = True
            if not module.check_mode:
                if not exists:
                    obj.create()
                elif changed:
                    obj.modify()
        except Exception as e:
            module.fail_json(
                msg='Creating/editing dns zone {0} failed: {1}'.format(zone, e)
            )

    if state == 'absent' and exists:
        try:
            obj = umc_module_for_edit('dns/{0}'.format(type), dn)
            if not module.check_mode:
                obj.remove()
            changed = True
        except Exception as e:
            module.fail_json(
                msg='Removing dns zone {0} failed: {1}'.format(zone, e)
            )

    module.exit_json(
        changed=changed,
        diff=diff,
        zone=zone
    )


if __name__ == '__main__':
    main()
