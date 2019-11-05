#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Timo Funke <timoses@msn.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: pulp3_repository

short_description: Manage Pulp3 Repositories

version_added: "2.10"

author:
  - Timo Funke (@timoses)

description:
  - Supports CRUD operations against Pulp3 Repositories.

extends_documentation_fragment:
  - url
  - pulp3
  - pulp3.named

options:
  description:
    description:
    - An optional description.
    type: str
  state:
    description:
    - Whether the repository should exist or not.
    choices:
    - present
    - absent
    default: present
    type: str

requirements:
  - "python >= 2.7"
'''

EXAMPLES = '''
- name: Create a repository named 'foo'
  pulp3_repository:
    name: foo
    description: My name is foo and I am a Pulp3 repository

- name: Remove 'foo' repository again
  pulp3_repository:
    name: foo
    state: absent
'''

RETURN = r''' # '''

from ansible.module_utils.pulp3 import PulpAnsibleModule, REPOSITORY_API, load_pulp_api


PULP_API_DATA = {
    'name': 'name',
    'description': 'description'
}


class PulpRepositoryAnsibleModule(PulpAnsibleModule):

    def __init__(self):
        self.module_to_api_data = PULP_API_DATA
        PulpAnsibleModule.__init__(self)

        self.state = self.module.params['state']
        self.api = load_pulp_api(self.module, REPOSITORY_API)

    def module_spec(self):
        arg_spec = PulpAnsibleModule.argument_spec(self)
        arg_spec.update(
            name=dict(type='str', required=True),
            description=dict(required=False),
            state=dict(
                default="present",
                choices=['absent', 'present'])
        )
        return {'argument_spec': arg_spec}

    def execute(self):
        changed = False

        if self.state == 'present':
            changed = self.create_or_update()

        elif self.state == 'absent':
            changed = self.delete()

        self.module.exit_json(changed=changed)


def main():
    PulpRepositoryAnsibleModule().execute()


if __name__ == '__main__':
    main()
