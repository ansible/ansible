#!/usr/bin/python
# -*- coding: UTF-8 -*-

# Copyright (c) 2016, Adfinis SyGroup AG
# Tobias Rueetschi <tobias.ruetschi@adfinis-sygroup.ch>
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


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.univention_umc import (
    umc_module_for_add,
    umc_module_for_edit,
    ldap_search,
    base_dn,
    config,
    uldap,
)
from univention.admin.handlers.dns import (
    forward_zone,
    reverse_zone,
)


DOCUMENTATION = '''
---
module: udm_dns_record
version_added: "2.2"
author: "Tobias Rueetschi (@2-B)"
short_description: Manage dns entries on a univention corporate server
description:
    - "This module allows to manage dns records on a univention corporate server (UCS).
       It uses the python API of the UCS to create a new object or edit it."
requirements:
    - Python >= 2.6
options:
    state:
        required: false
        default: "present"
        choices: [ present, absent ]
        description:
            - Whether the dns record is present or not.
    name:
        required: true
        description:
            - "Name of the record, this is also the DNS record. E.g. www for
               www.example.com."
    zone:
        required: true
        description:
            - Corresponding DNS zone for this record, e.g. example.com.
    type:
        required: true
        choices: [ host_record, alias, ptr_record, srv_record, txt_record ]
        description:
            - "Define the record type. C(host_record) is a A or AAAA record,
               C(alias) is a CNAME, C(ptr_record) is a PTR record, C(srv_record)
               is a SRV record and C(txt_record) is a TXT record."
    data:
        required: false
        default: []
        description:
            - "Additional data for this record, e.g. ['a': '192.0.2.1'].
               Required if C(state=present)."
'''


EXAMPLES = '''
# Create a DNS record on a UCS
- udm_dns_zone: name=www
                zone=example.com
                type=host_record
                data=['a': '192.0.2.1']
'''


RETURN = '''# '''


def main():
    module = AnsibleModule(
        argument_spec = dict(
            type        = dict(required=True,
                               type='str'),
            zone        = dict(required=True,
                               type='str'),
            name        = dict(required=True,
                               type='str'),
            data        = dict(default=[],
                               type='dict'),
            state       = dict(default='present',
                               choices=['present', 'absent'],
                               type='str')
        ),
        supports_check_mode=True,
        required_if = ([
            ('state', 'present', ['data'])
        ])
    )
    type        = module.params['type']
    zone        = module.params['zone']
    name        = module.params['name']
    data        = module.params['data']
    state       = module.params['state']
    changed     = False

    obj = list(ldap_search(
        '(&(objectClass=dNSZone)(zoneName={})(relativeDomainName={}))'.format(zone, name),
        attr=['dNSZone']
    ))

    exists = bool(len(obj))
    container = 'zoneName={},cn=dns,{}'.format(zone, base_dn())
    dn = 'relativeDomainName={},{}'.format(name, container)

    if state == 'present':
        try:
            if not exists:
                so = forward_zone.lookup(
                    config(),
                    uldap(),
                    '(zone={})'.format(zone),
                    scope='domain',
                ) or reverse_zone.lookup(
                    config(),
                    uldap(),
                    '(zone={})'.format(zone),
                    scope='domain',
                )
                obj = umc_module_for_add('dns/{}'.format(type), container, superordinate=so[0])
            else:
                obj = umc_module_for_edit('dns/{}'.format(type), dn)
            obj['name'] = name
            for k, v in data.items():
                obj[k] = v
            diff = obj.diff()
            changed = obj.diff() != []
            if not module.check_mode:
                if not exists:
                    obj.create()
                else:
                    obj.modify()
        except BaseException as e:
            module.fail_json(
                msg='Creating/editing dns entry {} in {} failed: {}'.format(name, container, e)
            )

    if state == 'absent' and exists:
        try:
            obj = umc_module_for_edit('dns/{}'.format(type), dn)
            if not module.check_mode:
                obj.remove()
            changed = True
        except BaseException as e:
            module.fail_json(
                msg='Removing dns entry {} in {} failed: {}'.format(name, container, e)
            )

    module.exit_json(
        changed=changed,
        name=name,
        diff=diff,
        container=container
    )


if __name__ == '__main__':
    main()
