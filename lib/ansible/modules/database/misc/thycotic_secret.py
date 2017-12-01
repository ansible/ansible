#!/usr/bin/python

# TODO: Allow for secret files
# TODO: Update to pass all sanity checks
# TODO: Review


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: thycotic_secret

short_description: Allows the retrieval or addition of secrets from a instance of Thycotic Secret Server

version_added: "2.4"

description:
    - "NOTE: Requires Zeep library. The module interacts with the SOAP API of the instance. Webservices must be enabled for this work correctly"

options:
    endpoint:
        description:
            - The endpoint of your secret server instance
        required: true
    name:
        description:
            - Name of the secret you wish to interact with
        required: true
    folder:
        description:
            - The folder you wish to store/retrieve the secret in/from
        required: true
    username:
        description:
            - Name of the user you wish to authenticate into the instance with
        required: true
    password:
        description:
            - Password of the user you wish to authenticate into the instance with; it is recomended to store your password in a file and use a lookup plugin to inject it into your playbook
        required: true
    mode:
        description:
            - Mode of operation of the module
        choices:
            - get
            - put
        required: false
        default: get
    type:
        description:
            - Type of secret template you wish to use
        required: false
    secret_args:
        description:
            - Dictionary of the secrets you wish to store. Keys should be the field name as it is shown in the template and the value should be the coresponding secret
        required: false
    overwrite:
        description:
            - If set, if a secrets value's are different than the secret_args, the secret will be updated
        required: false
        default: false

author:
    - Patrick Thomison (@pthomison)
'''

EXAMPLES = '''
# Retrieve a SSH Key
- name: Retrieve an SSH Key
  thycotic_secret:
    name: 'example_ssh_key'
    folder: 'example_folder'
    mode: 'get'
    username: 'admin'
    password: 'r3dh4t1!'
    endpoint: 'http://127.0.0.1/SecretServer/webservices/sswebservice.asmx'
    register: results

# Add a SSH key
- name: add secret into secret server
  thycotic_secret:
    name: 'example_ssh_key'
    folder: 'example_folder'
    mode: 'put'
    username: 'admin'
    password: 'r3dh4t1!'
    endpoint: 'http://127.0.0.1/SecretServer/webservices/sswebservice.asmx'
    type: 'SSH Key'
    secret_args:
      Public Key: "{{ lookup('file', '~/.ssh/id_rsa.pub') }}"
      Private Key: "{{ lookup('file', '~/.ssh/id_rsa') }}"
      Private Key Passphrase: password
'''

RETURN = '''
secret:
    description: The secret object stored in thycotic secret server
    type: dict
'''

try:
    from ansible.module_utils.basic import AnsibleModule
    from zeep import Client, helpers
except:
    module.fail_json(msg="Zeep is a required library", **result)

def run_module():
    module_args = dict(
        endpoint=dict(type='str', required=True),
        name=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True),
        folder=dict(type='str', required=True),
        mode=dict(type='str', required=False, choices=['get', 'put', 'debug'], default='get'),
        type=dict(type='str', required=False),
        secret_args=dict(type='dict', required=False),
        overwrite=dict(type='bool', required=False, default=False)
    )

    result = dict(
        changed=False,
        secret=dict(),
        debug=dict()
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ["mode", "put", ["type", "secret_args"]]
        ]
    )

    # non production, testing mode
    if module.params['mode'] == 'debug':
        result['debug'] = 'test'
        result['changed'] = False

    else:
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

        # determining if secret exists
        search_args = {'token': token, 'searchTerm': module.params['name'], 'folderId': folderId, 'includeSubFolders': False, 'includeDeleted': False, 'includeRestricted': False}
        search_result = make_soap_request(module.params['endpoint'], 'SearchSecretsByFolder', search_args)

        # Secret exists, request it
        if search_result['SecretSummaries']:
            secret_id = int(search_result['SecretSummaries']['SecretSummary'][0]['SecretId'])
            secret_args = {'token': token, 'secretId': secret_id, 'loadSettingsAndPermissions': False, 'codeResponses': []}
            secret_result = make_soap_request(module.params['endpoint'], 'GetSecret', secret_args)
            secret = secret_result['Secret']
        else:
            secret = None

        # retrieves a secret and returns it
        if module.params['mode'] == 'get':

            # error checking
            if secret is None:
                module.fail_json(msg='Secret Does Not Exist', **result)

            # returning secret
            result['secret'] = secret
            result['changed'] = False

        # ensures the secret is added into the secret server
        elif module.params['mode'] == 'put':

            # assume nothing changes
            result['changed'] = False

            if secret is not None:
                equality_test = check_secret_equality(local_secret=secret, args=module.params['secret_args'])
                # if arguments & secret match, change nothing
                if equality_test:
                    result['changed'] = False
                # if arguments & secret don't match & overwrite is true, the secret will be updated
                elif module.params['overwrite']:
                    result['changed'] = True
                # if arguments & secret don't match & overwrite is false,
                # nothing will change and the module will fail
                else:
                    result['changed'] = False
                    module.fail_json(msg="Secret is present & changed, and overwrite is not set", **result)
            # if secret is not present, it will be uploaded
            else:
                result['changed'] = True

            # if the secret is not present or doesn't match the argmuments,
            if result['changed'] and not module.check_mode:

                # if secret is present, update it
                if secret is not None:
                    updated_secret = inject_args(secret, module.params['secret_args'])
                    make_soap_request(module.params['endpoint'], 'UpdateSecret', {'token': token, 'secret': updated_secret})
                    result['changed'] = True

                # if secret is not present, it should be created
                else:
                    # Get the correct type id
                    get_templates_result = make_soap_request(module.params['endpoint'], 'GetSecretTemplates', {'token': token})
                    templates = get_templates_result["SecretTemplates"]["SecretTemplate"]
                    requested_template = [tpl for tpl in templates if (module.params['type'] == tpl["Name"])][0]
                    template_id = requested_template['Id']

                    # Creating a new secret from the template
                    get_new_secret_args = {'token': token, 'secretTypeId': template_id, 'folderId': folderId}
                    get_new_secret_result = make_soap_request(module.params['endpoint'], 'GetNewSecret', get_new_secret_args)

                    # Adding in the actual secrets
                    new_secret = get_new_secret_result['Secret']
                    new_secret["Name"] = module.params['name']
                    new_secret = inject_args(new_secret, module.params['secret_args'])

                    make_soap_request(module.params['endpoint'], 'AddNewSecret', {'token': token, 'secret': new_secret})
                    result['changed'] = True

        module.exit_json(**result)


def check_secret_equality(local_secret, args):
    for item in local_secret["Items"]["SecretItem"]:
        if item['FieldName'] in args.keys():
            if str(args[item['FieldName']]) != str(item['Value']):
                return False
    return True


# takes in a secret and a dictionary of argument and applies them to the secret
def inject_args(local_secret, args):
    for item in local_secret["Items"]["SecretItem"]:
        if item['FieldName'] in args.keys():
            item["Value"] = args[item['FieldName']]
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
