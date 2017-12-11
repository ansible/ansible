#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# TODO: Write quick & dirty test playbook
# TODO: Review & Submit PR

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: "thycotic_secret"

short_description: "Add or retrieve secrets from of Thycotic Secret Server"

version_added: "2.4"

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
    type:
        description:
            - Type of secret template you wish to use
            - Required for putting secrets (file or text)
        required: false
    src:
        description:
            - Absolute path on the host machine to the file that you wish to upload and attach to the secret
            - Required for putting files
        required: false
    dest:
        description:
            - Absolute path on the host machine to the folder that you wish to download the secret file to
            - Required for getting files
        required: false
    field_value:
        description:
            - Text value that you wish to place in the secret field
            - Required for putting text
        required: false
    mode:
        description:
            - Mode of operation of the module
        choices:
            - get
            - put
        required: true

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
    mode: 'get'
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
    mode: 'get'

# Place Text In A Field
- name: put text
  thycotic_secret:
    username: 'admin'
    password: 'adm-password'
    endpoint: 'http://endpoint/SecretServer/webservices/sswebservice.asmx'
    secret_name: 'test_password'
    type: 'Password'
    field_name: 'Password'
    field_value: 'pa44w0rd'
    folder: 'demo'
    mode: 'put'

# Attach A File To A Field
- name: put file
  thycotic_secret:
    username: 'admin'
    password: 'adm-password'
    endpoint: 'http://endpoint/SecretServer/webservices/sswebservice.asmx'
    secret_name: 'test_file'
    type: 'generic_file'
    field_name: 'file'
    src: '/tmp/test_file.jpg'
    folder: 'demo'
    mode: 'put'
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
        password=dict(type='str', required=True),
        folder=dict(type='str', required=True),
        secret_name=dict(type='str', required=True),
        field_name=dict(type='str', required=True),
        mode=dict(type='str', required=True, choices=['get', 'put', 'debug']),
        src=dict(type='str', required=False),
        dest=dict(type='str', required=False),
        type=dict(type='str', required=False),
        field_value=dict(type='str', required=False),
    )

    result = dict(
        changed=False,
        secret_value="test"
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ["mode", "put", ["type"]]
        ]
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

    # non production, testing mode
    if module.params['mode'] == 'debug':
        result['changed'] = False

    # retrieves a secret and returns it
    elif module.params['mode'] == 'get':
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

    # ensures the secret is added into the secret server
    elif module.params['mode'] == 'put':
            # Get the correct template
            get_templates_result = make_soap_request(module.params['endpoint'], 'GetSecretTemplates', {'token': token})
            template_list = get_templates_result["SecretTemplates"]["SecretTemplate"]
            template_test = [tpl for tpl in template_list if (module.params['type'] == tpl["Name"])]
            # Ensuring template is Present
            if len(template_test) == 0:
                module.fail_json(msg='Secret Type Is Not Present On This Server', **result)
            template = template_test[0]

            template_fields = template['Fields']['SecretField']
            template_field_name_test = [x for x in template_fields if x['DisplayName'] == module.params['field_name']]
            # Ensuring the field name is on the template
            if len(template_field_name_test) == 0:
                module.fail_json(msg='Field Is Not Present On The Secret Type', **result)
            template_field = template_field_name_test[0]

            # CHANGE VALIDATION

            # assume nothing changes
            result['changed'] = False

            # Secret is present
            if secret is not None:
                field = field_name_filter(secret, module.params['field_name'])

                if template_field['IsFile']:
                    # error check for 'src'
                    if not module.params['src']:
                        module.fail_json(msg="Field is a file and no src was given", **result)

                    get_file_args = {'token': token, 'secretId': secret['Id'], 'secretItemId': field['Id']}
                    get_file_result = make_soap_request(module.params['endpoint'], 'DownloadFileAttachmentByItemId', get_file_args)
                    file_bytes = get_file_result["FileAttachment"]

                    with open(module.params['src'], "rb") as fp:
                        src_bytes = fp.read()
                    equality_test = file_bytes == src_bytes

                else:
                    equality_test = field['Value'] == module.params['field_value']

                # if arguments & secret match, change nothing
                if equality_test:
                    result['changed'] = False
                # if arguments & secret don't match, the secret will be updated
                else:
                    result['changed'] = True

            # if secret is not present
            # it will be uploaded
            else:
                result['changed'] = True

            # CHANGE IMPLEMENTATION

            # if the secret is not present or doesn't match the argmuments,
            if result['changed'] and not module.check_mode:

                # Secret does not exist, must be created
                if secret is None:
                    # Creating a new secret from the template
                    get_new_secret_args = {'token': token, 'secretTypeId': template['Id'], 'folderId': folderId}
                    get_new_secret_result = make_soap_request(module.params['endpoint'], 'GetNewSecret', get_new_secret_args)

                    new_secret = get_new_secret_result['Secret']
                    new_secret["Name"] = module.params['secret_name']

                    if not template_field['IsFile']:
                        new_secret = inject_arg(new_secret, module.params['field_name'], module.params['field_value'])

                    # Tell the server to add the new secret
                    make_soap_request(module.params['endpoint'], 'AddNewSecret', {'token': token, 'secret': new_secret})

                    if template_field['IsFile']:
                        # re-requesting secret to get updated ID
                        new_secret = find_secret(module.params['endpoint'], token, module.params['secret_name'], folderId)
                        new_secret_field = field_name_filter(new_secret, module.params['field_name'])
                        upload_file(module.params['endpoint'], token, new_secret['Id'], new_secret_field['Id'], module.params['src'])

                # if secret is present, update it
                else:
                    if template_field['IsFile']:
                        field = field_name_filter(secret, module.params['field_name'])
                        upload_file(module.params['endpoint'], token, secret['Id'], field['Id'], module.params['src'])

                    else:
                        updated_secret = inject_arg(secret, module.params['field_name'], module.params['field_value'])
                        make_soap_request(module.params['endpoint'], 'UpdateSecret', {'token': token, 'secret': updated_secret})

    module.exit_json(**result)


