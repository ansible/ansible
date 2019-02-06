#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: digital_ocean_project
short_description: Create and remove Digital Ocean projects
description:
    - Create and remove Digital Ocean projects.
author: "Kevin Breit (@kbreit)"
version_added: "2.8"
options:
  name:
    description:
      - Name of project.
      - Maximum of 255 characters.
  description:
    description:
      - Description of project.
      - Maximum of 255 characters.
  purpose:
    description:
      - Purpose of project per DigitalOcean options.
      - Values are case sensitive.
    choices: ['Just trying out DigitalOcean',
              'Class project / Education purposes',
              'Website or blog',
              'Web application',
              'Service or API',
              'Mobile Application',
              'Machine learning / AI / Data processing',
              'IoT',
              'Operational / Developer tooling',
              'Other']
  id:
    description:
      - ID number of project as assigned by DigitalOcean.
  default:
    description:
      - States whether resources are assigned to project by default.
      - Only valid for modifications to existing projects.
    type: bool
  environment:
    description:
      - General type of deployment environment, case sensitive
    choices: ['Development', 'Production', 'Staging']
  resources:
    description:
      - 'List of Uniform Resource Names (URN), such as do:droplet:1234, of which to move into the project.'
      - Can only be performed against an existing project.
    type: list
  state:
    description:
      - Defines that a project should be created or modified.
    choices: ['present']
    default: present
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, DO_API_KEY and DO_API_TOKEN.
    They both refer to the v2 token.
'''


EXAMPLES = '''
- name: Create a new project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    description: Contains all corporate web frontends
    purpose: Web application
    environment: Production

- name: Assign a resource to an existing project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    resources:
      - "do:droplet:1"
      - "do:volume:42"

- name: Assign a resource to the default project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    default: yes
    resources:
      - "do:droplet:1"
      - "do:volume:42"

- name: Modify properties of an existing project
  digital_ocean_project:
    oauth_token: abc123
    state: present
    name: Web Frontends
    description: Contains all corporate public web frontends
    purpose: Web application
    environment: Production
    default: no
'''


RETURN = '''
data:
    description: a DigitalOcean Project resource
    returned: success and no resource constraint
    type: dict
    sample:     {
      "id": "4e1bfbc3-dc3e-41f2-a18f-1b4d7ba71679",
      "owner_uuid": "99525febec065ca37b2ffe4f852fd2b2581895e7",
      "owner_id": 2,
      "name": "my-web-api",
      "description": "My website API",
      "purpose": "Service or API",
      "environment": "Production",
      "is_default": false,
      "created_at": "2018-09-27T20:10:35Z",
      "updated_at": "2018-09-27T20:10:35Z"
    }

'''

from traceback import format_exc
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.digital_ocean import DigitalOceanHelper
from ansible.module_utils._text import to_native


def get_all_projects(rest):
    response = rest.get('projects')
    if response.status_code == 200:
        return response.json


def get_pid(name, projects):
    for project in projects:
        if project['name'] == name:
            return project['id']
    return False


def core(module):
    state = module.params['state']
    name = module.params['name']
    pid = module.params['id']
    rest = DigitalOceanHelper(module)

    if pid is None:
        pid = get_pid(name, get_all_projects(rest)['projects'])

    if state == 'present':
        if module.params['resources'] is None:  # No resource should be assigned
            payload = {'name': name,
                       'description': module.params['description'],
                       'purpose': module.params['purpose'],
                       'environment': module.params['environment'],
                       }
            if pid is False:  # Create new project
                response = rest.post('projects', data=payload)
                if response.status_code == 201:
                    module.exit_json(changed=True, data=response.json)
                elif response.status_code == 409:
                    module.exit_json(changed=False, data="name is already in use (duplicate)")
                else:
                    module.fail_json(msg=response.json)
            else:
                payload['is_default'] = module.params['default']
                response = rest.put('projects/{0}'.format(pid), data=payload)
                if response.status_code == 200:
                    module.exit_json(changed=True, data=response.json)
                else:
                    module.fail_json(msg=response.json)
        else:  # Manipulate resources in a project
            if module.params['default'] is True:  # Assign to the default project
                payload = {'resources': module.params['resources']}
                response = rest.post('projects/default/resources', data=payload)
                if response.status_code == 200:
                    module.exit_json(changed=True, data=response.json)
                else:
                    module.fail_json(msg=response.json)

            else:  # Assign to a specified project
                if pid is False:
                    module.fail_json(msg="Project must exist to assign resources")
                payload = {'resources': module.params['resources']}
                response = rest.post('projects/{0}/resources'.format(pid), data=payload)
                if response.status_code == 200:
                    module.exit_json(changed=True, data=response.json)
                else:
                    module.fail_json(msg=response.json)
    module.exit_json(changed=False)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        description=dict(type='str'),
        purpose=dict(type='str', choices=['Just trying out DigitalOcean',
                                          'Class project / Education purposes',
                                          'Website or blog',
                                          'Web application',
                                          'Service or API',
                                          'Mobile Application',
                                          'Machine learning / AI / Data processing',
                                          'IoT',
                                          'Operational / Developer tooling',
                                          'Other']),
        environment=dict(type='str', choices=['Development',
                                              'Staging',
                                              'Production',
                                              ]),
        default=dict(type='bool'),
        id=dict(type='str'),
        state=dict(type='str', choices=['present'], default='present'),
        resources=dict(type='list'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
