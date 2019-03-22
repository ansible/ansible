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
module: bitbucket_pipeline_variable
short_description: Manages Bitbucket pipeline variables
description:
  - Manages Bitbucket pipeline variables.
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
  name:
    description:
      - The pipeline variable name.
    type: str
    required: true
  value:
    description:
      - The pipeline variable value.
    type: str
  secured:
    description:
      - Whether to encrypt the variable value.
    type: bool
    default: no
  state:
    description:
      - Indicates desired state of the variable.
    type: str
    required: true
    choices: [ absent, present ]
notes:
  - Bitbucket OAuth consumer key and secret can be obtained from Bitbucket profile -> Settings -> Access Management -> OAuth.
  - Check mode is supported.
  - For secured values return parameter C(changed) is always C(True).
'''

EXAMPLES = r'''
- name: Create or update pipeline variables from the list
  bitbucket_pipeline_variable:
    repository: 'bitbucket-repo'
    username: bitbucket_username
    name: '{{ item.name }}'
    value: '{{ item.value }}'
    secured: '{{ item.secured }}'
    state: present
  with_items:
    - { name: AWS_ACCESS_KEY, value: ABCD1234 }
    - { name: AWS_SECRET, value: qwe789poi123vbn0, secured: True }

- name: Remove pipeline variable
  bitbucket_pipeline_variable:
    repository: bitbucket-repo
    username: bitbucket_username
    name: AWS_ACCESS_KEY
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.source_control.bitbucket import BitbucketHelper

error_messages = {
    'required_value': '`value` is required when the `state` is `present`',
}

BITBUCKET_API_ENDPOINTS = {
    'pipeline-variable-list': '%s/2.0/repositories/{username}/{repo_slug}/pipelines_config/variables/' % BitbucketHelper.BITBUCKET_API_URL,
    'pipeline-variable-detail': '%s/2.0/repositories/{username}/{repo_slug}/pipelines_config/variables/{variable_uuid}' % BitbucketHelper.BITBUCKET_API_URL,
}


def get_existing_pipeline_variable(module, bitbucket):
    """
    Search for a pipeline variable

    :param module: instance of the :class:`AnsibleModule`
    :param bitbucket: instance of the :class:`BitbucketHelper`
    :return: existing variable or None if not found
    :rtype: dict or None

    Return example::

        {
            'name': 'AWS_ACCESS_OBKEY_ID',
            'value': 'x7HU80-a2',
            'type': 'pipeline_variable',
            'secured': False,
            'uuid': '{9ddb0507-439a-495a-99f3-5464f15128127}'
        }

    The `value` key in dict is absent in case of secured variable.
    """
    content = {
        'next': BITBUCKET_API_ENDPOINTS['pipeline-variable-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        )
    }

    # Look through the all response pages in search of variable we need
    while 'next' in content:
        info, content = bitbucket.request(
            api_url=content['next'],
            method='GET',
        )

        if info['status'] == 404:
            module.fail_json(msg='Invalid `repository` or `username`.')

        if info['status'] != 200:
            module.fail_json(msg='Failed to retrieve the list of pipeline variables: {0}'.format(info))

        var = next(filter(lambda v: v['key'] == module.params['name'], content['values']), None)

        if var is not None:
            var['name'] = var.pop('key')
            return var

    return None


def create_pipeline_variable(module, bitbucket):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['pipeline-variable-list'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
        ),
        method='POST',
        data={
            'key': module.params['name'],
            'value': module.params['value'],
            'secured': module.params['secured'],
        },
    )

    if info['status'] != 201:
        module.fail_json(msg='Failed to create pipeline variable `{name}`: {info}'.format(
            name=module.params['name'],
            info=info,
        ))


def update_pipeline_variable(module, bitbucket, variable_uuid):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['pipeline-variable-detail'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
            variable_uuid=variable_uuid,
        ),
        method='PUT',
        data={
            'value': module.params['value'],
            'secured': module.params['secured'],
        },
    )

    if info['status'] != 200:
        module.fail_json(msg='Failed to update pipeline variable `{name}`: {info}'.format(
            name=module.params['name'],
            info=info,
        ))


def delete_pipeline_variable(module, bitbucket, variable_uuid):
    info, content = bitbucket.request(
        api_url=BITBUCKET_API_ENDPOINTS['pipeline-variable-detail'].format(
            username=module.params['username'],
            repo_slug=module.params['repository'],
            variable_uuid=variable_uuid,
        ),
        method='DELETE',
    )

    if info['status'] != 204:
        module.fail_json(msg='Failed to delete pipeline variable `{name}`: {info}'.format(
            name=module.params['name'],
            info=info,
        ))


def main():
    argument_spec = BitbucketHelper.bitbucket_argument_spec()
    argument_spec.update(
        repository=dict(type='str', required=True),
        username=dict(type='str', required=True),
        name=dict(type='str', required=True),
        value=dict(type='str'),
        secured=dict(type='bool', default=False),
        state=dict(type='str', choices=['present', 'absent'], required=True),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    bitbucket = BitbucketHelper(module)

    value = module.params['value']
    state = module.params['state']
    secured = module.params['secured']

    # Check parameters
    if (value is None) and (state == 'present'):
        module.fail_json(msg=error_messages['required_value'])

    # Retrieve access token for authorized API requests
    bitbucket.fetch_access_token()

    # Retrieve existing pipeline variable (if any)
    existing_variable = get_existing_pipeline_variable(module, bitbucket)
    changed = False

    # Create new variable in case it doesn't exists
    if not existing_variable and (state == 'present'):
        if not module.check_mode:
            create_pipeline_variable(module, bitbucket)
        changed = True

    # Update variable if it is secured or the old value does not match the new one
    elif existing_variable and (state == 'present'):
        if (existing_variable['secured'] != secured) or (existing_variable.get('value') != value):
            if not module.check_mode:
                update_pipeline_variable(module, bitbucket, existing_variable['uuid'])
            changed = True

    # Delete variable
    elif existing_variable and (state == 'absent'):
        if not module.check_mode:
            delete_pipeline_variable(module, bitbucket, existing_variable['uuid'])
        changed = True

    module.exit_json(changed=changed)


if __name__ == '__main__':
    main()
