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
    type: str
    required: true

  organization:
    aliases:
      - org
    description:
      - Organization containing a project.
    type: str
    required: true

  project_name:
    description:
      - Project name you want to work with.
    type: str
    required: true

  project_slug:
    description:
      - Slug name. Slug name must be unique (even after project deletion you can't create a project with same slug name).
    type: str
    required: true

  state:
    description:
      - The state of project.
    type: str
    required: true
    choices: [ "absent", "present" ]

  team:
    description:
      - The name of the team to create a new project for.
    type: str
    required: true

  url:
    description:
      - Sentry URL.
    type: str
    required: false
    default: sentry.io

notes:
  - Module supports check_mode, but it can't provide 100 percent guarantee that the specified slug hasn't been used before.
author:
  - "Mikhail Naletov (@okgolove)"
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

- sentry_project:
    api_token: 1234567890abcdwxyz
    organization: example
    project_name: backend
    project_slug: backend
    state: absent
    team: senior
    url: sentry.example.com
'''

RETURN = ''' # '''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.six.moves.urllib.parse import urlparse


def main():
    arg_spec = dict(
        api_token=dict(type="str", required=True),
        organization=dict(type="str", required=True, aliases=['org']),
        project_name=dict(type="str", required=True),
        project_slug=dict(type="str", required=True),
        state=dict(type="str", required=True, choices=['absent', 'present']),
        team=dict(type="str", required=True),
        url=dict(type="str", default="sentry.io"),
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

    def does_project_exist(project_name, organization, team, api_token):
        response, info = fetch_url(
            module, "{url}/api/0/teams/{organization}/{team}/projects/".format(
                url=url, organization=organization, team=team),
            headers={"Authorization": "Bearer {0}".format(api_token)},
            method="GET")
        if info["status"] != 200:
            module.fail_json(msg="Unable to obtain a project list, response status: {0}, message: {1}".format(
                info["status"], info.get("msg", "No message has been provided")))
        body = json.loads(response.read())
        return bool([x for x in body if x["name"] == project_name])

    if state == 'present':
        if does_project_exist(project_name, organization, team, api_token):
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
                    info["status"], info.get("msg", "No message has been provided")))
        module.exit_json(changed=True)

    if state == 'absent':
        if does_project_exist(project_name, organization, team, api_token):
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
                        info["status"], info.get("msg", "No message has been provided")))
            module.exit_json(changed=True)
        else:
            module.exit_json(changed=False)


if __name__ == '__main__':
    main()
