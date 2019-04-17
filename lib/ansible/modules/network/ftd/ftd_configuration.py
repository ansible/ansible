#!/usr/bin/python

# Copyright (c) 2018 Cisco and/or its affiliates.
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: ftd_configuration
short_description: Manages configuration on Cisco FTD devices over REST API
description:
  - Manages configuration on Cisco FTD devices including creating, updating, removing configuration objects,
    scheduling and staring jobs, deploying pending changes, etc. All operations are performed over REST API.
version_added: "2.7"
author: "Cisco Systems, Inc. (@annikulin)"
options:
  operation:
    description:
      - The name of the operation to execute. Commonly, the operation starts with 'add', 'edit', 'get', 'upsert'
       or 'delete' verbs, but can have an arbitrary name too.
    required: true
    type: str
  data:
    description:
      - Key-value pairs that should be sent as body parameters in a REST API call
    type: dict
  query_params:
    description:
      - Key-value pairs that should be sent as query parameters in a REST API call.
    type: dict
  path_params:
    description:
      - Key-value pairs that should be sent as path parameters in a REST API call.
    type: dict
  register_as:
    description:
      - Specifies Ansible fact name that is used to register received response from the FTD device.
    type: str
  filters:
    description:
      - Key-value dict that represents equality filters. Every key is a property name and value is its desired value.
        If multiple filters are present, they are combined with logical operator AND.
    type: dict
"""

EXAMPLES = """
- name: Create a network object
  ftd_configuration:
    operation: "addNetworkObject"
    data:
      name: "Ansible-network-host"
      description: "From Ansible with love"
      subType: "HOST"
      value: "192.168.2.0"
      dnsResolution: "IPV4_AND_IPV6"
      type: "networkobject"
      isSystemDefined: false
    register_as: "hostNetwork"

- name: Delete the network object
  ftd_configuration:
    operation: "deleteNetworkObject"
    path_params:
      objId: "{{ hostNetwork['id'] }}"
"""

RETURN = """
response:
  description: HTTP response returned from the API call.
  returned: success
  type: dict
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.ftd.configuration import BaseConfigurationResource, CheckModeException, \
    FtdInvalidOperationNameError
from ansible.module_utils.network.ftd.fdm_swagger_client import ValidationError
from ansible.module_utils.network.ftd.common import construct_ansible_facts, FtdConfigurationError, \
    FtdServerError, FtdUnexpectedResponse


def main():
    fields = dict(
        operation=dict(type='str', required=True),
        data=dict(type='dict'),
        query_params=dict(type='dict'),
        path_params=dict(type='dict'),
        register_as=dict(type='str'),
        filters=dict(type='dict')
    )
    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=True)
    params = module.params

    connection = Connection(module._socket_path)
    resource = BaseConfigurationResource(connection, module.check_mode)
    op_name = params['operation']
    try:
        resp = resource.execute_operation(op_name, params)
        module.exit_json(changed=resource.config_changed, response=resp,
                         ansible_facts=construct_ansible_facts(resp, module.params))
    except FtdInvalidOperationNameError as e:
        module.fail_json(msg='Invalid operation name provided: %s' % e.operation_name)
    except FtdConfigurationError as e:
        module.fail_json(msg='Failed to execute %s operation because of the configuration error: %s' % (op_name, e.msg))
    except FtdServerError as e:
        module.fail_json(msg='Server returned an error trying to execute %s operation. Status code: %s. '
                             'Server response: %s' % (op_name, e.code, e.response))
    except FtdUnexpectedResponse as e:
        module.fail_json(msg=e.args[0])
    except ValidationError as e:
        module.fail_json(msg=e.args[0])
    except CheckModeException:
        module.exit_json(changed=False)


if __name__ == '__main__':
    main()
