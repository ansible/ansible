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
module: ftd_file_upload
short_description: Uploads files to Cisco FTD devices over HTTP(S)
description:
  - Uploads files to Cisco FTD devices including disk files, backups, and upgrades.
version_added: "2.7"
author: "Cisco Systems, Inc. (@annikulin)"
options:
  operation:
    description:
      - The name of the operation to execute.
      - Only operations that upload file can be used in this module.
    required: true
    type: str
  file_to_upload:
    description:
      - Absolute path to the file that should be uploaded.
    required: true
    type: path
    version_added: "2.8"
  register_as:
    description:
      - Specifies Ansible fact name that is used to register received response from the FTD device.
    type: str
"""

EXAMPLES = """
- name: Upload disk file
  ftd_file_upload:
    operation: 'postuploaddiskfile'
    file_to_upload: /tmp/test1.txt
"""

RETURN = """
msg:
    description: The error message describing why the module failed.
    returned: error
    type: str
"""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import Connection
from ansible.module_utils.network.ftd.common import construct_ansible_facts, FtdServerError, HTTPMethod
from ansible.module_utils.network.ftd.fdm_swagger_client import OperationField


def is_upload_operation(op_spec):
    return op_spec[OperationField.METHOD] == HTTPMethod.POST or 'UploadStatus' in op_spec[OperationField.MODEL_NAME]


def main():
    fields = dict(
        operation=dict(type='str', required=True),
        file_to_upload=dict(type='path', required=True),
        register_as=dict(type='str'),
    )
    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=True)
    params = module.params
    connection = Connection(module._socket_path)

    op_spec = connection.get_operation_spec(params['operation'])
    if op_spec is None:
        module.fail_json(msg='Operation with specified name is not found: %s' % params['operation'])
    if not is_upload_operation(op_spec):
        module.fail_json(
            msg='Invalid upload operation: %s. The operation must make POST request and return UploadStatus model.' %
                params['operation'])

    try:
        if module.check_mode:
            module.exit_json()
        resp = connection.upload_file(params['file_to_upload'], op_spec[OperationField.URL])
        module.exit_json(changed=True, response=resp, ansible_facts=construct_ansible_facts(resp, module.params))
    except FtdServerError as e:
        module.fail_json(msg='Upload request for %s operation failed. Status code: %s. '
                             'Server response: %s' % (params['operation'], e.code, e.response))


if __name__ == '__main__':
    main()
