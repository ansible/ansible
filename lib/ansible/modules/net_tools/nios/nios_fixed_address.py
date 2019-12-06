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
module: nios_fixed_address
version_added: "2.8"
author: "Sumit Jaiswal (@sjaiswal)"
short_description: Configure Infoblox NIOS DHCP Fixed Address
description:
  - A fixed address is a specific IP address that a DHCP server
    always assigns when a lease request comes from a particular
    MAC address of the client.
  - Supports both IPV4 and IPV6 internet protocols
requirements:
  - infoblox-client
extends_documentation_fragment: nios
options:
  name:
    description:
      - Specifies the hostname with which fixed DHCP ip-address is stored
        for respective mac.
    required: false
  ipaddr:
    description:
      - IPV4/V6 address of the fixed address.
    required: true
  mac:
    description:
      - The MAC address of the interface.
    required: true
  network:
    description:
      - Specifies the network range in which ipaddr exists.
    required: true
    aliases:
      - network
  network_view:
    description:
      - Configures the name of the network view to associate with this
        configured instance.
    required: false
    default: default
  options:
    description:
      - Configures the set of DHCP options to be included as part of
        the configured network instance.  This argument accepts a list
        of values (see suboptions).  When configuring suboptions at
        least one of C(name) or C(num) must be specified.
    suboptions:
      name:
        description:
          - The name of the DHCP option to configure
      num:
        description:
          - The number of the DHCP option to configure
      value:
        description:
          - The value of the DHCP option specified by C(name)
        required: true
      use_option:
        description:
          - Only applies to a subset of options (see NIOS API documentation)
        type: bool
        default: 'yes'
      vendor_class:
        description:
          - The name of the space this DHCP option is associated to
        default: DHCP
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
- name: configure ipv4 dhcp fixed address
  nios_fixed_address:
    name: ipv4_fixed
    ipaddr: 192.168.10.1
    mac: 08:6d:41:e8:fd:e8
    network: 192.168.10.0/24
    network_view: default
    comment: this is a test comment
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: configure a ipv6 dhcp fixed address
  nios_fixed_address:
    name: ipv6_fixed
    ipaddr: fe80::1/10
    mac: 08:6d:41:e8:fd:e8
    network: fe80::/64
    network_view: default
    comment: this is a test comment
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: set dhcp options for a ipv4 fixed address
  nios_fixed_address:
    name: ipv4_fixed
    ipaddr: 192.168.10.1
    mac: 08:6d:41:e8:fd:e8
    network: 192.168.10.0/24
    network_view: default
    comment: this is a test comment
    options:
      - name: domain-name
        value: ansible.com
    state: present
    provider:
      host: "{{ inventory_hostname_short }}"
      username: admin
      password: admin
  connection: local
- name: remove a ipv4 dhcp fixed address
  nios_fixed_address:
    name: ipv4_fixed
    ipaddr: 192.168.10.1
    mac: 08:6d:41:e8:fd:e8
    network: 192.168.10.0/24
    network_view: default
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
from ansible.module_utils.network.common.utils import validate_ip_address, validate_ip_v6_address
from ansible.module_utils.net_tools.nios.api import NIOS_IPV4_FIXED_ADDRESS, NIOS_IPV6_FIXED_ADDRESS


def options(module):
    ''' Transforms the module argument into a valid WAPI struct
    This function will transform the options argument into a structure that
    is a valid WAPI structure in the format of:
        {
            name: <value>,
            num: <value>,
            value: <value>,
            use_option: <value>,
            vendor_class: <value>
        }
    It will remove any options that are set to None since WAPI will error on
    that condition.  It will also verify that either `name` or `num` is
    set in the structure but does not validate the values are equal.
    The remainder of the value validation is performed by WAPI
    '''
    options = list()
    for item in module.params['options']:
        opt = dict([(k, v) for k, v in iteritems(item) if v is not None])
        if 'name' not in opt and 'num' not in opt:
            module.fail_json(msg='one of `name` or `num` is required for option value')
        options.append(opt)
    return options


def validate_ip_addr_type(ip, arg_spec, module):
    '''This function will check if the argument ip is type v4/v6 and return appropriate infoblox network type
    '''
    check_ip = ip.split('/')

    if validate_ip_address(check_ip[0]) and 'ipaddr' in arg_spec:
        arg_spec['ipv4addr'] = arg_spec.pop('ipaddr')
        module.params['ipv4addr'] = module.params.pop('ipaddr')
        return NIOS_IPV4_FIXED_ADDRESS, arg_spec, module
    elif validate_ip_v6_address(check_ip[0]) and 'ipaddr' in arg_spec:
        arg_spec['ipv6addr'] = arg_spec.pop('ipaddr')
        module.params['ipv6addr'] = module.params.pop('ipaddr')
        return NIOS_IPV6_FIXED_ADDRESS, arg_spec, module


def main():
    ''' Main entry point for module execution
    '''
    option_spec = dict(
        # one of name or num is required; enforced by the function options()
        name=dict(),
        num=dict(type='int'),

        value=dict(required=True),

        use_option=dict(type='bool', default=True),
        vendor_class=dict(default='DHCP')
    )

    ib_spec = dict(
        name=dict(required=True),
        ipaddr=dict(required=True, aliases=['ipaddr'], ib_req=True),
        mac=dict(required=True, aliases=['mac'], ib_req=True),
        network=dict(required=True, aliases=['network'], ib_req=True),
        network_view=dict(default='default', aliases=['network_view']),

        options=dict(type='list', elements='dict', options=option_spec, transform=options),

        extattrs=dict(type='dict'),
        comment=dict()
    )

    argument_spec = dict(
        provider=dict(required=True),
        state=dict(default='present', choices=['present', 'absent'])
    )

    argument_spec.update(ib_spec)
    argument_spec.update(WapiModule.provider_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    # to get the argument ipaddr
    obj_filter = dict([(k, module.params[k]) for k, v in iteritems(ib_spec) if v.get('ib_req')])
    # to modify argument based on ipaddr type i.e. IPV4/IPV6
    fixed_address_ip_type, ib_spec, module = validate_ip_addr_type(obj_filter['ipaddr'], ib_spec, module)

    wapi = WapiModule(module)

    result = wapi.run(fixed_address_ip_type, ib_spec)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
