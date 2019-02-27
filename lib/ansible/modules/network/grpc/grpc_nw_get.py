#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: grpc_nw_get
version_added: "2.8"
author:
    - "Ganesh Nalawade (@ganeshrn)"
short_description: Fetch configuration/state data from gRPC enabled target hosts.
description:
    - gRPC is a high performance, open-source universal RPC framework.
    - This module allows the user to fetch configuration and state data from gRPC
      enabled devices.
options:
  section:
    description:
      - This option specifies the string which acts as a filter to restrict the portions of
        the data to be retrieved from the target host device. If this option is not specified the entire
        configuration or state data is returned in response provided it is supported by target host.
  command:
    description:
      - The option specifies the command to be executed on the target host and return the response
        in result. This option is supported if the gRPC target host supports executing CLI command
        over the gRPC connection.
  display:
    description:
      - Encoding scheme to use when serializing output from the device. The encoding scheme
        value depends on the capability of the gRPC server running on the target host.
        The values can be I(json), I(text) etc.
  data_type:
    description:
      - The type of data that should be fetched from the target host. The value depends on the
        capability of the gRPC server running on target host. The values can be I(config), I(oper)
        etc. based on what is supported by the gRPC server. By default it will return both configuration
        and operational state data in response.
requirements:
  - grpcio
  - protobuf

notes:
  - This module requires the gRPC system service be enabled on
    the target host being managed.
  - This module supports the use of connection=grpc.
  - This module requires the value of 'ansible_network_os' be defined as an inventory variable.
  - Tested against iosxrv 9k version 6.1.2.
"""

EXAMPLES = """
- name: Get bgp configuration data
  grpc_nw_get:
    section:  '{"Cisco-IOS-XR-ipv4-bgp-cfg:bgp": [null]}'

- name: Get configuration JSON format over secure TLS channel
  grpc_nw_get:
    display: json
    data: config
  vars:
    ansible_root_certificates_file: /home/username/ems.pem
    ansible_grpc_channel_options:
      'grpc.ssl_target_name_override': 'ems.cisco.com'

- name: run cli command
  grpc_nw_get:
    command: 'show version'
    display: text
"""

RETURN = """
stdout:
  description: The raw string containing configuration or state data
               received from the gRPC server.
  returned: always apart from low-level errors (such as action plugin)
  type: str
  sample: '...'
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low-level errors (such as action plugin)
  type: list
  sample: ['...', '...']
output:
  description: A dictionary representing a JSON-formatted response, if the response
               is a valid json string
  returned: when the device response is valid JSON
  type: list
  sample: |
        [{
            "Cisco-IOS-XR-ip-static-cfg:router-static": {
                "default-vrf": {
                    "address-family": {
                        "vrfipv4": {
                            "vrf-unicast": {
                                "vrf-prefixes": {
                                    "vrf-prefix": [
                                        {
                                            "prefix": "0.0.0.0",
                                            "prefix-length": 0,
                                            "vrf-route": {
                                                "vrf-next-hop-table": {
                                                    "vrf-next-hop-interface-name-next-hop-address": [
                                                        {
                                                            "interface-name": "MgmtEth0/RP0/CPU0/0",
                                                            "next-hop-address": "10.0.2.2"
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }]
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import ConnectionError
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.grpc.grpc import get_capabilities, get, run_cli


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        section=dict(),
        command=dict(),
        display=dict(),
        data_type=dict()
    )

    mutually_exclusive = [['section', 'command']]

    module = AnsibleModule(argument_spec=argument_spec,
                           mutually_exclusive=mutually_exclusive,
                           supports_check_mode=True)

    capabilities = get_capabilities(module)

    operations = capabilities['server_capabilities']

    section = module.params['section']
    command = module.params['command']
    display = module.params['display']
    data_type = module.params['data_type']

    if display and display not in operations.get('display', []):
        module.fail_json(msg="display option '%s' is not supported on this target host" % display)

    if command and not operations.get('supports_cli_command', False):
        module.fail_json(msg="command option '%s' is not supported on this target host" % command)

    if data_type and data_type not in operations.get('data_type', []):
        module.fail_json(msg="data_type option '%s' is not supported on this target host" % data_type)

    result = {'changed': False}

    try:
        if command:
            response, err = run_cli(module, command, display)
        else:
            response, err = get(module, section, data_type)

        try:
            output = module.from_json(response)
        except ValueError:
            output = None
    except ConnectionError as exc:
        module.fail_json(msg=to_text(exc, errors='surrogate_then_replace'), code=exc.code)

    result['stdout'] = response

    if output:
        result['output'] = to_list(output)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
