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
      - API token generated in Sentry. The token sufficient access to manipulate projects.
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
      - Slug name. Slug name must be unique (even after project deletion you can't create a project with same slug name).
    required: true

  state:
    description:
      - The state of project.
    required: true
    choices: [ "present", "absent" ]

  team:
    description:
      - The name of the team to create a new project for.

  url:
    description:
      - Sentry URL.
    required: false
    default: sentry.io

notes: "Module supports check_mode, but it can't provide 100 percent gurantee what specified slug hasn't been used before."
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
    url: sentry.example.com
'''

RETURN = ''' # '''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native
from ansible.module_utils.six.moves.urllib.parse import urlparse


def main():
    arg_spec = dict(
        api_token=dict(required=True),
        organization=dict(required=True),
        project_name=dict(required=True),
        project_slug=dict(required=True),
        state=dict(required=True, choices=['present', 'absent']),
        team=dict(required=True),
        url=dict(default="sentry.io")
    )

    module = AnsibleModule(argument_spec=arg_spec, supports_check_mode=True)

    api_token = module.params['api_token']
    organization = module.params['organization']
    project_name = module.params['project_name']
    project_slug = module.params['project_slug']
    state = module.params['state']
    team = module.params['team']
    url = urlparse(module.params['url'])

    if not url.scheme:
        url = "https://{0}".format(url.path)

    def is_project_exists(project_name, organization, team, api_token):
        response, info = fetch_url(
            module, "{url}/api/0/teams/{organization}/{team}/projects/".format(
                url=url, organization=organization, team=team),
            headers={"Authorization": "Bearer {0}".format(api_token)},
            method="GET")
        if info["status"] != 200:
            module.fail_json(msg="Unable to obtain a project list, response status: {0}, message: {1}".format(
                info["status"], info["msg"]))
        body = json.loads(response.read())
        return bool([x for x in body if x["name"] == project_name])

    if state == 'present':
        if is_project_exists(project_name, organization, team, api_token):
            module.exit_json(changed=False)
        if not module.check_mode:
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
                module.fail_json(msg="Unable to create the project, response status: {0}, message: {1}".format(
                    info["status"], info["msg"]))
        module.exit_json(changed=True)

    if state == 'absent':
        if is_project_exists(project_name, organization, team, api_token):
            if not module.check_mode:
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
                    module.fail_json(msg="Unable to delete the project, response status: {0}, message: {1}".format(
                        info["status"], info["msg"]))
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
