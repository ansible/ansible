#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage Check Point Firewall (c) 2019
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

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_host
short_description: Manages host objects on Check Point over Web Services API
description:
  - Manages host objects on Check Point devices including creating, updating and removing objects.
  - All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  ip_address:
    description:
      - IPv4 or IPv6 address. If both addresses are required use ipv4-address and ipv6-address fields explicitly.
    type: str
  ipv4_address:
    description:
      - IPv4 address.
    type: str
  ipv6_address:
    description:
      - IPv6 address.
    type: str
  interfaces:
    description:
      - Host interfaces.
    type: list
    suboptions:
      name:
        description:
          - Interface name.
        type: str
      subnet:
        description:
          - IPv4 or IPv6 network address. If both addresses are required use subnet4 and subnet6 fields explicitly.
        type: str
      subnet4:
        description:
          - IPv4 network address.
        type: str
      subnet6:
        description:
          - IPv6 network address.
        type: str
      mask_length:
        description:
          - IPv4 or IPv6 network mask length. If both masks are required use mask-length4 and mask-length6 fields explicitly. Instead of IPv4 mask
            length it is possible to specify IPv4 mask itself in subnet-mask field.
        type: int
      mask_length4:
        description:
          - IPv4 network mask length.
        type: int
      mask_length6:
        description:
          - IPv6 network mask length.
        type: int
      subnet_mask:
        description:
          - IPv4 network mask.
        type: str
      color:
        description:
          - Color of the object. Should be one of existing colors.
        type: str
        choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange',
                 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray',
                 'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive',
                 'orange', 'red', 'sienna', 'yellow']
      comments:
        description:
          - Comments string.
        type: str
      details_level:
        description:
          - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
            representation of the object.
        type: str
        choices: ['uid', 'standard', 'full']
      ignore_warnings:
        description:
          - Apply changes ignoring warnings.
        type: bool
      ignore_errors:
        description:
          - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
        type: bool
  nat_settings:
    description:
      - NAT settings.
    type: dict
    suboptions:
      auto_rule:
        description:
          - Whether to add automatic address translation rules.
        type: bool
      ip_address:
        description:
          - IPv4 or IPv6 address. If both addresses are required use ipv4-address and ipv6-address fields explicitly. This parameter is not
            required in case "method" parameter is "hide" and "hide-behind" parameter is "gateway".
        type: str
      ipv4_address:
        description:
          - IPv4 address.
        type: str
      ipv6_address:
        description:
          - IPv6 address.
        type: str
      hide_behind:
        description:
          - Hide behind method. This parameter is not required in case "method" parameter is "static".
        type: str
        choices: ['gateway', 'ip-address']
      install_on:
        description:
          - Which gateway should apply the NAT translation.
        type: str
      method:
        description:
          - NAT translation method.
        type: str
        choices: ['hide', 'static']
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  host_servers:
    description:
      - Servers Configuration.
    type: dict
    suboptions:
      dns_server:
        description:
          - Gets True if this server is a DNS Server.
        type: bool
      mail_server:
        description:
          - Gets True if this server is a Mail Server.
        type: bool
      web_server:
        description:
          - Gets True if this server is a Web Server.
        type: bool
      web_server_config:
        description:
          - Web Server configuration.
        type: dict
        suboptions:
          additional_ports:
            description:
              - Server additional ports.
            type: list
          application_engines:
            description:
              - Application engines of this web server.
            type: list
          listen_standard_port:
            description:
              - Whether server listens to standard port.
            type: bool
          operating_system:
            description:
              - Operating System.
            type: str
            choices: ['sparc linux', 'windows', 'other', 'x86 linux', 'sparc solaris']
          protected_by:
            description:
              - Network object which protects this server identified by the name or UID.
            type: str
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green',
             'pink', 'turquoise', 'dark blue', 'firebrick', 'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon',
             'coral', 'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of the object to a fully detailed
        representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-host
  cp_mgmt_host:
    ip_address: 192.0.2.1
    name: New Host 1
    state: present

- name: set-host
  cp_mgmt_host:
    color: green
    ipv4_address: 192.0.2.2
    name: New Host 1
    state: present

- name: delete-host
  cp_mgmt_host:
    name: New Host 1
    state: absent
"""

RETURN = """
cp_mgmt_host:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str'),
        ipv4_address=dict(type='str'),
        ipv6_address=dict(type='str'),
        interfaces=dict(type='list', options=dict(
            name=dict(type='str'),
            subnet=dict(type='str'),
            subnet4=dict(type='str'),
            subnet6=dict(type='str'),
            mask_length=dict(type='int'),
            mask_length4=dict(type='int'),
            mask_length6=dict(type='int'),
            subnet_mask=dict(type='str'),
            color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan',
                                            'dark green', 'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick',
                                            'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral',
                                            'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
                                            'sienna', 'yellow']),
            comments=dict(type='str'),
            details_level=dict(type='str', choices=['uid', 'standard', 'full']),
            ignore_warnings=dict(type='bool'),
            ignore_errors=dict(type='bool')
        )),
        nat_settings=dict(type='dict', options=dict(
            auto_rule=dict(type='bool'),
            ip_address=dict(type='str'),
            ipv4_address=dict(type='str'),
            ipv6_address=dict(type='str'),
            hide_behind=dict(type='str', choices=['gateway', 'ip-address']),
            install_on=dict(type='str'),
            method=dict(type='str', choices=['hide', 'static'])
        )),
        tags=dict(type='list'),
        host_servers=dict(type='dict', options=dict(
            dns_server=dict(type='bool'),
            mail_server=dict(type='bool'),
            web_server=dict(type='bool'),
            web_server_config=dict(type='dict', options=dict(
                additional_ports=dict(type='list'),
                application_engines=dict(type='list'),
                listen_standard_port=dict(type='bool'),
                operating_system=dict(type='str', choices=['sparc linux', 'windows', 'other', 'x86 linux', 'sparc solaris']),
                protected_by=dict(type='str')
            ))
        )),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green',
                                        'khaki', 'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
                                        'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral', 'sea green',
                                        'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red', 'sienna',
                                        'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'host'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
