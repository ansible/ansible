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
module: nios_cname_record
version_added: "2.7"
author: "Blair Rampling (@brampling)"
short_description: Configure Infoblox NIOS CNAME records
description:
  - Adds and/or removes instances of CNAME record objects from
    Infoblox NIOS servers.  This module manages NIOS C(record:cname) objects
    using the Infoblox WAPI interface over REST.
requirements:
  - infoblox-client
extends_documentation_fragment: nios
options:
  name:
    description:
      - Specifies the fully qualified hostname to add or remove from
        the system
    required: true
  view:
    description:
      - Sets the DNS view to associate this CNAME record with.  The DNS
        view must already be configured on the system
    required: true
    default: default
    aliases:
      - dns_view
  canonical:
    description:
      - Configures the canonical name for this CNAME record.
    required: true
    aliases:
      - cname
  ttl:
    description:
      - Configures the TTL to be associated with this CNAME record
  extattrs:
    description:
      - Allows for the configuration of Extensible Attributes on the
        instance of the object.  This argument accepts a set of key / value
        pairs for configuration.
  comment:
    description:
      - Configures a text string comment to be associated with the instance
        of this object.  The provided text string will be configured on the
        object instance.
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
- name: configure a CNAME record
  nios_cname_record:
    name: cname.ansible.com
    canonical: realhost.ansible.com
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local

- name: add a comment to an existing CNAME record
  nios_cname_record:
    name: cname.ansible.com
    canonical: realhost.ansible.com
    comment: this is a test comment
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local

- name: remove a CNAME record from the system
  nios_cname_record:
    name: cname.ansible.com
    canonical: realhost.ansible.com
    state: absent
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import iteritems
from ansible.module_utils.net_tools.nios.api import WapiModule
from ansible.module_utils.net_tools.nios.api import NIOS_CNAME_RECORD


def main():
    ''' Main entry point for module execution
    '''

    ib_spec = dict(
        name=dict(required=True, ib_req=True),
        view=dict(default='default', aliases=['dns_view'], ib_req=True),

        canonical=dict(aliases=['cname'], ib_req=True),

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

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    wapi = WapiModule(module)
    result = wapi.run(NIOS_CNAME_RECORD, ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
