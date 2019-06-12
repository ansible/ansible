#!/usr/bin/python

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
author: Chaitanya Deshpande (@chaitanyaavi) <chaitanya.deshpande@avinetworks.com>

short_description: Avi API Module for fileservice
description:
    - This module can be used for calling fileservice resources to upload/download files
version_added: 2.9
requirements: [ avisdk, requests_toolbelt ]
options:
    upload:
        description:
            - Allowed upload flag false for download and true for upload.
        required: true
    force_mode:
        description:
            - Allowed force mode for upload forcefully.
        default: true
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
        default: 60
extends_documentation_fragment:
    - avi
'''

EXAMPLES = '''

  - name: Download se image from controller
    avi_api_fileservice:
      controller: ""
      username: ""
      password: ""
      upload: false
      path: seova
      file_path: ./se.ova
      api_version: 17.2.8

  - name: Upload HSM package to controller
    avi_api_fileservice:
      controller: ""
      username: ""
      password: ""
      upload: true
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
import os
from ansible.module_utils.basic import AnsibleModule

try:
    from requests_toolbelt import MultipartEncoder
    HAS_LIB = True
except ImportError:
    HAS_LIB = False

try:
    from ansible.module_utils.network.avi.avi import (
        avi_common_argument_spec, ansible_return, avi_obj_cmp,
        cleanup_absent_fields, HAS_AVI)
    from ansible.module_utils.network.avi.avi_api import (
        ApiSession, AviCredentials)
except ImportError:
    HAS_AVI = False


def upload_file(module, api, file_path, tenant, tenant_uuid, timeout):
    if not os.path.exists(file_path):
        return module.fail_json(msg=('File not found : %s' % file_path))
    file_name = os.path.basename(file_path)
    # Handle special case of upgrade controller using .pkg file which will be uploaded to upgrade_pkgs directory
    if file_name.lower().endswith('.pkg'):
        uri = 'controller://upgrade_pkgs'
        path = 'fileservice/uploads'
    else:
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


def download_file(module, api, file_path, path, params, force_mode):
    # Removing existing file.
    if force_mode and os.path.exists(file_path):
        os.remove(file_path)
    rsp = api.get(path, params=params, stream=True)
    if rsp.status_code > 300:
        return module.fail_json(msg='Fail to download file: %s' % rsp.text)
    with open(file_path, 'wb') as f:
        for chunk in rsp.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return module.exit_json(msg='File downloaded successfully',
                            changed=True)


def main():
    argument_specs = dict(
        force_mode=dict(type='bool', default=True),
        upload=dict(required=True,
                    type='bool'),
        path=dict(type='str', required=True),
        file_path=dict(type='str', required=True),
        params=dict(type='dict'),
        timeout=dict(type='int', default=60)
    )
    argument_specs.update(avi_common_argument_spec())
    module = AnsibleModule(argument_spec=argument_specs)
    if not HAS_AVI:
        return module.fail_json(msg=(
            'Avi python API SDK (avisdk>=17.1) or requests is not installed. '
            'For more details visit https://github.com/avinetworks/sdk.'))
    if not HAS_LIB:
        return module.fail_json(
            msg='avi_api_fileservice, requests_toolbelt is required for this module')

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
    upload = module.params['upload']
    file_path = module.params['file_path']
    force_mode = module.params['force_mode']

    if upload:
        upload_file(module, api, file_path, tenant, tenant_uuid, timeout)

    elif not upload:
        download_file(module, api, file_path, path, params, force_mode)


if __name__ == '__main__':
    main()
