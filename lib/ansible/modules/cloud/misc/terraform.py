#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2017, Ryan Scott Brown <ryansb@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: terraform
short_description: Manages a Terraform deployment (and plans)
description:
     - Provides support for deploying resources with Terraform and pulling
       resource information back into Ansible.
version_added: "2.5"
options:
  state:
    choices: ['latest', 'present', 'absent']
    description:
      - Goal state of given stage/project
    required: false
    default: present
  tf_bin_path:
    description:
      - The path of a terraform binary to use, relative to the 'service_path'
        unless you supply an absolute path.
    required: false
  project_path:
    description:
      - The path to the root of the Terraform directory with the
        vars.tf/main.tf/etc to use.
    required: true
  plan:
    description:
      - The path to an existing Terraform plan file to apply. If this is not
        specified, Ansible will build a new TF plan and execute it.
    required: false
  force_init:
    description:
      - To avoid duplicating infra, if a state file can't be found this will
        force a `terraform init`. Generally, this should be turned off unless
        you intend to provision an entirely new Terraform deployment.
    required: false
    default: false
notes:
   - To just run a `terraform plan`, use check mode.
requirements: [ "terraform" ]
author: "Ryan Scott Brown @ryansb"
'''

EXAMPLES = """
# Basic deploy of a service
- terraform:
    project_path: '{{ project_dir }}'
    state: latest
"""

RETURN = """
service_name:
  type: string
  description: Most
  returned: always
  sample: my-fancy-service-dev
state:
  type: string
  description: Whether the stack for the TF project is present/absent.
  returned: always
command:
  type: string
  description: Full `terraform` command built by this module, in case you want to re-run the command outside the module or debug a problem.
  returned: always
  sample: terraform apply ...
"""

import os
import json
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule

APPLY_ARGS = ('apply', '-auto-approve=true')

def preflight_validation(module, bin_path, project_path, variables_file=None, plan_file=None):
    if not os.path.exists(bin_path):
        module.fail_json(msg="Path for Terraform binary '{0}' doesn't exist on this host - check the path and try again please.".format(project_path))
    if not os.path.isdir(project_path):
        module.fail_json(msg="Path for Terraform project '{0}' doesn't exist on this host - check the path and try again please.".format(project_path))

    rc, out, err = module.run_command([bin_path, 'validate'], cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failed to validate Terraform configuration files:\r\n{0}".format(err))


def build_plan(module, bin_path, project_path, variables_args):
    _, plan_path = tempfile.mkstemp(suffix='.tfplan')

    rc, out, err = module.run_command([bin_path, 'plan', '-detailed-exitcode', '-out', plan_path] + variables_args, cwd=project_path)

    if rc == 0:
        # no changes
        return plan_path, False
    elif rc == 1:
        # failure to plan
        module.fail_json(msg='Terraform plan could not be created\r\nSTDOUT: {}\r\n\r\nSTDERR: {}'.format(out, err))
    elif rc == 2:
        # changes, but successful
        return plan_path, True

    module.fail_json(msg='Terraform plan failed with unexpected exit code {}. \r\nSTDOUT: {}\r\n\r\nSTDERR: {}'.format(rc, out, err))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            project_path=dict(required=True, type='path'),
            binary_path=dict(type='path'),
            state=dict(default='present', choices=['present', 'absent', 'latest']),
            variables=dict(type='dict'),
            variables_file=dict(type='path'),
            plan_file=dict(type='path'),
            state_file=dict(type='path'), #TODO
        ),
    )

    project_path = module.params.get('project_path')
    bin_path = module.params.get('binary_path')
    state = module.params.get('state')
    variables = module.params.get('variables') or {}
    variables_file = module.params.get('variables_file')
    plan_file = module.params.get('plan_file')
    state_file = module.params.get('state_file')

    if bin_path is not None:
        command = [bin_path]
    else:
        command = [module.get_bin_path('terraform')]

    preflight_validation(module, command[0], project_path)

    variables_args = []
    for k, v in variables.items():
        variables_args.extend([
            '-var',
            '{}={}'.format(k, v)
        ])
    if variables_file:
        variables_args.append('-var-file', variables_file)


    command.extend(APPLY_ARGS)

    # we aren't sure if this plan will result in changes, so assume yes
    needs_application, changed = True, True

    if plan_file and os.path.exists(os.path.expanduser('plan_file')):
        command.append(plan_file)
    if plan_file and not os.path.exists('plan_file'):
        module.fail_json(msg='Could not find plan_file "{}", check the path and try again.'.format(plan_file))
    else:
        plan_file, needs_application = build_plan(module, command[0], project_path, variables_args)
        command.append(plan_file)

    #module.fail_json(msg="About to run: {}, needs_application: {}".format(command, needs_application))
    if needs_application:
        rc, out, err = module.run_command(command, cwd=project_path)
        if rc != 0:
            module.fail_json(msg="Failure when executing Terraform command. Exited {}.\nstdout: {}\nstderr: {}".format(rc, out, err))
    else:
        changed = False
        out, err = '', ''

    rc, outputs_text, outputs_err = module.run_command([command[0], 'output', '-json'], cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failure when getting Terraform outputs. Exited {}.\nstdout: {}\nstderr: {}".format(rc, outputs_text, outputs_err))

    outputs = json.loads(outputs_text)


    # gather some facts about the deployment
    module.exit_json(changed=changed, state='present', outputs=outputs, sdtout=out, stderr=err, command=command)


if __name__ == '__main__':
    main()
