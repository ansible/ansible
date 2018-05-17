#!/usr/bin/python
#  -*- coding: utf-8 -*-
#
# Copyright 2017 Radware LTD.
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
module: vdirect_file
author: Evgeny Fedoruk @ Radware LTD (@evgenyfedoruk)
short_description: Uploads a new or updates an existing runnable file into Radware vDirect server
description:
    - Uploads a new or updates an existing configuration template or workflow template into the Radware vDirect server.
      All parameters may be set as environment variables.
notes:
    - Requires the Radware vdirect-client Python package on the host. This is as easy as
      C(pip install vdirect-client)
version_added: "2.4"
options:
  vdirect_ip:
    description:
     - Primary vDirect server IP address, may be set as VDIRECT_IP environment variable.
    required: true
  vdirect_user:
    description:
     - vDirect server username, may be set as VDIRECT_USER environment variable.
    required: true
  vdirect_password:
    description:
     - vDirect server password, may be set as VDIRECT_PASSWORD environment variable.
    required: true
  vdirect_secondary_ip:
    description:
     - Secondary vDirect server IP address, may be set as VDIRECT_SECONDARY_IP environment variable.
  vdirect_wait:
    description:
     - Wait for async operation to complete, may be set as VDIRECT_WAIT environment variable.
    type: bool
    default: 'yes'
  vdirect_https_port:
    description:
     - vDirect server HTTPS port number, may be set as VDIRECT_HTTPS_PORT environment variable.
    default: 2189
  vdirect_http_port:
    description:
     - vDirect server HTTP port number, may be set as VDIRECT_HTTP_PORT environment variable.
    default: 2188
  vdirect_timeout:
    description:
     - Amount of time to wait for async operation completion [seconds],
     - may be set as VDIRECT_TIMEOUT environment variable.
    default: 60
  vdirect_use_ssl:
    description:
     - If C(no), an HTTP connection will be used instead of the default HTTPS connection,
     - may be set as VDIRECT_HTTPS or VDIRECT_USE_SSL environment variable.
    type: bool
    default: 'yes'
  vdirect_validate_certs:
    description:
     - If C(no), SSL certificates will not be validated,
     - may be set as VDIRECT_VALIDATE_CERTS or VDIRECT_VERIFY environment variable.
     - This should only set to C(no) used on personally controlled sites using self-signed certificates.
    type: bool
    default: 'yes'
  file_name:
    description:
     - vDirect runnable file name to be uploaded.
     - May be velocity configuration template (.vm) or workflow template zip file (.zip).
    required: true

requirements:
  - "vdirect-client >= 4.1.1"
'''

EXAMPLES = '''
- name: vdirect_file
  vdirect_file:
      vdirect_ip: 10.10.10.10
      vdirect_user: vDirect
      vdirect_password: radware
      file_name: /tmp/get_vlans.vm
'''

RETURN = '''
result:
    description: Message detailing upload result
    returned: success
    type: string
    sample: "Workflow template created"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback
import os
import os.path

try:
    from vdirect_client import rest_client
    HAS_REST_CLIENT = True
except ImportError:
    HAS_REST_CLIENT = False

TEMPLATE_EXTENSION = '.vm'
WORKFLOW_EXTENSION = '.zip'
WRONG_EXTENSION_ERROR = 'The file_name parameter must have ' \
                        'velocity script (.vm) extension or ZIP archive (.zip) extension'
CONFIGURATION_TEMPLATE_CREATED_SUCCESS = 'Configuration template created'
CONFIGURATION_TEMPLATE_UPDATED_SUCCESS = 'Configuration template updated'
WORKFLOW_TEMPLATE_CREATED_SUCCESS = 'Workflow template created'
WORKFLOW_TEMPLATE_UPDATED_SUCCESS = 'Workflow template updated'

