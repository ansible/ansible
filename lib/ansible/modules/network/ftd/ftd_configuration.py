#!/usr/bin/python

# Copyright (c) 2018 Cisco Systems, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ftd_configuration
short_description: Manages ConfigEntity objects on Cisco FTD devices over REST API.
version_added: "2.7"
author: "Cisco Systems, Inc."
options:
  operation:
    description:
      - The name of the operation to execute. Commonly, the operation starts with 'add', 'edit', 'get'
       or 'delete' verbs, but can have an arbitrary name too. 
    required: true
  data:
    description:
      - Key-value pairs that should be sent as body parameters in a REST API call
  query_params:
    description:
      - Key-value pairs that should be sent as query parameters in a REST API call.
  path_params:
    description:
      - Key-value pairs that should be sent as path parameters in a REST API call.
  register_as:
    description:
      - Specifies Ansible fact name that is used to register received response from the FTD device.
  filters:
    description:
      - Key-value dict that represents equality filters. Every key is a property name and value is its desired value.
        If multiple filters are present, they are combined with logical operator AND.
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
from ansible.module_utils.network.ftd.common import HTTPMethod, construct_ansible_facts, FtdConfigurationError, \
    FtdServerError
from ansible.module_utils.network.ftd.configuration import BaseConfigurationResource
from ansible.module_utils.network.ftd.fdm_swagger_client import OperationField


def is_add_operation(operation_name, operation_spec):
    # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
    return operation_name.startswith('add') and operation_spec[OperationField.METHOD] == HTTPMethod.POST


def is_edit_operation(operation_name, operation_spec):
    # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
    return operation_name.startswith('edit') and operation_spec[OperationField.METHOD] == HTTPMethod.PUT


def is_delete_operation(operation_name, operation_spec):
    # Some endpoints have non-CRUD operations, so checking operation name is required in addition to the HTTP method
    return operation_name.startswith('delete') and operation_spec[OperationField.METHOD] == HTTPMethod.DELETE


def is_find_by_filter_operation(operation_name, operation_spec, params):
    """
    Checks whether the called operation is 'find by filter'. This operation fetches all objects and finds
    the matching ones by the given filter. As filtering is done on the client side, this operation should be used
    only when selected filters are not implemented on the server side.

    :param operation_name: name of the operation being called by the user
    :type operation_name: str
    :param operation_spec: specification of the operation being called by the user
    :type operation_spec: dict
    :param params: module parameters
    :return: True if called operation is find by filter, otherwise False
    :rtype: bool
    """
    is_get_list_operation = operation_name.startswith('get') and operation_name.endswith('List')
    is_get_method = operation_spec[OperationField.METHOD] == HTTPMethod.GET
    return is_get_list_operation and is_get_method and params['filters']


def main():
    fields = dict(
        operation=dict(type='str', required=True),
        data=dict(type='dict'),
        query_params=dict(type='dict'),
        path_params=dict(type='dict'),
        register_as=dict(type='str'),
        filters=dict(type='dict')
    )
    module = AnsibleModule(argument_spec=fields)
    params = module.params
    connection = Connection(module._socket_path)

    op_name = params['operation']
    op_spec = connection.get_operation_spec(op_name)
    if op_spec is None:
        module.fail_json(msg='Invalid operation name provided: %s' % op_name)

    data, query_params, path_params = params['data'], params['query_params'], params['path_params']
    # TODO: implement validation for input parameters

    resource = BaseConfigurationResource(connection)

    try:
        if is_add_operation(op_name, op_spec):
            resp = resource.add_object(op_spec[OperationField.URL], data, path_params, query_params)
        elif is_edit_operation(op_name, op_spec):
            resp = resource.edit_object(op_spec[OperationField.URL], data, path_params, query_params)
        elif is_delete_operation(op_name, op_spec):
            resp = resource.delete_object(op_spec[OperationField.URL], path_params)
        elif is_find_by_filter_operation(op_name, op_spec, params):
            resp = resource.get_objects_by_filter(op_spec[OperationField.URL], params['filters'], path_params,
                                                  query_params)
        else:
            resp = resource.send_request(op_spec[OperationField.URL], op_spec[OperationField.METHOD], data, path_params,
                                         query_params)

        module.exit_json(changed=resource.config_changed, response=resp,
                         ansible_facts=construct_ansible_facts(resp, module.params))
    except FtdConfigurationError as e:
        module.fail_json(msg='Failed to execute %s operation because of the configuration error: %s' % (op_name, e))
    except FtdServerError as e:
        module.fail_json(msg='Server returned an error trying to execute %s operation. Status code: %s. '
                             'Server response: %s' % (op_name, e.code, e.response))


if __name__ == '__main__':
    main()
