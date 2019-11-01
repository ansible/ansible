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

module: pulp3_task

short_description: Check Pulp3 Task state

version_added: "2.10"

author:
  - Timo Funke (@timoses)

description:
  - This module fails if the task's state is not in the desired state.

extends_documentation_fragment:
  - url
  - pulp3

options:
  href:
    description:
    - Task's C(pulp_href) (e.g. C(/pulp/api/v3/tasks/d82ff00f-8e40-4935-80a9-a598baa7a2d8/)).
    required: true
    type: str
  state:
    description:
    - The state in which the task should be in.
    choices:
    - waiting
    - skipped
    - running
    - completed
    - failed
    - canceled
    type: str
    default: completed

requirements:
  - "python >= 2.7"
'''

EXAMPLES = '''
- name: Create a remote and start a sync task
  pulp3_remote:
    name: my_remote
    remote_url: "https://repos.fedorapeople.org/pulp/pulp/demo_repos/test_file_repo/PULP_MANIFEST"
    repositories: my_repo
    sync: yes # This will create a task for each repository listed
  register: result

- name: Wait until task is complete
  pulp3_task:
    href: "{{ result.sync_tasks[0].task_href }}"
    state: completed
  register: result
  delay: 3
  retries: 10
  until: result is success
  when: '"sync_tasks" in result'

'''

RETURN = r''' # '''

from ansible.module_utils.pulp3 import PulpAnsibleModule, TASK_API, load_pulp_api


class PulpTaskAnsibleModule(PulpAnsibleModule):

    def __init__(self):
        self.module_to_api_data = {}
        PulpAnsibleModule.__init__(self)

        self.state = self.module.params['state']
        self.api = load_pulp_api(self.module, TASK_API)

    def module_spec(self):
        arg_spec = PulpAnsibleModule.argument_spec(self)
        arg_spec.update(
            href=dict(type='str', required=True),
            state=dict(type='str', default='completed',
                       choices=['waiting', 'skipped', 'running', 'completed', 'failed', 'canceled'])
        )
        return {'argument_spec': arg_spec}

    def execute(self):
        changed = False

        task = self.api.read(self.module.params['href'])
        if task.state != self.state:
            self.module.fail_json(msg="Task is not in desired state '%s'. Task is in state '%s'." % (self.state, task.state))

        self.module.exit_json(changed=changed)


def main():
    PulpTaskAnsibleModule().execute()


if __name__ == '__main__':
    main()
