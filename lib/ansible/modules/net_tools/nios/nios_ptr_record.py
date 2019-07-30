#!/usr/bin/python
# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
---
module: nios_ptr_record
version_added: "2.7"
author: "Trebuchet Clement (@clementtrebuchet)"
short_description: Configure Infoblox NIOS PTR records
description:
  - Adds and/or removes instances of PTR record objects from
    Infoblox NIOS servers.  This module manages NIOS C(record:ptr) objects
    using the Infoblox WAPI interface over REST.
requirements:
  - infoblox_client
extends_documentation_fragment: nios
options:
  name:
    description:
      - The name of the DNS PTR record in FQDN format to add or remove from
        the system.
        The field is required only for an PTR object in Forward Mapping Zone.
    required: false
  view:
    description:
      - Sets the DNS view to associate this a record with. The DNS
        view must already be configured on the system
    required: false
    aliases:
      - dns_view
  ipv4addr:
    description:
      - The IPv4 Address of the record. Mutually exclusive with the ipv6addr.
    required: true
    aliases:
      - ipv4
  ipv6addr:
    description:
      - The IPv6 Address of the record. Mutually exclusive with the ipv4addr.
    required: true
    aliases:
      - ipv6
  ptrdname:
    description:
      - The domain name of the DNS PTR record in FQDN format.
    required: true
  ttl:
    description:
      - Time To Live (TTL) value for the record.
        A 32-bit unsigned integer that represents the duration, in seconds, that the record is valid (cached).
        Zero indicates that the record should not be cached.
  extattrs:
    description:
      - Allows for the configuration of Extensible Attributes on the
        instance of the object.  This argument accepts a set of key / value
        pairs for configuration.
  comment:
    description:
      - Configures a text string comment to be associated with the instance
        of this object.  The provided text string will be configured on the
        object instance. Maximum 256 characters.
  state:
    description:
      - Configures the intended state of the instance of the object on
        the NIOS server.  When this value is set to C(present), the object
        is configured on the device and when this value is set to C(absent)
        the value is removed (if necessary) from the device.
    default: present
    choices:
      - present
      - absent
'''

EXAMPLES = '''
- name: Create a PTR Record
  nios_ptr_record:
    ipv4: 192.168.10.1
    ptrdname: host.ansible.com
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local

- name: Delete a PTR Record
  nios_ptr_record:
    ipv4: 192.168.10.1
    ptrdname: host.ansible.com
    state: absent
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.net_tools.nios.api import WapiModule
from ansible.module_utils.net_tools.nios.api import NIOS_PTR_RECORD


def main():
    # Module entry point
    ib_spec = dict(
        name=dict(required=False),
        view=dict(aliases=['dns_view']),
        ipv4addr=dict(aliases=['ipv4'], ib_req=True),
        ipv6addr=dict(aliases=['ipv6'], ib_req=True),
        ptrdname=dict(ib_req=True),

        ttl=dict(type='int'),

        extattrs=dict(type='dict'),
        comment=dict(),
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(WapiModule.provider_spec)

    mutually_exclusive = [('ipv4addr', 'ipv6addr')]
    required_one_of = [
        ['ipv4addr', 'ipv6addr']
    ]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True,
                           required_one_of=required_one_of)

    if module.params['ipv4addr']:
        del ib_spec['ipv6addr']
    elif module.params['ipv6addr']:
        del ib_spec['ipv4addr']

    wapi = WapiModule(module)
    result = wapi.run(NIOS_PTR_RECORD, ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
