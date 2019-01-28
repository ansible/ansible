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
module: digital_ocean_project_facts
short_description: Query information about Digital Ocean projects.
description:
    - Query information about Digital Ocean projects.
author: "Kevin Breit (@kbreit)"
version_added: "2.8"
options:
  name:
    description:
      - Name of project.
      - Maximum of 255 characters.
  id:
    description:
      - ID number of project as assigned by DigitalOcean.
  default:
    description:
      - States whether resources are assigned to project by default.
      - Only valid for modifications to existing projects.
    type: bool
  resources:
    description:
      - 'List of Uniform Resource Names (URN), such as do:droplet:1234, of which to move into the project.'
      - Can only be performed against an existing project.
    type: bool
extends_documentation_fragment: digital_ocean.documentation
notes:
  - Two environment variables can be used, C(DO_API_KEY) and C(DO_API_TOKEN).
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
    description: DigitalOcean Project details
    returned: success
    type: dict
    contains:
        id:
            description: The unique universal identifier of the project.
            returned: success
            type: string, when resource not defined or false
            example: 4e1bfbc3-dc3e-41f2-a18f-1b4d7ba71679
        owner_uuid:
            description: The unique universal identifier of the project owner.
            returned: success, when resource not defined or false
            type: string
            example: The unique universal identifier of the project owner.
        owner_id:
            description: The integer id of the project owner.
            returned: success, when resource not defined or false
            type: string
            example: 2
        name:
            description: The human-readable name for the project. The maximum length is 175 characters and the name must be unique.
            returned: success, when resource not defined or false
            type: string
            example: Production
        description:
            description: The description of the project. The maximum length is 255 characters.
            returned: success, when resource not defined or false
            type: string
            example: Production database
        purpose:
            description: The purpose of the project. The maximum length is 255 characters.
            type: string
            returned: succes, when resource not defined or false
            example: Service or API
        environment:
            description: The environment of the project's resources.
            returned: success, when resource not defined or false
            type: string
            example: Production
        is_default:
            description: If true, all resources will be added to this project if no project is specified.
            returned: success, when resource not defined or false
            type: string
            example: true
        created_at:
            description: A time value given in ISO8601 combined date and time format that represents when the project was created.
            returned: success, when resource not defined or false
            type: string
            example: "2018-09-27T15:52:48Z"
        updated_at:
            description: A time value given in ISO8601 combined date and time format that represents when the project was updated.
            returned: success, when resource not defined or false
            type: string
            example: "2018-09-27T15:52:48Z"
        urn:
            description: The uniform resource name of the resource.
            returned: success, when resource is true
            type: string
            example: "do:droplet:1"
        assigned_at:
            description: A time value given in ISO8601 combined date and time format that represents when the project was created.
            returned: success, when resource is true
            type: string
            example: "2018-09-28T19:26:37Z"
        links:
            description: The links object contains the self object, which contains the resource relationship.
            returned: success, when resource is true
            type: string
            example: "https://api.digitalocean.com/v2/droplets/1"
        status:
            description: The status of assigning and fetching the resources.
            returned: success, when resource is true
            type: string
            example: ok
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
    name = module.params['name']
    pid = module.params['id']
    rest = DigitalOceanHelper(module)

    if pid is None and name is not None:
        pid = get_pid(name, get_all_projects(rest)['projects'])
    if module.params['resources'] is not None:
        if module.params['default'] is None and pid is None:
            module.fail_json(msg='Project name, project ID, or default is required for querying resource information')

    if module.params['resources'] is None:  # Get generic information about projects
        if pid is not None:  # Get information about specific project
            response = rest.get('projects/{0}'.format(pid))
        elif module.params['default'] is True:  # Get information about default project
            response = rest.get('projects/default')
        else:  # Get information about all projects
            response = rest.get_paginated_data(base_url='projects?', data_key_name='projects')
    else:
        if module.params['default'] is True:  # Get information about default project resources
            response = rest.get_paginated_data(base_url='projects/default/resources?', data_key_name='resources')
        elif module.params['default'] is None or module.params['default'] is False:  # Get information about specific project resources
            response = rest.get_paginated_data(base_url='/projects/{0}/resources?'.format(pid), data_key_name='resources')
    try:
        if response.status_code == 200:
            module.exit_json(changed=False, data=response.json)
        else:
            module.fail_json(msg=response.json)
    except AttributeError:  # Probably using paginated data
        module.exit_json(changed=False, data=response)
    module.exit_json(changed=False)


def main():
    argument_spec = DigitalOceanHelper.digital_ocean_argument_spec()
    argument_spec.update(
        name=dict(type='str'),
        default=dict(type='bool'),
        id=dict(type='str'),
        resources=dict(type='bool'),
    )

    module = AnsibleModule(argument_spec=argument_spec)

    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == '__main__':
    main()
