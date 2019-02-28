#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Mikhail Naletov <okgolove@markeloff.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: sentry_project
short_description: Manage Sentry project
description:
    - Manage the state of a project in Sentry.
version_added: "2.8"

options:
  api_token:
    description:
      - API token generated in Sentry. The token has to have an acess for manipulating projects.
    required: true

  organization:
    description:
      - Organization containing a project.
    required: true

  project_name:
    description:
      - Project name you want to work with.
    required: true

  project_slug:
    description:
      - Slug name. Slug name must be uniq (even after project deletion you can't create a project with same slug name).
    required: true

  state:
    description:
      - The state of project.
    required: true
    choices: [ "present", "absent" ]

  team:
    description:
      - A team you are in and which has an access for project manipulating.

  url:
    description:
      - Sentry URL with scheme.
    required: true

author: "Mikhail Naletov (@okgolove)"
'''

EXAMPLES = '''
# Create project "backend" in "example" organization and "senior" team
- sentry_project:
    api_token: 1234567890abcdwxyz
    organization: example
    project_name: backend
    project_slug: backend
    state: present
    team: senior
    url: https://sentry.example.com
'''

RETURN = ''' # '''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native


def main():
    arg_spec = dict(
        api_token=dict(required=True),
        organization=dict(required=True),
        project_name=dict(required=True),
        project_slug=dict(required=True),
        state=dict(required=True, choices=['present', 'absent']),
        team=dict(required=True),
        url=dict(required=True)
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=False)

    api_token = module.params['api_token']
    organization = module.params['organization']
    project_name = module.params['project_name']
    project_slug = module.params['project_slug']
    state = module.params['state']
    team = module.params['team']
    url = module.params['url']

    def is_project_exists(project_name, organization, team, api_token):
        response, info = fetch_url(
            module, "{url}/api/0/teams/{organization}/{team}/projects/".format(
                url=url, organization=organization, team=team),
            headers={"Authorization": "Bearer {0}".format(api_token)},
            method="GET")
        if info["status"] != 200:
            module.fail_json(msg=info["msg"])
        body = json.loads(response.read())
        return bool([x for x in body if x["name"] == project_name])

    if state == 'present':
        if is_project_exists(project_name, organization, team, api_token):
            module.exit_json(changed=False)
        else:
            response, info = fetch_url(
                module, "{url}/api/0/teams/{organization}/{team}/projects/".format(
                    url=url, organization=organization, team=team
                ),
                headers={
                    "Authorization": "Bearer {0}".format(api_token),
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "name": project_name,
                    "slug": project_slug
                }),
                method="POST")
            if info["status"] != 201:
                module.fail_json(msg=info["msg"])
            module.exit_json(changed=True)

    if state == 'absent':
        if is_project_exists(project_name, organization, team, api_token):
            response, info = fetch_url(
                module, "{url}/api/0/projects/{organization}/{project_slug}/".format(
                    url=url, organization=organization,
                    project_slug=project_slug),
                headers={
                    "Authorization": "Bearer {0}".format(api_token),
                    "Content-Type": "application/json"
                },
                method="DELETE")
            if info["status"] != 204:
                module.fail_json(msg=info["msg"])
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
