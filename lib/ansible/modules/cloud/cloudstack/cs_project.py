#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2015, René Moser <mail@renemoser.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cs_project
short_description: Manages projects on Apache CloudStack based clouds.
description:
    - Create, update, suspend, activate and remove projects.
version_added: '2.0'
author: René Moser (@resmo)
options:
  name:
    description:
      - Name of the project.
    type: str
    required: true
  display_text:
    description:
      - Display text of the project.
      - If not specified, I(name) will be used as I(display_text).
    type: str
  state:
    description:
      - State of the project.
    type: str
    default: present
    choices: [ present, absent, active, suspended ]
  domain:
    description:
      - Domain the project is related to.
    type: str
  account:
    description:
      - Account the project is related to.
    type: str
  tags:
    description:
      - List of tags. Tags are a list of dictionaries having keys I(key) and I(value).
      - "If you want to delete all tags, set a empty list e.g. I(tags: [])."
    type: list
    aliases: [ tag ]
    version_added: '2.2'
  poll_async:
    description:
      - Poll async jobs until job has finished.
    type: bool
    default: yes
extends_documentation_fragment: cloudstack
'''

EXAMPLES = '''
- name: Create a project
  cs_project:
    name: web
    tags:
      - { key: admin, value: john }
      - { key: foo,   value: bar }
  delegate_to: localhost

- name: Rename a project
  cs_project:
    name: web
    display_text: my web project
  delegate_to: localhost

- name: Suspend an existing project
  cs_project:
    name: web
    state: suspended
  delegate_to: localhost

- name: Activate an existing project
  cs_project:
    name: web
    state: active
  delegate_to: localhost

- name: Remove a project
  cs_project:
    name: web
    state: absent
  delegate_to: localhost
'''

RETURN = '''
---
id:
  description: UUID of the project.
  returned: success
  type: str
  sample: 04589590-ac63-4ffc-93f5-b698b8ac38b6
name:
  description: Name of the project.
  returned: success
  type: str
  sample: web project
display_text:
  description: Display text of the project.
  returned: success
  type: str
  sample: web project
state:
  description: State of the project.
  returned: success
  type: str
  sample: Active
domain:
  description: Domain the project is related to.
  returned: success
  type: str
  sample: example domain
account:
  description: Account the project is related to.
  returned: success
  type: str
  sample: example account
tags:
  description: List of resource tags associated with the project.
  returned: success
  type: list
  sample: '[ { "key": "foo", "value": "bar" } ]'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.cloudstack import (
    AnsibleCloudStack,
    cs_argument_spec,
    cs_required_together
)


class AnsibleCloudStackProject(AnsibleCloudStack):

    def get_project(self):
        if not self.project:
            project = self.module.params.get('name')

            args = {
                'account': self.get_account(key='name'),
                'domainid': self.get_domain(key='id'),
                'fetch_list': True,
            }
            projects = self.query_api('listProjects', **args)
            if projects:
                for p in projects:
                    if project.lower() in [p['name'].lower(), p['id']]:
                        self.project = p
                        break
        return self.project

    def present_project(self):
        project = self.get_project()
        if not project:
            project = self.create_project(project)
        else:
            project = self.update_project(project)
        if project:
            project = self.ensure_tags(resource=project, resource_type='project')
            # refresh resource
            self.project = project
        return project

    def update_project(self, project):
        args = {
            'id': project['id'],
            'displaytext': self.get_or_fallback('display_text', 'name')
        }
        if self.has_changed(args, project):
            self.result['changed'] = True
            if not self.module.check_mode:
                project = self.query_api('updateProject', **args)

                poll_async = self.module.params.get('poll_async')
                if project and poll_async:
                    project = self.poll_job(project, 'project')
        return project

    def create_project(self, project):
        self.result['changed'] = True

        args = {
            'name': self.module.params.get('name'),
            'displaytext': self.get_or_fallback('display_text', 'name'),
            'account': self.get_account('name'),
            'domainid': self.get_domain('id')
        }
        if not self.module.check_mode:
            project = self.query_api('createProject', **args)

            poll_async = self.module.params.get('poll_async')
            if project and poll_async:
                project = self.poll_job(project, 'project')
        return project

    def state_project(self, state='active'):
        project = self.present_project()

        if project['state'].lower() != state:
            self.result['changed'] = True

            args = {
                'id': project['id']
            }
            if not self.module.check_mode:
                if state == 'suspended':
                    project = self.query_api('suspendProject', **args)
                else:
                    project = self.query_api('activateProject', **args)

                poll_async = self.module.params.get('poll_async')
                if project and poll_async:
                    project = self.poll_job(project, 'project')
        return project

    def absent_project(self):
        project = self.get_project()
        if project:
            self.result['changed'] = True

            args = {
                'id': project['id']
            }
            if not self.module.check_mode:
                res = self.query_api('deleteProject', **args)

                poll_async = self.module.params.get('poll_async')
                if res and poll_async:
                    res = self.poll_job(res, 'project')
            return project


def main():
    argument_spec = cs_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        display_text=dict(),
        state=dict(choices=['present', 'absent', 'active', 'suspended'], default='present'),
        domain=dict(),
        account=dict(),
        poll_async=dict(type='bool', default=True),
        tags=dict(type='list', aliases=['tag']),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=cs_required_together(),
        supports_check_mode=True
    )

    acs_project = AnsibleCloudStackProject(module)

    state = module.params.get('state')
    if state in ['absent']:
        project = acs_project.absent_project()

    elif state in ['active', 'suspended']:
        project = acs_project.state_project(state=state)

    else:
        project = acs_project.present_project()

    result = acs_project.get_result(project)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
