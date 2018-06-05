#!/usr/bin/python
# Copyright (c) 2018 Red Hat, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: nios_host_record
version_added: "2.5"
author: "Peter Sprygada (@privateip)"
short_description: Configure Infoblox NIOS host records
description:
  - Adds and/or removes instances of host record objects from
    Infoblox NIOS servers.  This module manages NIOS C(record:host) objects
    using the Infoblox WAPI interface over REST.
  - Updates instances of host record object from Infoblox NIOS servers.
requirements:
  - infoblox_client
extends_documentation_fragment: nios
options:
  name:
    description:
      - Specifies the fully qualified hostname to add or remove from
        the system. User can also update the hostname as it is possible
        to pass a dict containing I(new_name), I(old_name). See examples.
    required: true
  view:
    description:
      - Sets the DNS view to associate this host record with.  The DNS
        view must already be configured on the system
    required: true
    default: default
    aliases:
      - dns_view
  ipv4addrs:
    description:
      - Configures the IPv4 addresses for this host record.  This argument
        accepts a list of values (see suboptions)
    aliases:
      - ipv4
    suboptions:
      ipv4addr:
        description:
          - Configures the IPv4 address for the host record
        required: true
        aliases:
          - address
      mac:
        description:
          - Configures the hardware MAC address for the host record
  ipv6addrs:
    description:
      - Configures the IPv6 addresses for the host record.  This argument
        accepts a list of values (see options)
    aliases:
      - ipv6
    suboptions:
      ipv6addr:
        description:
          - Configures the IPv6 address for the host record
        required: true
        aliases:
          - address
  aliases:
    version_added: "2.6"
    description:
      - Configures an optional list of additional aliases to add to the host
        record. These are equivalent to CNAMEs but held within a host
        record. Must be in list format.
  ttl:
    description:
      - Configures the TTL to be associated with this host record
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
- name: configure an ipv4 host record
  nios_host_record:
    name: host.ansible.com
    ipv4:
      - address: 192.168.10.1
    aliases:
      - cname.ansible.com
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: add a comment to an existing host record
  nios_host_record:
    name: host.ansible.com
    ipv4:
      - address: 192.168.10.1
    comment: this is a test comment
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: remove a host record from the system
  nios_host_record:
    name: host.ansible.com
    state: absent
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: update an ipv4 host record
  nios_host_record:
    name: {new_name: host-new.ansible.com, old_name: host.ansible.com}
    ipv4:
      - address: 192.168.10.1
    state: present
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
from ansible.module_utils.net_tools.nios.api import NIOS_HOST_RECORD


def ipaddr(module, key, filtered_keys=None):
    ''' Transforms the input value into a struct supported by WAPI
    This function will transform the input from the playbook into a struct
    that is valid for WAPI in the form of:
        {
            ipv4addr: <value>,
            mac: <value>
        }
    This function does not validate the values are properly formatted or in
    the acceptable range, that is left to WAPI.
    '''
    filtered_keys = filtered_keys or list()
    objects = list()
    for item in module.params[key]:
        objects.append(dict([(k, v) for k, v in iteritems(item) if v is not None and k not in filtered_keys]))
    return objects


def ipv4addrs(module):
    return ipaddr(module, 'ipv4addrs', filtered_keys=['address'])


def ipv6addrs(module):
    return ipaddr(module, 'ipv6addrs', filtered_keys=['address'])


def main():
    ''' Main entry point for module execution
    '''
    ipv4addr_spec = dict(
        ipv4addr=dict(required=True, aliases=['address'], ib_req=True),
        mac=dict()
    )

    ipv6addr_spec = dict(
        ipv6addr=dict(required=True, aliases=['address'], ib_req=True)
    )

    ib_spec = dict(
        name=dict(required=True, ib_req=True),
        view=dict(default='default', aliases=['dns_view'], ib_req=True),

        ipv4addrs=dict(type='list', aliases=['ipv4'], elements='dict', options=ipv4addr_spec, transform=ipv4addrs),
        ipv6addrs=dict(type='list', aliases=['ipv6'], elements='dict', options=ipv6addr_spec, transform=ipv6addrs),
        aliases=dict(type='list'),

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
    result = wapi.run(NIOS_HOST_RECORD, ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
