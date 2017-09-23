#!/usr/bin/python
#
# Ansible module to manage arbitrary objects via API in fortigate devices
# (c) 2017, Will Wagner <willwagner602@gmail.com> and Eugene Opredelennov <eoprede@gmail.com>
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fortios_api
extends_documentation_fragment: fortios_api_doc
version_added: "2.5"
short_description: Manages arbitrarily designated fortios configurations.
description:
    - Manages arbitrarily designated fortios configurations. Can be used to edit any endpoint, as long as proper API path is provided.
author:
    - Will Wagner (@willwagner602)
      Eugene Opredelennov (@eoprede)
notes:
    - Tested against Fortigate v5.4.5 VM

options:
    endpoint_information:
      description: Information about the endpoint.
      required: true
      suboptions:
            endpoint:
                required: true
                description: identifies the string to be added to the api
                             URL to access the appropriate endpoint.
            list_identifier:
                required: true
                description: The identifier used by this configuration to identify the list of
                             objects that should be used to update the endpoint's configuration.
            object_identifier:
                required: false
                description: The unique identifier used by this endpoint to differentiate objects.
                             Typically 'name', 'id', or some variation. Not required for endpoints which
                             contain only a single object.
            permanent_objects:
                required: false
                description: A list of identifiers for objects at the endpoint that cannot be deleted.

'''
EXAMPLES = '''
- name: Update router static
  fortios_api:
  endpoint_information:
    endpoint: cmdb/router/static
    list_identifier: routers
    object_identifier: seq-num
    permanent_objects:
  conn_params:
    fortigate_username: admin
    fortigate_password: test
    fortigate_ip: 1.2.3.4
    port: 10080
    verify: false
    secure: false
    proxies:
        http: socks5://127.0.0.1:9000
  routers:
  - seq-num: 1
    status: enable
    dst: 0.0.0.0 0.0.0.0
    gateway: 192.0.2.1
    distance: 10
    weight: 0
    priority: 0
    device: port1
    comment: ''
    blackhole: disable
    dynamic-gateway: disable
    virtual-wan-link: disable
    dstaddr: ''
    internet-service: 0
    internet-service-custom: ''

  - seq-num: 2
    status: enable
    dst: 0.0.0.0 0.0.0.0
    gateway: 192.0.3.1
    distance: 10
    weight: 0
    priority: 0
    device: port2
    comment: ''
    blackhole: disable
    dynamic-gateway: disable
    virtual-wan-link: disable
    dstaddr: ''
    internet-service: 0
    internet-service-custom: ''
'''

RETURN = '''
proposed:
    description: k/v pairs of parameters passed into module and sent to the device for changes
    returned: always
    type: list
    sample: '[{"blackhole": "disable", "comment": "", "device": "port1", "distance": 10,
              "dst": "0.0.0.0 0.0.0.0", "dstaddr": "", "dynamic-gateway": "disable",
              "gateway": "192.0.2.1", "internet-service": 0, "internet-service-custom": "",
              "priority": 0, "seq-num": 1, "status": "enable", "virtual-wan-link": "disable", "weight": 0},
              {"blackhole": "disable", "comment": "", "device": "port2", "distance": 10,
              "dst": "0.0.0.0 0.0.0.0", "dstaddr": "", "dynamic-gateway": "disable",
              "gateway": "192.0.3.1", "internet-service": 0, "internet-service-custom": "",
              "priority": 0, "seq-num": 2, "status": "enable", "virtual-wan-link": "disable", "weight": 0}]'
existing:
    description: k/v pairs of existing configuration
    returned: always
    type: list
    sample: '[{"blackhole": "disable", "comment": "", "device": "port1", "distance": 10,
              "dst": "0.0.0.0 0.0.0.0", "dstaddr": "", "dynamic-gateway": "disable",
              "gateway": "192.0.2.1", "internet-service": 0, "internet-service-custom": "",
              "priority": 0, "q_origin_key": "1", "seq-num": 1, "status": "enable",
              "virtual-wan-link": "disable", "weight": 0}]'
end_state:
    description: k/v pairs of configuration after module execution
    returned: always
    type: list
    sample: '[{"blackhole": "disable", "comment": "", "device": "port1", "distance": 10,
              "dst": "0.0.0.0 0.0.0.0", "dstaddr": "", "dynamic-gateway": "disable",
              "gateway": "192.0.2.1", "internet-service": 0, "internet-service-custom": "",
              "priority": 0, "q_origin_key": "1", "seq-num": 1, "status": "enable",
              "virtual-wan-link": "disable", "weight": 0},
              {"blackhole": "disable", "comment": "", "device": "port2", "distance": 10,
              "dst": "0.0.0.0 0.0.0.0", "dstaddr": "", "dynamic-gateway": "disable",
              "gateway": "192.0.3.1", "internet-service": 0, "internet-service-custom": "",
              "priority": 0, "q_origin_key": "2", "seq-num": 2, "status": "enable",
              "virtual-wan-link": "disable", "weight": 0}]'
changed:
    description: Whether a change was required for the device configuration.
    returned: always
    type: boolean
    sample: true
msg:
    description: A short description of the success of the change and status of the device.
    returned: always
    type: str
    sample: "Configuration updated."
'''

from ansible.module_utils.fortios import API

interface_api_args = {
    "from_configs": True
}


def main():
    forti_api = API(interface_api_args)
    forti_api.apply_configuration_to_endpoint()


if __name__ == "__main__":
    main()
