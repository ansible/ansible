#!/usr/bin/python

# Copyright (c) 2018 Cisco Systems, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ftd_file_upload
short_description: Uploads files to Cisco FTD devices over HTTP(S)
description:
  - Uploads files to Cisco FTD devices including disk files, backups, and upgrades.
version_added: "2.7"
author: "Cisco Systems, Inc."
options:
  operation:
    description:
      - The name of the operation to execute. 
      - Only operations that upload file can be used in this module.
    required: true
  fileToUpload:
    description:
      - Absolute path to the file that should be uploaded.
    required: true
  register_as:
    description:
      - Specifies Ansible fact name that is used to register received response from the FTD device.
"""

EXAMPLES = """
- name: Upload disk file
  ftd_file_upload:
    operation: 'postuploaddiskfile'
    fileToUpload: /tmp/test1.txt
"""

RETURN = """
msg:
    description: the error message describing why the module failed
    returned: error
    type: string
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
        fileToUpload=dict(type='path', required=True),
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
        resp = connection.upload_file(params['fileToUpload'], op_spec[OperationField.URL])
        module.exit_json(changed=True, response=resp, ansible_facts=construct_ansible_facts(resp, module.params))
    except FtdServerError as e:
        module.fail_json(msg='Upload request for %s operation failed. Status code: %s. '
                             'Server response: %s' % (params['operation'], e.code, e.response))


if __name__ == '__main__':
    main()
