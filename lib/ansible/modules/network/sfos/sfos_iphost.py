#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Rubén del Campo Gómez <yo@rubendelcampo.es>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = """
---
module: sfos_iphost

author:
  - Rubén del Campo Gómez (@rdelcampog)

short_description: create, update or destroy IP Host in Sophos XG

description:
  - Create, update or destroy a IP Host in Sophos XG.

version_added: "2.8"

options:
  name:
    description:
      - Enter a descriptive name for the IP Host. Will be used to identify the entry.
    type: string
    required: true
  ipfamily:
    description:
      - IP Family to which the IP Host belongs: IPv4 or IPv6.
    type: string
    required: false
    default: IPv4
  hosttype:
    description:
      - Select the type of Host: IP, Network, IP Range or IP List. Required if state is 'present'.
    type: string
    choices:
      - IP
      - Network
      - IPRange
      - IPList
  ipaddress:
    description:
      - Specify IP Address. Required if the host type selected is 'IP' or 'Network'.
    type: string
    required: false
  subnet:
    description:
      - Specify Subnet address. Required if the host type selected is 'Network'.
    type: string
    required: false
  startipaddress:
    description:
      - Specify the starting IP address of the IP Range. Required if host type selected is 'IPRange'.
    type: string
    required: false
  endipaddress:
    description:
      - Specify the end IP address of the IP Range. Required if host type selected is 'IPRange'.
    type: string
    required: false
  listofipaddresses:
    description:
      - Specify the list of IP addresses. Required if host type selected is 'IPList'.
    type: list
    required: false
  hostgrouplist:
    description:
      - List of host groups to which the Host belongs. If not present, values already set preserves. If set but empty, current values are deleted.
    type: list
    required: false

extends_documentation_fragment:
    - sfos
"""

EXAMPLES = """
# Note: These examples do not set authentication or endpoint details like username, password, host or port.

- name: Create SophosXG IP Host list for GoogleDNS
  sfos_iphost:
    name: 'Google DNS Servers'
    hosttype: 'IPList'
    listofipaddresses:
        - '8.8.8.8'
        - '8.8.4.4'
    state: present

- name: Create SophosXG IP Host for localhost
  sfos_iphost:
    name: 'localhost'
    hosttype: 'IP'
    ipaddress: '127.0.0.1'
    state: present

- name: Remove SophosXG IP Host for GoogleDNS
  sfos_iphost:
    name: 'Google DNS Servers'
    state: absent
"""

RETURN = """
result:
  description: The IP Host object that was created
  returned: success
  type: complex
  contains:
    name:
      description: Descriptive name for the IP Host. Will be used to identify the entry.
      type: string
    ipfamily:
      description: IP Family to which the IP Host belongs: IPv4 or IPv6.
      type: string
    hosttype:
      description: The type of IP Host, can be IP, Network, IPRange or IPList.
      type: string
    ipaddress:
      description: The IP Address for this IP Host, applicable if the host type selected is 'IP' or 'Network'.
      type: string
    subnet:
      description: The subnet mask for this IP Host, applicable if the host type selected is 'Network'.
      type: string
    startipaddress:
      description: The starting IP address of the IP Range, applicable if host type selected is 'IPRange'.
      type: string
    endipaddress:
      description: The ending IP address of the IP Range, applicable if host type selected is 'IPRange'.
      type: string
    listofipaddresses:
      description: The list of IP address of the IP Range, applicable if host type selected is 'IPList'.
      type: list
    hostgrouplist:
      description: A list of host groups to which this IP Host belongs.
      type: list
"""

from ansible.module_utils.sfos_utils import SFOS, SFOSModule
from ansible.module_utils._text import to_native


def main():
    endpoint = "IPHost"
    key_to_check_for_changes = ["name", "hostgrouplist"]

    bool_keys = {}

    argument_spec = dict(
        name=dict(type='str', required=True),
        ipfamily=dict(type='str', required=False, default="IPv4", choices=["IPv4", "IPv6"]),
        hosttype=dict(type='str', required=False, choices=["IP", "Network", "IPRange", "IPList"]),
        ipaddress=dict(type='str', required=False),
        subnet=dict(type='str', required=False),
        startipaddress=dict(type='str', required=False),
        endipaddress=dict(type='str', required=False),
        listofipaddresses=dict(type='list', required=False),
        hostgrouplist=dict(type='list', required=False, item="HostGroup"),
    )

    required_if = [
        ["state", "present", ["hosttype"]],
        ["hosttype", "IP", ["ipaddress"]],
        ["hosttype", "Network", ["ipaddress", "subnet"]],
        ["hosttype", "IPRange", ["startipaddress", "endipaddress"]],
        ["hosttype", "IPList", ["listofipaddresses"]],
    ]

    module = SFOSModule(argument_spec, required_if=required_if)
    try:
        SFOS(module, endpoint, key_to_check_for_changes, bool_keys, argument_spec).execute()
    except Exception as e:
        module.fail_json(msg=to_native(e))


if __name__ == '__main__':
    main()
