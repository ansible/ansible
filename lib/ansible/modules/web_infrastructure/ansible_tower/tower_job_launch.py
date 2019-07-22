#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_job_launch
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: Launch an Ansible Job.
description:
    - Launch an Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_template:
      description:
        - Name of the job template to use.
      required: True
    job_explanation:
      description:
        - Job explanation field.
    job_type:
      description:
        - Job_type to use for the job, only used if prompt for job_type is set.
      choices: ["run", "check", "scan"]
    inventory:
      description:
        - Inventory to use for the job, only used if prompt for inventory is set.
    credential:
      description:
        - Credential to use for job, only used if prompt for credential is set.
    extra_vars:
      description:
        - Extra_vars to use for the job_template. Prepend C(@) if a file.
    limit:
      description:
        - Limit to use for the I(job_template).
    tags:
      description:
        - Specific tags to use for from playbook.
    use_job_endpoint:
      description:
        - Disable launching jobs from job template.
      type: bool
      default: 'no'
extends_documentation_fragment: tower
'''

EXAMPLES = '''
# Launch a job template
- name: Launch a job
  tower_job_launch:
    job_template: "My Job Template"
  register: job

- name: Wait for job max 120s
  tower_job_wait:
    job_id: "{{ job.id }}"
    timeout: 120

# Launch job template with inventory and credential for prompt on launch
- name: Launch a job with inventory and credential
  tower_job_launch:
    job_template: "My Job Template"
    inventory: "My Inventory"
    credential: "My Credential"
  register: job
- name: Wait for job max 120s
  tower_job_wait:
    job_id: "{{ job.id }}"
    timeout: 120
'''

RETURN = '''
id:
    description: job id of the newly launched job
    returned: success
    type: int
    sample: 86
status:
    description: status of newly launched job
    returned: success
    type: str
    sample: pending
'''


from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        job_template=dict(required=True, type='str'),
        job_type=dict(choices=['run', 'check', 'scan']),
        inventory=dict(type='str', default=None),
        credential=dict(type='str', default=None),
        limit=dict(),
        tags=dict(type='list'),
        extra_vars=dict(type='list'),
    )

    module = TowerModule(
        argument_spec,
        supports_check_mode=True
    )

    json_output = {}
    tags = module.params.get('tags')

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        try:
            params = module.params.copy()
            if isinstance(tags, list):
                params['tags'] = ','.join(tags)
            job = tower_cli.get_resource('job')

            lookup_fields = ('job_template', 'inventory', 'credential')
            for field in lookup_fields:
                try:
                    name = params.pop(field)
                    if name:
                        result = tower_cli.get_resource(field).get(name=name)
                        params[field] = result['id']
                except exc.NotFound as excinfo:
                    module.fail_json(msg='Unable to launch job, {0}/{1} was not found: {2}'.format(field, name, excinfo), changed=False)

            result = job.launch(no_input=True, **params)
            json_output['id'] = result['id']
            json_output['status'] = result['status']
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Unable to launch job: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