def upload_file(endpoint, token, secretId, secretItemId, src):
    filename = os.path.basename(src)
    with open(src, 'rb') as fp:
        data = fp.read()
        upload_file_args = {'token': str(token),
                            'secretId': int(secretId),
                            'secretItemId': int(secretItemId),
                            'fileData': bytes(data),
                            'fileName': str(filename)}
    # Tell the server to upload file
    make_soap_request(endpoint, 'UploadFileAttachmentByItemId', upload_file_args)


def find_secret(endpoint, token, secret_name, folder_id):
    # determining if secret exists
    search_args = {'token': token,
                   'searchTerm': secret_name,
                   'folderId': folder_id,
                   'includeSubFolders': False,
                   'includeDeleted': False,
                   'includeRestricted': False}
    search_result = make_soap_request(endpoint, 'SearchSecretsByFolder', search_args)

    # Secret exists, request it
    if search_result['SecretSummaries']:
        secret_id = int(search_result['SecretSummaries']['SecretSummary'][0]['SecretId'])
        secret_args = {'token': token,
                       'secretId': secret_id,
                       'loadSettingsAndPermissions': False,
                       'codeResponses': []}
        secret_result = make_soap_request(endpoint, 'GetSecret', secret_args)
        secret = secret_result['Secret']
    else:
        secret = None
    return secret


def field_name_filter(secret, field_name):
    arr = [x for x in secret['Items']['SecretItem'] if x['FieldDisplayName'] == field_name]
    if len(arr) != 0:
        return arr[0]


# takes in a secret and a dictionary of argument and applies them to the secret
def inject_arg(local_secret, field, val):
    for item in local_secret["Items"]["SecretItem"]:
        if item['FieldDisplayName'] == field:
            item["Value"] = val
    return local_secret


# makes request against the specified service at the endpoint with the given argument_list
# return dictionary of results
def make_soap_request(endpoint, serviceName, argument_list):
    client = Client(endpoint + '?WSDL')
    response = getattr(client.service, serviceName)(**argument_list)
    if response:
        return dict(helpers.serialize_object(response))


def main():
    run_module()


if __name__ == '__main__':
    main()
