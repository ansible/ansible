#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Evgeniy Krysanov <evgeniy.krysanov@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = r'''
---
module: bitbucket_pipeline_key_pair
short_description: Manages Bitbucket pipeline SSH key pair
description:
  - Manages Bitbucket pipeline SSH key pair.
version_added: "2.8"
author:
  - Evgeniy Krysanov (@catcombo)
options:
  client_id:
    description:
      - OAuth consumer key.
      - If not set the environment variable C(BITBUCKET_CLIENT_ID) will be used.
    type: str
  client_secret:
    description:
      - OAuth consumer secret.
      - If not set the environment variable C(BITBUCKET_CLIENT_SECRET) will be used.
    type: str
  repository:
    description:
      - The repository name.
    type: str
    required: true
  username:
    description:
      - The repository owner.
    type: str
    required: true
  public_key:
    description:
      - The public key.
    type: str
  private_key:
    description:
      - The private key.
    type: str
  state:
    description:
      - Indicates desired state of the key pair.
    type: str
    required: true
    choices: [ absent, present ]
notes:
  - Bitbucket OAuth consumer key and secret can be obtained from Bitbucket profile -> Settings -> Access Management -> OAuth.
  - Check mode is supported.
'''

EXAMPLES = r'''
- name: Create or update SSH key pair
  bitbucket_pipeline_key_pair:
    repository: 'bitbucket-repo'
    username: bitbucket_username
    public_key: '{{lookup("file", "bitbucket.pub") }}'
    private_key: '{{lookup("file", "bitbucket") }}'
    state: present

- name: Remove SSH key pair
  bitbucket_pipeline_key_pair:
    repository: bitbucket-repo
    username: bitbucket_username
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.source_control.bitbucket import BitbucketHelper

error_messages = {
    'invalid_params': 'Account, repository or SSH key pair was not found',
    'required_keys': '`public_key` and `private_key` are required when the `state` is `present`',
}

BITBUCKET_API_ENDPOINTS = {
    'ssh-key-pair': '%s/2.0/repositories/{username}/{repo_slug}/pipelines_config/ssh/key_pair' % BitbucketHelper.BITBUCKET_API_URL,
}


def get_existing_ssh_key_pair(module, bitbucket):
    """
    Retrieves an existing ssh key pair from repository
    specified in module param `repository`

    :param module: instance of the :class:`AnsibleModule`
    :param bitbucket: instance of the :class:`BitbucketHelper`
    :return: existing key pair or None if not found
    :rtype: dict or None

    Return example::

        {
            "public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...2E8HAeT",
            "type": "pipeline_ssh_key_pair"
        }
    """
    api_url = BITBUCKET_API_ENDPOINTS['ssh-key-pair'].format(
        username=module.params['username'],
        repo_slug=module.params['repository'],
    )

    info, content = bitbucket.request(
        api_url=api_url,
        method='GET',
    )

    if info['status'] == 404:
        # Account, repository or SSH key pair was not found.
        return None

    return content


def update_ssh_key_pair(module, bitbucket):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['ssh-key-pair'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        ),
        method='PUT',
        data={
            'private_key': module.params['private_key'],
            'public_key': module.params['public_key'],
        },
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_params'])

    if info['status'] != 200:
        module.fail_json(msg='Failed to create or update pipeline ssh key pair : {0}'.format(info))


def delete_ssh_key_pair(module, bitbucket):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['ssh-key-pair'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        ),
        method='DELETE',
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_params'])

    if info['status'] != 204:
        module.fail_json(msg='Failed to delete pipeline ssh key pair: {0}'.format(info))


def main():
    argument_spec = BitbucketHelper.bitbucket_argument_spec()
    argument_spec.update(
        repository=dict(type='str', required=True),
        username=dict(type='str', required=True),
        public_key=dict(type='str'),
        private_key=dict(type='str', no_log=True),
        state=dict(type='str', choices=['present', 'absent'], required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    bitbucket = BitbucketHelper(module)

    state = module.params['state']
    public_key = module.params['public_key']
    private_key = module.params['private_key']

    # Check parameters
    if ((public_key is None) or (private_key is None)) and (state == 'present'):
        module.fail_json(msg=error_messages['required_keys'])

    # Retrieve access token for authorized API requests
    bitbucket.fetch_access_token()

    # Retrieve existing ssh key
    key_pair = get_existing_ssh_key_pair(module, bitbucket)
    changed = False

    # Create or update key pair
    if (not key_pair or (key_pair.get('public_key') != public_key)) and (state == 'present'):
        if not module.check_mode:
            update_ssh_key_pair(module, bitbucket)
        changed = True

    # Delete key pair
    elif key_pair and (state == 'absent'):
        if not module.check_mode:
            delete_ssh_key_pair(module, bitbucket)
        changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
