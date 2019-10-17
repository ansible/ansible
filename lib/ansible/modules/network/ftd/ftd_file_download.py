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
module: ftd_file_download
short_description: Downloads files from Cisco FTD devices over HTTP(S)
description:
  - Downloads files from Cisco FTD devices including pending changes, disk files, certificates,
    troubleshoot reports, and backups.
version_added: "2.7"
author: "Cisco Systems, Inc. (@annikulin)"
options:
  operation:
    description:
      - The name of the operation to execute.
      - Only operations that return a file can be used in this module.
    required: true
    type: str
  path_params:
    description:
      - Key-value pairs that should be sent as path parameters in a REST API call.
    type: dict
  destination:
    description:
      - Absolute path of where to download the file to.
      - If destination is a directory, the module uses a filename from 'Content-Disposition' header specified by
        the server.
    required: true
    type: path
"""

EXAMPLES = """
- name: Download pending changes
  ftd_file_download:
    operation: 'getdownload'
    path_params:
      objId: 'default'
    destination: /tmp/
"""

RETURN = """
msg:
    description: The error message describing why the module failed.
    returned: error
    type: str
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.ftd.common import FtdServerError, HTTPMethod
from ansible.module_utils.network.ftd.fdm_swagger_client import OperationField, ValidationError, FILE_MODEL_NAME


def is_download_operation(op_spec):
    return op_spec[OperationField.METHOD] == HTTPMethod.GET and op_spec[OperationField.MODEL_NAME] == FILE_MODEL_NAME


def validate_params(connection, op_name, path_params):
    field_name = 'Invalid path_params provided'
    try:
        is_valid, validation_report = connection.validate_path_params(op_name, path_params)
        if not is_valid:
            raise ValidationError({
                field_name: validation_report
            })
    except Exception as e:
        raise ValidationError({
            field_name: str(e)
        })


def main():
    fields = dict(
        operation=dict(type='str', required=True),
        path_params=dict(type='dict'),
        destination=dict(type='path', required=True)
    )
    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=True)
    params = module.params
    connection = Connection(module._socket_path)

    op_name = params['operation']
    op_spec = connection.get_operation_spec(op_name)
    if op_spec is None:
        module.fail_json(msg='Operation with specified name is not found: %s' % op_name)
    if not is_download_operation(op_spec):
        module.fail_json(
            msg='Invalid download operation: %s. The operation must make GET request and return a file.' %
                op_name)

    try:
        path_params = params['path_params']
        validate_params(connection, op_name, path_params)
        if module.check_mode:
            module.exit_json(changed=False)
        connection.download_file(op_spec[OperationField.URL], params['destination'], path_params)
        module.exit_json(changed=False)
    except FtdServerError as e:
        module.fail_json(msg='Download request for %s operation failed. Status code: %s. '
                             'Server response: %s' % (op_name, e.code, e.response))
    except ValidationError as e:
        module.fail_json(msg=e.args[0])


if __name__ == '__main__':
    main()
