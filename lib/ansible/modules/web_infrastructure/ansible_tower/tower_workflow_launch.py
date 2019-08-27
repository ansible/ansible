#!/usr/bin/python
# coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: tower_workflow_launch
author: "John Westcott IV (@john-westcott-iv)"
version_added: "2.8"
short_description: Run a workflow in Ansible Tower
description:
    - Launch an Ansible Tower workflows. See
      U(https://www.ansible.com/tower) for an overview.
options:
    workflow_template:
      description:
        - The name of the workflow template to run.
      required: True
    extra_vars:
      description:
        - Any extra vars required to launch the job.
      required: False
    wait:
      description:
        - Wait for the workflow to complete.
      required: False
      default: True
      type: bool
    timeout:
      description:
        - If waiting for the workflow to complete this will abort after this
        - ammount of seconds

requirements:
  - "python >= 2.6"
extends_documentation_fragment: tower
'''

RETURN = '''
tower_version:
    description: The version of Tower we connected to
    returned: If connection to Tower works
    type: str
    sample: '3.4.0'
job_info:
    description: dictionary containing information about the workflow executed
    returned: If workflow launched
    type: dict
'''


EXAMPLES = '''
- name: Launch a workflow
  tower_workflow_launch:
    name: "Test Workflow"
  delegate_to: localhost
  run_once: true
  register: workflow_results

- name: Launch a Workflow with parameters without waiting
  tower_workflow_launch:
    workflow_template: "Test workflow"
    extra_vars: "---\nmy: var"
    wait: False
  delegate_to: localhost
  run_once: true
  register: workflow_task_info
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config

try:
    import tower_cli
    from tower_cli.api import client
    from tower_cli.conf import settings
    from tower_cli.exceptions import ServerError, ConnectionError, BadRequest, TowerCLIError
except ImportError:
    pass


def main():
    argument_spec = dict(
        workflow_template=dict(required=True),
        extra_vars=dict(required=False),
        wait=dict(required=False, default=True, type='bool'),
        timeout=dict(required=False, default=None, type='int'),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    workflow_template = module.params.get('workflow_template')
    extra_vars = module.params.get('extra_vars')
    wait = module.params.get('wait')
    timeout = module.params.get('timeout')

    # If we are going to use this result to return we can consider ourselfs changed
    result = dict(
        changed=False,
        msg='initial message'
    )

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        # First we will test the connection. This will be a test for both check and run mode
        # Note, we are not using the tower_check_mode method here because we want to do more than just a ping test
        # If we are in check mode we also want to validate that we can find the workflow
        try:
            ping_result = client.get('/ping').json()
            # Stuff the version into the results as an FYI
            result['tower_version'] = ping_result['version']
        except(ServerError, ConnectionError, BadRequest) as excinfo:
            result['msg'] = "Failed to reach Tower: {0}".format(excinfo)
            module.fail_json(**result)

        # Now that we know we can connect, lets verify that we can resolve the workflow_template
        try:
            workflow = tower_cli.get_resource("workflow").get(**{'name': workflow_template})
        except TowerCLIError as e:
            result['msg'] = "Failed to find workflow: {0}".format(e)
            module.fail_json(**result)

        # Since we were able to find the workflow, if we are in check mode we can return now
        if module.check_mode:
            result['msg'] = "Check mode passed"
            module.exit_json(**result)

        # We are no ready to run the workflow
        try:
            result['job_info'] = tower_cli.get_resource('workflow_job').launch(
                workflow_job_template=workflow['id'],
                monitor=False,
                wait=wait,
                timeout=timeout,
                extra_vars=extra_vars
            )
            if wait:
                # If we were waiting for a result we will fail if the workflow failed
                if result['job_info']['failed']:
                    result['msg'] = "Workflow execution failed"
                    module.fail_json(**result)
                else:
                    module.exit_json(**result)

            # We were not waiting and there should be no way we can make it here without the workflow fired off so we can return a success
            module.exit_json(**result)

        except TowerCLIError as e:
            result['msg'] = "Failed to execute workflow: {0}".format(e)
            module.fail_json(**result)


if __name__ == '__main__':
    main()
