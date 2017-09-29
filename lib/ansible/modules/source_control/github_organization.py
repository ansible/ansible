#!/usr/bin/python
#
# Copyright (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
module: github_organization
short_description: Create/Rename a GitHub organization.
description:
    - Create or Rename a GitHub organization.
version_added: "2.5"
options:
  state:
    description:
      -  Whether to create or rename an organization
    choices: ['present', 'rename']
    default: 'present'
  name:
    description:
      - The name of the organization to create or rename
    required: True
  owner:
    description:
      - The owner of the organization that is being created.
        The owner is required when I(state=present)
  rename_to:
    description:
      - The new name of the organization when renaming.
        Required when I(state=rename).
  base_url:
    description:
      - The base URL for the GitHub Enterprise instance being connected to.
        The URL can either be the URL to the web interface (upon which the /api/v3 path will be appended)
        or full URL to the API endpoint.
        e.g. https://github.domain.com or https://github.domain.com/api/v3
    required: True
  token:
    description:
      - The access token for the I(token_user)
    required: True
  token_user:
    description:
      - The username of the user for the I(token).
        The user must have the necessary privileges to be able to create organizations
        in the GitHub Enterprise instance.
    required: True
  validate_certs:
    description:
      - Whether or not to validate the certificate returned from the GitHub Enterprise
        instance. This is useful when using a self signed certificate.
    type: bool
    default: True
author:
  - "Peter Murray (@peter-murray)"
'''

RETURN = '''
name:
  description: The name of the organization
  returned: always
  type: string
  sample: my-organization
id:
  description: The id of the organization inside GitHub Enterprise
  returned: always
  type: int
  sample: 1
created_at:
  description: The timestamp of when the organization was created
  returned: always
  type: str
  sample: '2017-06-25T12:20:25Z'
updated_at:
  description: The timestamp of the last update to the organization
  returned: always
  type: str
  sample: '2017-06-25T12:20:25Z'
collaborators:
  description: The number of collaborators in the organization
  returned: always
  type: int
  sample: 10
public_repo_count:
  description: The count of public repositories in the organization
  returned: always
  type: int
  sample: 0
private_repo_count:
  description: The count of private repositories in the organization
  returned: always
  type: int
  sample: 1
default_repo_permission:
  description: The default permission for repositories in the organization
  returned: always
  type: string
  sample: read
'''

EXAMPLES = '''
- name: Create an Organization
  github_organization:
    state: present
    base_url: https://github-enterprise.domain.com
    token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
    token_user: token-username
    name: my-organization
    owner: a-user

- name: Rename an organization
  github_organization:
      state: rename
      base_url: https://github-enterprise.domain.com
      token: 'xxxxxxxxxxxxxxxxxxxxxxxxxxx'
      token_user: token-username
      name: my-organization
      rename_to: my-renamed-organization
'''

import base64
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.basic import AnsibleModule


def _build_api_url(base_url, path):
    url = base_url

    if url.endswith('/'):
        if path.startswith('/'):
            url += path[1:]
        else:
            url += path
    else:
        if path.startswith('/'):
            url += path
        else:
            url += '/' + path

    return url


def _get_auth_header(user, token):
    auth = base64.encodestring(('%s:%s' % (user, token)).encode()).decode().replace('\n', '')
    return 'Basic %s' % auth


def _get_organization(module, base_url, auth_header, name):
    path = "orgs/%s" % (name)
    url = _build_api_url(base_url, path)
    headers = {'Authorization': auth_header}

    r, info = fetch_url(module, url, method="GET", headers=headers)
    if info['status'] == 200:
        return module.from_json(r.read())
    else:
        return None


def _get_base_url(module):
    url = module.params['base_url']

    if not url.endswith('api/v3'):
        url = _build_api_url(url, 'api/v3')

    return url


def _merge_organization_result(res, org):
    res.update({
        'name': org['name'],
        'id': org['id'],
        'created_at': org['created_at'],
        'updated_at': org['updated_at'],
        'collaborators': org['collaborators'],
        'public_repo_count': org['public_repos'],
        'private_repo_count': org['total_private_repos'],
        'default_repo_permission': org['default_repository_permission']
    })
    return res


def create_organization(module, auth_header):
    result = {'changed': False}

    organization_name = module.params['name']
    base_url = _get_base_url(module)

    existing_org = _get_organization(module, base_url, auth_header, organization_name)

    if existing_org is None:
        url = _build_api_url(base_url, 'admin/organizations')
        headers = {'Authorization': auth_header}
        data = {
            "login": organization_name,
            # "profile_name": organization_name,
            "admin": module.params['owner']
        }

        r, info = fetch_url(module,
                            url,
                            data=module.jsonify(data),
                            method="POST",
                            headers=headers)
        if info['status'] == 201:
            org = _get_organization(module, base_url, auth_header, organization_name)
            result.update({'changed': True})
            _merge_organization_result(result, org)
        else:
            try:
                failure = module.from_json(info['body'])
                error_message = failure['message']
            except ValueError:
                error_message = info['body']

            module.fail_json(msg='Failed to create organization: {0}'.format(error_message))

    else:
        _merge_organization_result(result, existing_org)

    return result


def rename_organization(module, auth_header):
    result = {'changed': False}

    organization_name = module.params['name']
    new_name = module.params['rename_to']

    if new_name is None:
        module.fail_json(msg="A name to rename the organization to must be provided")

    base_url = _get_base_url(module)
    data = {'login': new_name}

    existing_org = _get_organization(module, base_url, auth_header, organization_name)
    target_org = _get_organization(module, base_url, auth_header, new_name)

    if existing_org is not None:
        if target_org is None:
            url = _build_api_url(base_url, 'admin/organizations/{0}'.format(organization_name))
            headers = {'Authorization': auth_header}

            r, info = fetch_url(module,
                                url,
                                data=module.jsonify(data),
                                method="PATCH",
                                headers=headers)
            if info['status'] == 202:
                # This action is added to a queue, so if successful, report back the change
                result.update({'changed': True})
                _merge_organization_result(result, existing_org)
                result.update({'name': new_name})
            else:
                failure = module.from_json(info['body'])
                module.fail_json(msg='Failed to rename organization: {0}'.format(failure['message']))
        else:
            module.fail_json(msg="An organization with the target name already exists, '{0}'".format(new_name))

    return result


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            owner=dict(required=False),
            rename_to=dict(required=False),
            base_url=dict(required=True),
            token=dict(no_log=True, required=True),
            token_user=dict(required=True),
            validate_certs=dict(type='bool', default=True),
            state=dict(choices=['present', 'rename'], default='present')
        ),
        supports_check_mode=False,
    )

    user = module.params['token_user']
    token = module.params['token']
    state = module.params['state']
    auth_header = _get_auth_header(user, token)

    if state == 'present':
        result = create_organization(module, auth_header)
    elif state == 'rename':
        result = rename_organization(module, auth_header)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
