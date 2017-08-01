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

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
module: vdirect_file
author: Evgeny Fedoruk (@evgenyfedoruk)
short_description: Uploads a new or updates an existing runnable file into Radware vDirect server
description:
    - Uploads a new or updates an existing configuration template or workflow template into the Radware vDirect server.
      All parameters are not mandatory required since they may be set as environment variables.
notes:
    - Requires the Radware vdirect-client Python package on the host. This is as easy as pip
      install vdirect-client
version_added: "devel"
options:
  vdirect_ip:
    description:
     - Primary vDirect server IP address.
    required: false
  vdirect_user:
    description:
     - vDirect server username
    required: false
    default: None
  vdirect_password:
    description:
     - vDirect server password
    required: false
    default: None
  vdirect_wait:
    description:
     - Wait for async operation to complete.
    required: false
    default: None
  vdirect_secondary_ip:
    description:
     - Secondary vDirect server IP address.
    required: false
  vdirect_https_port:
    description:
     - vDirect server HTTPS port number.
    required: false
    default: None
  vdirect_http_port:
    description:
     - vDirect server HTTP port number.
    required: false
    default: None
  vdirect_timeout:
    description:
     - Amount of time to wait for async operation completion [seconds].
    required: false
    default: None
  vdirect_https:
    description:
     - Use HTTPS.
    required: false
    default: None
  vdirect_strict_http_results:
    description:
     - Throw exception for status codes 4xx,5xx or not.
    required: false
    default: None
  vdirect_ssl_verify_context:
    description:
     - SSL contect verification.
    required: false
    default: None
  file_name:
    description:
     - vDirect runnable file name to be uploaded. May be configuration template or workflow template.
    required: true

requirements:
  - "vdirect-client >= 4.1.1"
'''

EXAMPLES = '''
- name: vdirect_file
  vdirect_file:
      vdirect_primary_ip: 10.10.10.10
      vdirect_user: vDirect
      vdirect_password: radware
      file_name: /tmp/get_vlans.vm
'''

try:
    from vdirect_client import vdirect_client as rest_client
    HAS_REST_CLIENT = True
    import pkg_resources
    version = pkg_resources.get_distribution("vdirect_client").version
    if version.startswith("4.1.1"):
        HAS_REST_CLIENT_VERSION = True
    else:
        HAS_REST_CLIENT_VERSION = False
except ImportError:
    HAS_REST_CLIENT = False

TEMPLATE_EXTENSION = '.vm'
WORKFLOW_EXTENSION = '.zip'

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
                                             https=params['vdirect_https'],
                                             strict_http_results=params['vdirect_strict_http_results'],
                                             ssl_verify_context=params['vdirect_ssl_verify_context'])

    def upload(self, fqn):
        if fqn.endswith(TEMPLATE_EXTENSION):
            template_name = os.path.basename(fqn)
            template = rest_client.Template(self.client)
            runnable_file = open(fqn, 'r')
            file_content = runnable_file.read()

            result = template.create_from_source(file_content, template_name, fail_if_invalid=True)
            if result[rest_client.RESP_STATUS] == 409:
                template.upload_source(file_content, template_name, fail_if_invalid=True)
                result = "Template updated"
            else:
                result = "Template created"
        elif fqn.endswith(WORKFLOW_EXTENSION):
            workflow = rest_client.WorkflowTemplate(self.client)

            runnable_file = open(fqn, 'rb')
            file_content = runnable_file.read()
            result = workflow.create_template_from_archive(file_content, fail_if_invalid=True)
            if result[rest_client.RESP_STATUS] == 409:
                workflow.update_archive(file_content, os.path.splitext(os.path.basename(fqn))[0])
                result = "Workflow template updated"
            else:
                result = "Workflow template created"
        else:
            result = "The file_name parameter must have " \
                     "velocity script (.vm) extension or ZIP archive (.zip) extension"
        return result


def main():

    if not HAS_REST_CLIENT:
        raise ImportError("The python vdirect-client module is required")
    elif not HAS_REST_CLIENT_VERSION:
        raise ImportError("The python vdirect-client module version should be 4.1.1 and above")

    meta_args = dict(
        vdirect_ip=dict(
            required=False,
            default=None),
        vdirect_user=dict(
            required=False,
            default=None),
        vdirect_password=dict(
            required=False,
            no_log=True,
            type='str',
            default=None),
        vdirect_secondary_ip=dict(
            required=False,
            default=None),
        vdirect_https=dict(
            required=False,
            default=None),
        vdirect_wait=dict(
            required=False,
            default=None),
        vdirect_timeout=dict(
            required=False,
            default=None),
        vdirect_ssl_verify_context=dict(
            required=False,
            default=None),
        vdirect_https_port=dict(
            required=False,
            default=None),
        vdirect_http_port=dict(
            required=False,
            default=None),
        vdirect_strict_http_results=dict(
            required=False,
            default=None),
        file_name=dict(required=True, default=None),
    )

    module = AnsibleModule(
        argument_spec=meta_args
    )

    try:
        params = module.params
        vdirect_file = VdirectFile(module.params)
        result = vdirect_file.upload(params['file_name'])
        result = dict(result=result)
        module.exit_json(**result)
    except Exception as e:
        module.fail_json(msg=str(e))

import os
import os.path
from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()