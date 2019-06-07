#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Kevin Breit (@kbreit) <kevin.breit@kevinbreit.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: meraki_management_interface
short_description: Configure Meraki management interfaces
version_added: "2.9"
description:
- Allows for configuration of management interfaces on Meraki devices.
notes:
- C(WAN2) parameter is only valid for MX appliances.
options:
    state:
        description:
        - Specifies whether configuration template information should be queried, modified, or deleted.
        choices: ['absent', 'query', 'present']
        default: query
        type: str
    org_name:
        description:
        - Name of organization containing the configuration template.
        type: str
    org_id:
        description:
        - ID of organization associated to a configuration template.
        type: str
    net_name:
        description:
        - Name of the network to bind or unbind configuration template to.
        type: str
    net_id:
        description:
        - ID of the network to bind or unbind configuration template to.
        type: str
    serial:
        description:
        - serial number of the device to configure.
        type: str
    wan1:
        description:
        - Management interface details for management interface.
        aliases: [mgmt1]
        type: dict
        suboptions:
            wan_enabled:
                description:
                - States whether the management interface is enabled.
                type: str
                choices: [disabled, enabled, not configured]
            using_static_ip:
                description:
                - Configures the interface to use static IP or DHCP.
                type: bool
            static_ip:
                description:
                - IP address assigned to Management interface.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_ip_gateway:
                description:
                - IP address for default gateway.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_subnet_mask:
                description:
                - Netmask for static IP address.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_dns:
                description:
                - DNS servers to use.
                - Allows for a maximum of 2 addresses.
                type: list
            vlan:
                description:
                - VLAN number to use for the management network.
                type: int
    wan2:
        description:
        - Management interface details for management interface.
        type: dict
        aliases: [mgmt2]
        suboptions:
            wan_enabled:
                description:
                - States whether the management interface is enabled.
                type: str
                choices: [disabled, enabled, not configured]
            using_static_ip:
                description:
                - Configures the interface to use static IP or DHCP.
                type: bool
            static_ip:
                description:
                - IP address assigned to Management interface.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_ip_gateway:
                description:
                - IP address for default gateway.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_subnet_mask:
                description:
                - Netmask for static IP address.
                - Valid only if C(using_static_ip) is C(True).
                type: str
            static_dns:
                description:
                - DNS servers to use.
                - Allows for a maximum of 2 addresses.
                type: list
            vlan:
                description:
                - VLAN number to use for the management network.
                type: int

author:
- Kevin Breit (@kbreit)
extends_documentation_fragment: meraki
'''

EXAMPLES = r'''
- name: Set WAN2 as static IP
  meraki_management_interface:
    auth_key: abc123
    state: present
    org_name: YourOrg
    net_id: YourNetId
    serial: AAAA-BBBB-CCCC
    wan2:
      wan_enabled: enabled
      using_static_ip: yes
      static_ip: 192.168.16.195
      static_gateway_ip: 192.168.16.1
      static_subnet_mask: 255.255.255.0
      static_dns:
        - 1.1.1.1
      vlan: 1
  delegate_to: localhost

- name: Query management information
  meraki_management_interface:
    auth_key: abc123
    state: query
    org_name: YourOrg
    net_id: YourNetId
    serial: AAAA-BBBB-CCCC
  delegate_to: localhost
