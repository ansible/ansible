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
    service_path: '{{ project_dir }}'
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
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule

APPLY_ARGS = ('apply', '-auto-approve', 'true')

def preflight_validation(module, bin_path, project_path, variables_file=None, plan_file=None):
    if not os.path.exists(bin_path):
        module.fail_json(msg="Path for Terraform binary '{0}' doesn't exist on this host - check the path and try again please.".format(project_path))
    if not os.path.isdir(project_path):
        module.fail_json(msg="Path for Terraform project '{0}' doesn't exist on this host - check the path and try again please.".format(project_path))

    rc, out, err = module.run_command([bin_path, 'validate'], cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failed to validate Terraform configuration files:\r\n{0}".format(err))


def build_plan(module, bin_path, project_path, variables_args):
    #TODO - for right now just require a plan file
    _, plan_path = tempfile.mkstemp(suffix='.tfplan')

    rc, out, err = module.run_command([bin_path, 'plan', '-out', plan_path] + variables_args, cwd=project_path)

    if rc == 0:
        return plan_path, True
    return plan_path, False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_path=dict(required=True, type='path'),
            binary_path=dict(type='path'),
            state=dict(default='present', choices=['present', 'absent', 'latest']),
            variables=dict(type='json'),
            variables_file=dict(type='path'),
            plan_file=dict(type='path'),
            state_file=dict(type='path'), #TODO
        ),
    )

    project_path = module.params.get('service_path')
    bin_path = module.params.get('binary_path')
    state = module.params.get('state')
    variables = module.params.get('variables')
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
            '{}={}'.format(variables)
        ])
    if variables_file:
        variables_args.append('-var-file', variables_file)


    command.extend(APPLY_ARGS)

    if plan_file and os.path.exists('plan_file'):
        command.append(plan_file)
    else:
        plan_file, success = build_plan(module, command[0], project_path, variables_args)
        command.append(plan_file)

    rc, out, err = module.run_command(command, cwd=project_path)
    if rc != 0:
        if state == 'absent' and "-{}' does not exist".format(stage) in out:
            module.exit_json(changed=False, state='absent', command=command,
                    out=out, service_name=get_service_name(module, stage))

        module.fail_json(msg="Failure when executing Terraform command. Exited {}.\nstdout: {}\nstderr: {}".format(rc, out, err))

    # gather some facts about the deployment
    module.exit_json(changed=True, state='present', out=out, command=command,
            service_name=get_service_name(module, stage))


if __name__ == '__main__':
    main()