meta_args = dict(
    vdirect_ip=dict(required=True, fallback=(env_fallback, ['VDIRECT_IP'])),
    vdirect_user=dict(required=True, fallback=(env_fallback, ['VDIRECT_USER'])),
    vdirect_password=dict(
        required=True, fallback=(env_fallback, ['VDIRECT_PASSWORD']),
        no_log=True, type='str'),
    vdirect_secondary_ip=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_SECONDARY_IP']),
        default=None),
    vdirect_use_ssl=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTPS', 'VDIRECT_USE_SSL']),
        default=True, type='bool'),
    vdirect_wait=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_WAIT']),
        default=True, type='bool'),
    vdirect_timeout=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_TIMEOUT']),
        default=60, type='int'),
    vdirect_validate_certs=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_VERIFY', 'VDIRECT_VALIDATE_CERTS']),
        default=True, type='bool'),
    vdirect_https_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTPS_PORT']),
        default=2189, type='int'),
    vdirect_http_port=dict(
        required=False, fallback=(env_fallback, ['VDIRECT_HTTP_PORT']),
        default=2188, type='int'),
    file_name=dict(required=True)
)


class FileException(Exception):
    def __init__(self, reason, details):
        self.reason = reason
        self.details = details

    def __str__(self):
        return 'Reason: {0}. Details:{1}.'.format(self.reason, self.details)


class InvalidSourceException(FileException):
    def __init__(self, message):
        super(InvalidSourceException, self).__init__(
            'Error parsing file', repr(message))


class VdirectFile(object):
    def __init__(self, params):
        self.client = rest_client.RestClient(params['vdirect_ip'],
                                             params['vdirect_user'],
                                             params['vdirect_password'],
                                             wait=params['vdirect_wait'],
                                             secondary_vdirect_ip=params['vdirect_secondary_ip'],
                                             https_port=params['vdirect_https_port'],
                                             http_port=params['vdirect_http_port'],
                                             timeout=params['vdirect_timeout'],
                                             https=params['vdirect_use_ssl'],
                                             verify=params['vdirect_validate_certs'])

    def upload(self, fqn):
        if fqn.endswith(TEMPLATE_EXTENSION):
            template_name = os.path.basename(fqn)
            template = rest_client.Template(self.client)
            runnable_file = open(fqn, 'r')
            file_content = runnable_file.read()

            result_to_return = CONFIGURATION_TEMPLATE_CREATED_SUCCESS
            result = template.create_from_source(file_content, template_name, fail_if_invalid=True)
            if result[rest_client.RESP_STATUS] == 409:
                result_to_return = CONFIGURATION_TEMPLATE_UPDATED_SUCCESS
                result = template.upload_source(file_content, template_name, fail_if_invalid=True)

            if result[rest_client.RESP_STATUS] == 400:
                raise InvalidSourceException(str(result[rest_client.RESP_STR]))
        elif fqn.endswith(WORKFLOW_EXTENSION):
            workflow = rest_client.WorkflowTemplate(self.client)

            runnable_file = open(fqn, 'rb')
            file_content = runnable_file.read()

            result_to_return = WORKFLOW_TEMPLATE_CREATED_SUCCESS
            result = workflow.create_template_from_archive(file_content, fail_if_invalid=True)
            if result[rest_client.RESP_STATUS] == 409:
                result_to_return = WORKFLOW_TEMPLATE_UPDATED_SUCCESS
                result = workflow.update_archive(file_content, os.path.splitext(os.path.basename(fqn))[0])

            if result[rest_client.RESP_STATUS] == 400:
                raise InvalidSourceException(str(result[rest_client.RESP_STR]))
        else:
            result_to_return = WRONG_EXTENSION_ERROR
        return result_to_return


def main():

    module = AnsibleModule(argument_spec=meta_args)

    if not HAS_REST_CLIENT:
        module.fail_json(msg="The python vdirect-client module is required")

    try:
        vdirect_file = VdirectFile(module.params)
        result = vdirect_file.upload(module.params['file_name'])
        result = dict(result=result)
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
