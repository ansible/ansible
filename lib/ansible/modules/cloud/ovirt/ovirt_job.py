#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Red Hat, Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: ovirt_job
short_description: Module to manage tags in oVirt/RHV
version_added: "2.9"
author: "Ondra Machacek (@machacekondra)"
description:
    - "This module manage tags in oVirt/RHV. It can also manage assignments
       of those tags to entities."
options:
    id:
        description:
            - "ID of the tag to manage."
    name:
        description:
            - "Name of the tag to manage."
        required: true
    state:
        description:
            - "Should the tag be present/absent."
            - "C(Note): I(attached) and I(detached) states are supported since version 2.4."
        choices: ['present', 'absent']
        default: present
    description:
        description:
            - "Description of the tag to manage."
    parent:
        description:
            - "Name of the parent tag."
    vms:
        description:
            - "List of the VMs names, which should have assigned this tag."
    hosts:
        description:
            - "List of the hosts names, which should have assigned this tag."
extends_documentation_fragment: ovirt
'''

EXAMPLES = '''
# Examples don't contain auth parameter for simplicity,
# look at ovirt_auth module to see how to reuse authentication:

# Create(if not exists) and assign tag to vms vm1 and vm2:
- ovirt_tag:
    name: mytag
    vms:
      - vm1
      - vm2

# Attach a tag to VM 'vm3', keeping the rest already attached tags on VM:
- ovirt_tag:
    name: mytag
    state: attached
    vms:
      - vm3

'''

RETURN = '''
id:
    description: ID of the tag which is managed
    returned: On success if tag is found.
    type: str
    sample: 7de90f31-222c-436c-a1ca-7e655bd5b60c
job:
    description: "Dictionary of all the tag attributes. Tag attributes can be found on your oVirt/RHV instance
                  at following url: http://ovirt.github.io/ovirt-engine-api-model/master/#types/job."
    returned: On success if tag is found.
    type: dict
'''

import traceback

try:
    import ovirtsdk4.types as otypes
except ImportError:
    pass

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ovirt import (
    BaseModule,
    check_sdk,
    create_connection,
    equal,
    get_id_by_name,
    ovirt_full_argument_spec,
    get_dict_of_struct,
)

def build_job(module):
    return otypes.Job(
            description=module.params['description'],
            status=otypes.JobStatus.STARTED,
            external=True,
            auto_cleared=True
    )

def build_step(step, entity_id):
    return otypes.Step(
            description=step.get('description'),
            type=otypes.StepEnum.UNKNOWN,
            job=otypes.Job(
                id=entity_id
            ),
            status=otypes.StepStatus.STARTED,
            external=True,
    )

def attach_steps(module, entity_id, jobs_service):
    # Attach NICs to VM, if specified:
    changed = False
    steps_service = jobs_service.job_service(entity_id).steps_service()
    if module.params.get('steps'):
        for step in module.params.get('steps'):
            step_entity = get_entity(steps_service, step.get('description')) 
            step_state = step.get('state','present')
            if not module.check_mode:
                if step_state == 'present' or step_state == 'started':
                    if step_entity is None:
                        steps_service.add(build_step(step, entity_id))
                        changed = True
                if step_entity is not None and step_entity.status != otypes.StepStatus.FINISHED:
                    if step_state == 'absent' or step_state == 'finished':
                        steps_service.step_service(step_entity.id).end(status=otypes.StepStatus.FINISHED, succeeded=True)
                        changed = True
                    elif step_state == 'failed':
                        steps_service.step_service(step_entity.id).end(status=otypes.StepStatus.FINISHED, succeeded=False)
                        changed = True
    return changed

def get_entity(service, description):
    all_entities = service.list()
    for entity in all_entities:
        if entity.description == description:
            return entity

def main():
    argument_spec = ovirt_full_argument_spec(
        state=dict(
            choices=['present', 'absent', 'started', 'finished', 'failed'],
            default='present',
        ),
        description=dict(default=None),
        steps=dict(default=None, type='list'),
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    check_sdk(module)

    try:
        auth = module.params.pop('auth')
        connection = create_connection(auth)
        jobs_service = connection.system_service().jobs_service()

        state = module.params['state']
        job = get_entity(jobs_service, module.params['description'])
        changed = False 
        if state in ['present', 'started']:
            if job is None:
                job = jobs_service.add(build_job(module))
                changed = True
            changed = changed or attach_steps(module, job.id, jobs_service)

        elif state in ['absent', 'finished']:
            jobs_service.job_service(job.id).end(status=otypes.JobStatus.FINISHED, succeeded=True)
            changed = True

        elif state == 'failed':
            jobs_service.job_service(job.id).end(status=otypes.JobStatus.FINISHED, succeeded=False)
            changed = True

        ret ={
            'changed': changed,
            'id': getattr(job, 'id', None),
            type(job).__name__.lower(): get_dict_of_struct(
                struct=job,
                connection=connection,
                fetch_nested=module.params.get('fetch_nested'),
                attributes=module.params.get('nested_attributes'),
            ),
        }

        module.exit_json(**ret)
    except Exception as e:
        module.fail_json(msg=str(e), exception=traceback.format_exc())
    finally:
        connection.close(logout=auth.get('token') is None)


if __name__ == "__main__":
    main()
