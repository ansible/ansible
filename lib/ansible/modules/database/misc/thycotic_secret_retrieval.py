#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: "thycotic_secret_retrieval"

short_description: "Retrieve secrets stored in Thycotic Secret Server"

version_added: "2.5"

requirements:
    - zeep

description:
    - "NOTE: Requires Zeep library. The module interacts with the SOAP API of the instance."
    - "Webservices must be enabled for this work correctly."
    - "This module works by editing a single field value of a secret at a time."
    - "The field value can be a file or text value."

options:
    endpoint:
        description:
            - The endpoint of your secret server instance
        required: true
    username:
        description:
            - Name of the user you wish to authenticate into the instance with
        required: true
    password:
        description:
            - Password of the user you wish to authenticate into the instance with
            - It is recomended to store your password in a file and use a lookup plugin to inject it into your playbook
        required: true
    folder:
        description:
            - The folder you wish to store/retrieve the secret in/from
        required: true
    secret_name:
        description:
            - Name of the secret you wish to interact with
        required: true
    field_name:
        description:
            - Name of the field you wish to edit
        required: true
    dest:
        description:
            - Absolute path on the host machine to the folder that you wish to download the secret file to
            - Required for getting files
        required: false

author:
    - Patrick Thomison (@pthomison)
'''


EXAMPLES = '''
# Retrieve Text From A Field
- name: get text
  thycotic_secret:
    username: 'admin'
    password: 'adm-password'
    endpoint: 'http://endpoint/SecretServer/webservices/sswebservice.asmx'
    secret_name: 'example_ssh_key'
    field_name: 'Private Key'
    folder: 'demo'
  register: priv_key

# Retrieve File Attachement From A Field
- name: get file
  thycotic_secret:
    username: 'admin'
    password: 'adm-password'
    endpoint: 'http://endpoint/SecretServer/webservices/sswebservice.asmx'
    secret_name: 'test_image'
    field_name: 'file'
    dest: '/tmp/'
    folder: 'demo'
'''

RETURN = '''
secret_value:
    description: The secret field value that you requested; Only populated when getting text
    type: str
    returned: success
'''

from ansible.module_utils.basic import AnsibleModule
import os

import_failed = False
try:
    from zeep import Client, helpers
except:
    import_failed = True


def run_module():
    module_args = dict(
        endpoint=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True, no_log=True),
        folder=dict(type='str', required=True),
        secret_name=dict(type='str', required=True),
        field_name=dict(type='str', required=True),
        dest=dict(type='str', required=False)
    )

    result = dict(
        changed=False,
        secret_value="test"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Error checking for imports
    if import_failed:
        module.fail_json(msg="Zeep is a required library", **result)

    # authenticates & retrieves token
    token_args = {'username': module.params['username'], 'password': module.params['password']}
    token_result = make_soap_request(module.params['endpoint'], 'Authenticate', token_args)
    token = token_result['Token']

    # if errors when encountered during authentication
    if token_result['Errors']:
        module.fail_json(msg=str(token_result['Errors']), **result)

    # searches for specified folder
    # should fail if folder does not exist
    folder_result = make_soap_request(module.params['endpoint'], 'SearchFolders', {'token': token, 'folderName': module.params['folder']})

    # if errors when encountered during authentication
    if not folder_result['Folders']:
        module.fail_json(msg="folder does not exist", **result)

    folderId = folder_result['Folders']['Folder'][0]['Id']

    secret = find_secret(module.params['endpoint'], token, module.params['secret_name'], folderId)

    # secret must exist
    if secret is None:
        module.fail_json(msg='Secret Does Not Exist', **result)

    # field name must be present on the secret
    field = field_name_filter(secret, module.params['field_name'])
    if field is None:
        module.fail_json(msg='Field Is Not Present On The Secret', **result)

    if field['IsFile']:
        # Download destination must be present if it is a file
        if not module.params['dest']:
            module.fail_json(msg="Field is a file and no destination was given", **result)

        # Downloading file
        get_file_args = {'token': token, 'secretId': secret['Id'], 'secretItemId': field['Id']}
        get_file_result = make_soap_request(module.params['endpoint'], 'DownloadFileAttachmentByItemId', get_file_args)
        file_bytes = get_file_result["FileAttachment"]
        download_location = os.path.join(module.params['dest'], get_file_result["FileName"])

        # assume nothing changes
        result['changed'] = False

        # if getting a file and the dest does not exist
        if not os.path.exists(download_location):
            result['changed'] = True

        # if getting a file, and the dest already exists, download a temp copy, check to see if the files match
        else:
            with open(download_location, 'rb') as fp:
                curr_file = fp.read()

            # if they do, return nothing changed
            if curr_file == file_bytes:
                result['changed'] = False

            # if they don't & check mode is not enabled, return changed & update the file
            # if they don't & check mode is enabled, return changed, but do not update the file
            else:
                result['changed'] = True

        # Downloading the file to the correct location
        if result['changed'] and not module.check_mode:
            with open(download_location, 'wb') as fp:
                fp.write(file_bytes)

    else:
        # returning secret
        result['secret_value'] = field['Value']
        result['changed'] = False

    module.exit_json(**result)
