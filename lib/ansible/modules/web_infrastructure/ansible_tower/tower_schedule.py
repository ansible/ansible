#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Pierre GINDRAUD (pgindraud@gmail.com)
# Based on code:
# Copyright: (c) 2018, Adrien Fleury <fleu42@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_schedule
short_description: Manages Tower job schedules.
description:
     - Adds, updates and removes job schedules
     - You must set one of the job_template, inventory_source, project or workflow on which you want to set the schedule
version_added: "2.9"
author:
  - Pierre GINDRAUD (@Turgon37)
options:
    name:
      description:
        - Name to use for the schedule.
      type: str
      required: true
    rrule:
      description:
        - The schedule time string in rrule format.
      type: str
      required: true
    job_template:
      description:
        - The name of the job template to apply schedule to
      type: str
    inventory_source:
      description:
        - The name of the inventory source to apply schedule to
      type: str
    project:
      description:
        - The name of the project to apply schedule to
      type: str
    workflow:
      description:
        - The name of the workflow to apply schedule to
      type: str
    enabled:
      description:
        - Is the schedule enabled ?
      type: bool
      default: true
    state:
      description:
        - Desired state of the resource.
      choices: ["present", "absent"]
      default: "present"

extends_documentation_fragment:
  - tower
'''

EXAMPLES = '''
- name: Ensure tower job templates schedules
  tower_schedule:
    name: play_1__periodic
    rrule: 'DTSTART;TZID=Europe/Paris:20190625T001500 RRULE:FREQ=HOURLY;INTERVAL=3'
    job_template: play_1
    state: present
    tower_host: '{{ tower__host }}'
    tower_username: '{{ tower__username }}'
    tower_password: '{{ tower__password }}'
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ansible_tower import (
    TowerModule,
    tower_auth_config,
    tower_check_mode
)

try:
    import tower_cli
    import tower_cli.exceptions as exc
    from tower_cli.conf import settings
except ImportError:
    pass


def initial_diff(name, state, prev_state):
    diff = {'before': {'name': name},
            'after': {'name': name},
            }

    if prev_state != state:
        diff['before']['state'] = prev_state
        diff['after']['state'] = state

    return diff


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        rrule=dict(type='str', required=True),
        job_template=dict(type='str'),
        inventory_source=dict(type='str'),
        project=dict(type='str'),
        workflow=dict(type='str'),
        enabled=dict(type='bool', default=True),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        mutually_exclusive = [
          ['job_template', 'inventory_source', 'project', 'workflow'],
        ],
        supports_check_mode=True
    )

    ref_found = None
    for k in ['job_template', 'inventory_source', 'project', 'workflow']:
        if module.params.get(k):
            ref_found = True
    if not ref_found:
        module.fail_json(
            msg='Failed to update schedule,'
                'you should specify at least job_template or inventory_source or project or workflow',
            changed=False
        )

    name = module.params.get('name')
    state = module.params.get('state')

    json_output = {'schedule': name, 'state': state}
    changed = False

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        schedule_res = tower_cli.get_resource('schedule')
        job_template_res = tower_cli.get_resource('job_template')
        inventory_source_res = tower_cli.get_resource('inventory_source')
        project_res = tower_cli.get_resource('project')
        workflow_res = tower_cli.get_resource('workflow')
        params = {}
        for k in ['name', 'enabled', 'rrule']:
            params[k] = module.params.get(k)

        try:
            try:
                current = schedule_res.get(name=name)
                prev_state = 'present'
            except exc.NotFound:
                current = dict()
                prev_state = 'absent'

            diff = initial_diff(name, state, prev_state)

            try:
                if module.params.get('job_template'):
                    params['job_template'] = job_template_res.get(name=module.params.get('job_template'))['id']
                    params['unified_job_template'] = params['job_template']
                if module.params.get('inventory_source'):
                    params['inventory_source'] = inventory_source_res.get(name=module.params.get('inventory_source'))['id']
                    params['unified_job_template'] = params['inventory_source']
                if module.params.get('project'):
                    params['project'] = inventory_source_res.get(name=module.params.get('project'))['id']
                    params['unified_job_template'] = params['project']
                if module.params.get('workflow'):
                    params['workflow'] = inventory_source_res.get(name=module.params.get('workflow'))['id']
                    params['unified_job_template'] = params['workflow']
            except exc.MultipleResults as excinfo:
                module.fail_json(
                    msg='Failed to update schedule,'
                    'multiple target resource found, please be more specific in name: {0}'.format(excinfo),
                    changed=False
                )
            except exc.NotFound as excinfo:
                module.fail_json(
                    msg='Failed to update schedule,'
                    'target resource not found: {0}'.format(excinfo),
                    changed=False
                )

            if state == 'present':
                if prev_state != state:
                    for key, value in params.items():
                        diff['after'][key] = str(value)

                    if not module.check_mode:
                        result = schedule_res.create(**params)
                        changed = result['changed']
                    else:
                        changed = True
                else:
                    must_change = False
                    for key, value in params.items():
                        if key in current and current[key] != value:
                            diff['before'][key] = str(current[key])
                            diff['after'][key] = str(value)
                            must_change = True

                    if must_change:
                        if not module.check_mode:
                            result = schedule_res.modify(**params)
                            changed = result['changed']
                        else:
                            changed = True
            elif state == 'absent' and state != prev_state:
                if not module.check_mode:
                    result = schedule_res.delete(name=name)
                    changed = result['changed']
                else:
                    changed = True
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update workflow template: \
                    {0}'.format(excinfo), changed=False)
        except exc.UsageError as excinfo:
            module.fail_json(msg='Failed to update workflow template: \
                    {0}'.format(excinfo), changed=False)

    json_output['changed'] = changed
    json_output['diff'] = diff
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
