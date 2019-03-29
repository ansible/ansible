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
module: bitbucket_access_key
short_description: Manages Bitbucket repository access keys
description:
  - Manages Bitbucket repository access keys (also called deploy keys).
version_added: "2.8"
author:
  - Evgeniy Krysanov (@catcombo)
options:
  client_id:
    description:
      - The OAuth consumer key.
      - If not set the environment variable C(BITBUCKET_CLIENT_ID) will be used.
    type: str
  client_secret:
    description:
      - The OAuth consumer secret.
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
  key:
    description:
      - The SSH public key.
    type: str
  label:
    description:
      - The key label.
    type: str
    required: true
  state:
    description:
      - Indicates desired state of the access key.
    type: str
    required: true
    choices: [ absent, present ]
notes:
  - Bitbucket OAuth consumer key and secret can be obtained from Bitbucket profile -> Settings -> Access Management -> OAuth.
  - Bitbucket OAuth consumer should have permissions to read and administrate account repositories.
  - Check mode is supported.
'''

EXAMPLES = r'''
- name: Create access key
  bitbucket_access_key:
    repository: 'bitbucket-repo'
    username: bitbucket_username
    key: '{{lookup("file", "bitbucket.pub") }}'
    label: 'Bitbucket'
    state: present

- name: Delete access key
  bitbucket_access_key:
    repository: bitbucket-repo
    username: bitbucket_username
    label: Bitbucket
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.source_control.bitbucket import BitbucketHelper

error_messages = {
    'required_key': '`key` is required when the `state` is `present`',
    'required_permission': 'OAuth consumer `client_id` should have permissions to read and administrate the repository',
    'invalid_username_or_repo': 'Invalid `repository` or `username`',
    'invalid_key': 'Invalid SSH key or key is already in use',
}

BITBUCKET_API_ENDPOINTS = {
    'deploy-key-list': '%s/2.0/repositories/{username}/{repo_slug}/deploy-keys/' % BitbucketHelper.BITBUCKET_API_URL,
    'deploy-key-detail': '%s/2.0/repositories/{username}/{repo_slug}/deploy-keys/{key_id}' % BitbucketHelper.BITBUCKET_API_URL,
}


def get_existing_deploy_key(module, bitbucket):
    """
    Search for an existing deploy key on Bitbucket
    with the label specified in module param `label`

    :param module: instance of the :class:`AnsibleModule`
    :param bitbucket: instance of the :class:`BitbucketHelper`
    :return: existing deploy key or None if not found
    :rtype: dict or None

    Return example::

        {
            "id": 123,
            "label": "mykey",
            "created_on": "2019-03-23T10:15:21.517377+00:00",
            "key": "ssh-rsa AAAAB3NzaC1yc2EAAAADA...AdkTg7HGqL3rlaDrEcWfL7Lu6TnhBdq5",
            "type": "deploy_key",
            "comment": "",
            "last_used": None,
            "repository": {
                "links": {
                    "self": {
                        "href": "https://api.bitbucket.org/2.0/repositories/mleu/test"
                    },
                    "html": {
                        "href": "https://bitbucket.org/mleu/test"
                    },
                    "avatar": {
                        "href": "..."
                    }
                },
                "type": "repository",
                "name": "test",
                "full_name": "mleu/test",
                "uuid": "{85d08b4e-571d-44e9-a507-fa476535aa98}"
            },
            "links": {
                "self": {
                    "href": "https://api.bitbucket.org/2.0/repositories/mleu/test/deploy-keys/123"
                }
            },
        }
    """
    content = {
        'next': BITBUCKET_API_ENDPOINTS['deploy-key-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        )
    }

    # Look through the all response pages in search of deploy key we need
    while 'next' in content:
        info, content = bitbucket.request(
            api_url=content['next'],
            method='GET',
        )

        if info['status'] == 404:
            module.fail_json(msg=error_messages['invalid_username_or_repo'])

        if info['status'] == 403:
            module.fail_json(msg=error_messages['required_permission'])

        if info['status'] != 200:
            module.fail_json(msg='Failed to retrieve the list of deploy keys: {0}'.format(info))

        res = next(filter(lambda v: v['label'] == module.params['label'], content['values']), None)

        if res is not None:
            return res

    return None


def create_deploy_key(module, bitbucket):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['deploy-key-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        ),
        method='POST',
        data={
            'key': module.params['key'],
            'label': module.params['label'],
        },
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_username_or_repo'])

    if info['status'] == 403:
        module.fail_json(msg=error_messages['required_permission'])

    if info['status'] == 400:
        module.fail_json(msg=error_messages['invalid_key'])

    if info['status'] != 200:
        module.fail_json(msg='Failed to create deploy key `{label}`: {info}'.format(
            label=module.params['label'],
            info=info,
        ))


def delete_deploy_key(module, bitbucket, key_id):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['deploy-key-detail'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
            key_id=key_id,
        ),
        method='DELETE',
    )

    if info['status'] == 404:
        module.fail_json(msg=error_messages['invalid_username_or_repo'])

    if info['status'] == 403:
        module.fail_json(msg=error_messages['required_permission'])

    if info['status'] != 204:
        module.fail_json(msg='Failed to delete deploy key `{label}`: {info}'.format(
            label=module.params['label'],
            info=info,
        ))


def main():
    argument_spec = BitbucketHelper.bitbucket_argument_spec()
    argument_spec.update(
        repository=dict(type='str', required=True),
        username=dict(type='str', required=True),
        key=dict(type='str'),
        label=dict(type='str', required=True),
        state=dict(type='str', choices=['present', 'absent'], required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    bitbucket = BitbucketHelper(module)

    key = module.params['key']
    state = module.params['state']

    # Check parameters
    if (key is None) and (state == 'present'):
        module.fail_json(msg=error_messages['required_key'])

    # Retrieve access token for authorized API requests
    bitbucket.fetch_access_token()

    # Retrieve existing deploy key (if any)
    existing_deploy_key = get_existing_deploy_key(module, bitbucket)
    changed = False

    # Create new deploy key in case it doesn't exists
    if not existing_deploy_key and (state == 'present'):
        if not module.check_mode:
            create_deploy_key(module, bitbucket)
        changed = True

    # Update deploy key if the old value does not match the new one
    elif existing_deploy_key and (state == 'present'):
        if not key.startswith(existing_deploy_key.get('key')):
            if not module.check_mode:
                # Bitbucket doesn't support update key for the same label,
                # so we need to delete the old one first
                delete_deploy_key(module, bitbucket, existing_deploy_key['id'])
                create_deploy_key(module, bitbucket)
            changed = True

    # Delete deploy key
    elif existing_deploy_key and (state == 'absent'):
        if not module.check_mode:
            delete_deploy_key(module, bitbucket, existing_deploy_key['id'])
        changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
