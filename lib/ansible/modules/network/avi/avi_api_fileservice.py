#!/usr/bin/python
############################################################################
#
# AVI CONFIDENTIAL
# __________________
#
# [2013] - [2018] Avi Networks Incorporated
# All Rights Reserved.
#
# NOTICE: All information contained herein is, and remains the property
# of Avi Networks Incorporated and its suppliers, if any. The intellectual
# and technical concepts contained herein are proprietary to Avi Networks
# Incorporated, and its suppliers and are covered by U.S. and Foreign
# Patents, patents in process, and are protected by trade secret or
# copyright law, and other laws. Dissemination of this information or
# reproduction of this material is strictly forbidden unless prior written
# permission is obtained from Avi Networks Incorporated.
###

"""
# Created on April 25, 2018
#
# @author: Chaitanya Deshpande (chaitanya.deshpande@avinetworks.com) GitHub ID: chaitanyaavi
#
# module_check: not supported
#
# Copyright: (c) 2017 Chaitanya Deshpande, <chaitanya.deshpande@avinetworks.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
"""

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: avi_api_fileservice
author: Chaitanya Deshpande (chaitanya.deshpande@avinetworks.com)

short_description: Avi API Module for fileservice
description:
    - This module can be used for calling fileservice resources to upload/download files 
version_added: 2.6
requirements: [ avisdk ]
options:
    http_method:
        description:
            - Allowed HTTP methods GET for download and POST for upload.
        choices: ["get", "post"]
        required: true
    file_path:
        description:
            - Local file path of file to be uploaded or downloaded file
        required: true
    params:
        description:
            - Query parameters passed to the HTTP API.
    path:
        description:
            - 'Path for Avi API resource. For example, C(path: seova) will translate to C(api/fileservice/seova).'
        required: true
    timeout:
        description:
            - Timeout (in seconds) for Avi API calls.
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''

  - name: Download se image from controller
    avi_api_fileservice:
      controller: ""
      username: ""
      password: ""
      http_method: get
      path: seova
      file_path: ./se.ova
      api_version: 17.2.8

  - name: Upload HSM package to controller
    avi_api_fileservice:
      controller: ""
      username: ""
      password: ""
      http_method: post
      path: hsmpackages?hsmtype=safenet
      file_path: ./safenet.tar
      api_version: 17.2.8

'''


RETURN = '''
obj:
    description: Avi REST resource
    returned: success, changed
    type: dict
'''

import json
import time
import os
from ansible.module_utils.basic import AnsibleModule
from copy import deepcopy
from requests_toolbelt import MultipartEncoder

try:
    from avi.sdk.avi_api import ApiSession, AviCredentials
    from avi.sdk.utils.ansible_utils import (
        avi_obj_cmp, cleanup_absent_fields, avi_common_argument_spec,
        ansible_return)
    from pkg_resources import parse_version
    import avi.sdk
    sdk_version = getattr(avi.sdk, '__version__', None)
    if ((sdk_version is None) or
            (sdk_version and
             (parse_version(sdk_version) < parse_version('17.2.2b3')))):
        # It allows the __version__ to be '' as that value is used in development builds
        raise ImportError
    HAS_AVI = True
except ImportError:
    HAS_AVI = False


def main():
    argument_specs = dict(
        http_method=dict(required=True,
                         choices=['get', 'post']),
        path=dict(type='str', required=True),
        file_path=dict(type='str', required=True),
        params=dict(type='dict'),
        timeout=dict(type='int', default=60)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)

    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk) is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))

    api_creds = AviCredentials()
    api_creds.update_from_ansible_module(module)
    api = ApiSession.get_session(
        api_creds.controller, api_creds.username, password=api_creds.password,
        timeout=api_creds.timeout, tenant=api_creds.tenant,
        tenant_uuid=api_creds.tenant_uuid, token=api_creds.token,
        port=api_creds.port)

    tenant_uuid = api_creds.tenant_uuid
    tenant = api_creds.tenant
    timeout = int(module.params.get('timeout'))
    # path is a required argument
    path = 'fileservice/%s' % module.params.get('path', '')
    params = module.params.get('params', None)
    data = module.params.get('data', None)
    # Get the api_version from module.
    api_version = api_creds.api_version
    if data is not None:
        data = json.loads(data)
    method = module.params['http_method']
    file_path = module.params['file_path']

    if method == 'post':
        if not os.path.exists(file_path):
            return module.fail_json('File not found : %s' % file_path)
        file_name = os.path.basename(file_path)
        uri = 'controller://%s' % module.params.get('path', '').split('?')[0]
        changed = False
        file_uri = 'fileservice?uri=%s' % uri
        rsp = api.post(file_uri, tenant=tenant, tenant_uuid=tenant_uuid,
                       timeout=timeout)
        with open(file_path, "rb") as f:
            f_data = {"file": (file_name, f, "application/octet-stream"),
                      "uri": uri}
            m = MultipartEncoder(fields=f_data)
            headers = {'Content-Type': m.content_type}
            rsp = api.post(path, data=m, headers=headers,
                         verify=False)
            if rsp.status_code > 300:
                return module.fail_json(msg='Fail to upload file: %s' %
                                        rsp.text)
            else:
                return module.exit_json(
                    changed=True, msg="File uploaded successfully")

    elif method == 'get':
        rsp = api.get(path, params=params, stream=True)
        if rsp.status_code > 300:
            return module.fail_json(msg='Fail to download file: %s' % rsp.text)
        with open(file_path, 'wb') as f:
            for chunk in rsp.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return module.exit_json(msg='File downloaded successfully' ,changed=True)


if __name__ == '__main__':
    main()