'''

RETURN = r'''
data:
    description: Information about queried object.
    returned: success
    type: complex
    contains:
        wan1:
          description: Management configuration for WAN1 interface
          returned: success
          type: complex
          contains:
            wan_enabled:
                description: Enabled state of interface
                returned: success
                type: string
                sample: enabled
            using_static_ip:
                description: Boolean value of whether static IP assignment is used on interface
                returned: success
                type: bool
                sample: True
            static_ip:
                description: Assigned static IP
                returned: only if static IP assignment is used
                type: string
                sample: 192.0.1.2
            static_gateway_ip:
                description: Assigned static gateway IP
                returned: only if static IP assignment is used
                type: string
                sample: 192.0.1.1
            static_subnet_mask:
                description: Assigned netmask for static IP
                returned: only if static IP assignment is used
                type: string
                sample: 255.255.255.0
            static_dns:
                description: List of DNS IP addresses
                returned: only if static IP assignment is used
                type: list
                sample: ["1.1.1.1"]
            vlan:
                description: VLAN tag id of management VLAN
                returned: success
                type: int
                sample: 2
        wan2:
          description: Management configuration for WAN1 interface
          returned: success
          type: complex
          contains:
            wan_enabled:
                description: Enabled state of interface
                returned: success
                type: string
                sample: enabled
            using_static_ip:
                description: Boolean value of whether static IP assignment is used on interface
                returned: success
                type: bool
                sample: True
            static_ip:
                description: Assigned static IP
                returned: only if static IP assignment is used
                type: string
                sample: 192.0.1.2
            static_gateway_ip:
                description: Assigned static gateway IP
                returned: only if static IP assignment is used
                type: string
                sample: 192.0.1.1
            static_subnet_mask:
                description: Assigned netmask for static IP
                returned: only if static IP assignment is used
                type: string
                sample: 255.255.255.0
            static_dns:
                description: List of DNS IP addresses
                returned: only if static IP assignment is used
                type: list
                sample: ["1.1.1.1"]
            vlan:
                description: VLAN tag id of management VLAN
                returned: success
                type: int
                sample: 2
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.module_utils.network.meraki.meraki import MerakiModule, meraki_argument_spec


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    int_arg_spec = dict(wan_enabled=dict(type='str', choices=['enabled', 'disabled', 'not configured']),
                        using_static_ip=dict(type='bool'),
                        static_ip=dict(type='str'),
                        static_gateway_ip=dict(type='str'),
                        static_subnet_mask=dict(type='str'),
                        static_dns=dict(type='list', element='str'),
                        vlan=dict(type='int'),
                        )

    argument_spec = meraki_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'query', 'present'], default='query'),
                         net_name=dict(type='str'),
                         net_id=dict(type='str'),
                         serial=dict(type='str', required=True),
                         wan1=dict(type='dict', default=None, options=int_arg_spec, aliases=['mgmt1']),
                         wan2=dict(type='dict', default=None, options=int_arg_spec, aliases=['mgmt2']),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    meraki = MerakiModule(module, function='management_interface')
    meraki.params['follow_redirects'] = 'all'

    query_urls = {'management_interface': '/networks/{net_id}/devices/{serial}/managementInterfaceSettings'}

    meraki.url_catalog['get_one'].update(query_urls)

    if meraki.params['net_id'] and meraki.params['net_name']:
        meraki.fail_json('net_id and net_name are mutually exclusive.')
    if meraki.params['state'] == 'present':
        interfaces = ('wan1', 'wan2')
        for interface in interfaces:
            if meraki.params[interface] is not None:
                if meraki.params[interface]['using_static_ip'] is True:
                    if len(meraki.params[interface]['static_dns']) > 2:
                        meraki.fail_json("Maximum number of static DNS addresses is 2.")

    payload = dict()

    if meraki.params['state'] == 'present':
        interfaces = ('wan1', 'wan2')
        for interface in interfaces:
            if meraki.params[interface] is not None:
                wan_int = {'wanEnabled': meraki.params[interface]['wan_enabled'],
                           'usingStaticIp': meraki.params[interface]['using_static_ip'],
                           }
                if meraki.params[interface]['vlan'] is not None:
                    wan_int['vlan'] = meraki.params[interface]['vlan']
                if meraki.params[interface]['using_static_ip'] is True:
                    wan_int['staticIp'] = meraki.params[interface]['static_ip']
                    wan_int['staticGatewayIp'] = meraki.params[interface]['static_gateway_ip']
                    wan_int['staticSubnetMask'] = meraki.params[interface]['static_subnet_mask']
                    wan_int['staticDns'] = meraki.params[interface]['static_dns']
                payload[interface] = wan_int

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    org_id = meraki.params['org_id']
    if meraki.params['org_name']:
        org_id = meraki.get_org_id(meraki.params['org_name'])
    net_id = meraki.params['net_id']
    if net_id is None:
        nets = meraki.get_nets(org_id=org_id)
        net_id = meraki.get_net_id(net_name=meraki.params['net_name'], data=nets)

    if meraki.params['state'] == 'query':
        path = meraki.construct_path('get_one', net_id=net_id, custom={'serial': meraki.params['serial']})
        # meraki.fail_json(msg=path)
        response = meraki.request(path, method='GET')
        if meraki.status == 200:
            meraki.result['data'] = response
    elif meraki.params['state'] == 'present':
        path = meraki.construct_path('get_one', net_id=net_id, custom={'serial': meraki.params['serial']})
        original = meraki.request(path, method='GET')
        if meraki.is_update_required(original, payload):
            if meraki.check_mode is True:
                diff = recursive_diff(original, payload)
                original.update(payload)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1]}
                meraki.result['data'] = original
                meraki.result['changed'] = True
                meraki.exit_json(**meraki.result)
            response = meraki.request(path, method='PUT', payload=json.dumps(payload))
            if meraki.status == 200:
                diff = recursive_diff(original, response)
                meraki.result['diff'] = {'before': diff[0],
                                         'after': diff[1]}
                meraki.result['data'] = response
                meraki.result['changed'] = True
        else:
            meraki.result['data'] = original

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    meraki.exit_json(**meraki.result)


if __name__ == '__main__':
    main()
