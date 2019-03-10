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
    choices: ['planned', 'present', 'absent']
    description:
      - Goal state of given stage/project
    required: false
    default: present
  binary_path:
    description:
      - The path of a terraform binary to use, relative to the 'service_path'
        unless you supply an absolute path.
    required: false
  project_path:
    description:
      - The path to the root of the Terraform directory with the
        vars.tf/main.tf/etc to use.
    required: true
  workspace:
    description:
      - The terraform workspace to work with.
    required: false
    default: default
    version_added: 2.7
  purge_workspace:
    description:
      - Only works with state = absent
      - If true, the workspace will be deleted after the "terraform destroy" action.
      - The 'default' workspace will not be deleted.
    required: false
    default: false
    type: bool
    version_added: 2.7
  plan_file:
    description:
      - The path to an existing Terraform plan file to apply. If this is not
        specified, Ansible will build a new TF plan and execute it.
        Note that this option is required if 'state' has the 'planned' value.
    required: false
  state_file:
    description:
      - The path to an existing Terraform state file to use when building plan.
        If this is not specified, the default `terraform.tfstate` will be used.
      - This option is ignored when plan is specified.
    required: false
  variables_file:
    description:
      - The path to a variables file for Terraform to fill into the TF
        configurations.
    required: false
  variables:
    description:
      - A group of key-values to override template variables or those in
        variables files.
    required: false
  targets:
    description:
      - A list of specific resources to target in this plan/application. The
        resources selected here will also auto-include any dependencies.
    required: false
  lock:
    description:
      - Enable statefile locking, if you use a service that accepts locks (such
        as S3+DynamoDB) to store your statefile.
    required: false
    type: bool
  lock_timeout:
    description:
      - How long to maintain the lock on the statefile, if you use a service
        that accepts locks (such as S3+DynamoDB).
    required: false
  force_init:
    description:
      - To avoid duplicating infra, if a state file can't be found this will
        force a `terraform init`. Generally, this should be turned off unless
        you intend to provision an entirely new Terraform deployment.
    default: false
    required: false
    type: bool
  backend_config:
    description:
      - A group of key-values to provide at init stage to the -backend-config parameter.
    required: false
    version_added: 2.7
notes:
   - To just run a `terraform plan`, use check mode.
requirements: [ "terraform" ]
author: "Ryan Scott Brown (@ryansb)"
'''

EXAMPLES = """
# Basic deploy of a service
- terraform:
    project_path: '{{ project_dir }}'
    state: present

# Define the backend configuration at init
- terraform:
    project_path: 'project/'
    state: "{{ state }}"
    force_init: true
    backend_config:
      region: "eu-west-1"
      bucket: "some-bucket"
      key: "random.tfstate"
"""

RETURN = """
outputs:
  type: complex
  description: A dictionary of all the TF outputs by their assigned name. Use `.outputs.MyOutputName.value` to access the value.
  returned: on success
  sample: '{"bukkit_arn": {"sensitive": false, "type": "string", "value": "arn:aws:s3:::tf-test-bukkit"}'
  contains:
    sensitive:
      type: bool
      returned: always
      description: Whether Terraform has marked this value as sensitive
    type:
      type: str
      returned: always
      description: The type of the value (string, int, etc)
    value:
      returned: always
      description: The value of the output as interpolated by Terraform
stdout:
  type: str
  description: Full `terraform` command stdout, in case you want to display it or examine the event log
  returned: always
  sample: ''
command:
  type: str
  description: Full `terraform` command built by this module, in case you want to re-run the command outside the module or debug a problem.
  returned: always
  sample: terraform apply ...
"""

import os
import json
import tempfile
import traceback
from ansible.module_utils.six.moves import shlex_quote

from ansible.module_utils.basic import AnsibleModule

DESTROY_ARGS = ('destroy', '-no-color', '-force')
APPLY_ARGS = ('apply', '-no-color', '-input=false', '-auto-approve=true')
module = None


def preflight_validation(bin_path, project_path, variables_args=None, plan_file=None):
    if project_path in [None, ''] or '/' not in project_path:
        module.fail_json(msg="Path for Terraform project can not be None or ''.")
    if not os.path.exists(bin_path):
        module.fail_json(msg="Path for Terraform binary '{0}' doesn't exist on this host - check the path and try again please.".format(bin_path))
    if not os.path.isdir(project_path):
        module.fail_json(msg="Path for Terraform project '{0}' doesn't exist on this host - check the path and try again please.".format(project_path))

    rc, out, err = module.run_command([bin_path, 'validate'] + variables_args, cwd=project_path, use_unsafe_shell=True)
    if rc != 0:
        module.fail_json(msg="Failed to validate Terraform configuration files:\r\n{0}".format(err))


def _state_args(state_file, project_path, must_exists=True):
    if state_file:
        if os.path.isabs(state_file):
            check_path = state_file
        if not os.path.isabs(state_file):
            check_path = project_path + "/" + state_file
        if must_exists and not os.path.exists(check_path):
            module.fail_json(msg='Could not find state_file "{0}", check the path and try again.'.format(check_path))
        return ['-state', state_file]
    else:
        return []


def init_plugins(bin_path, project_path, backend_config):
    command = [bin_path, 'init', '-input=false']
    if backend_config:
        for key, val in backend_config.items():
            command.extend([
                '-backend-config',
                shlex_quote('{0}={1}'.format(key, val))
            ])
    rc, out, err = module.run_command(command, cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failed to initialize Terraform modules:\r\n{0}".format(err))


def get_workspace_context(bin_path, project_path):
    workspace_ctx = {"current": "default", "all": []}
    command = [bin_path, 'workspace', 'list', '-no-color']
    rc, out, err = module.run_command(command, cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failed to list Terraform workspaces:\r\n{0}".format(err))
    for item in out.split('\n'):
        stripped_item = item.strip()
        if not stripped_item:
            continue
        elif stripped_item.startswith('* '):
            workspace_ctx["current"] = stripped_item.replace('* ', '')
        else:
            workspace_ctx["all"].append(stripped_item)
    return workspace_ctx


def _workspace_cmd(bin_path, project_path, action, workspace):
    command = [bin_path, 'workspace', action, workspace, '-no-color']
    rc, out, err = module.run_command(command, cwd=project_path)
    if rc != 0:
        module.fail_json(msg="Failed to {0} workspace:\r\n{1}".format(action, err))
    return rc, out, err


def create_workspace(bin_path, project_path, workspace):
    _workspace_cmd(bin_path, project_path, 'new', workspace)


def select_workspace(bin_path, project_path, workspace):
    _workspace_cmd(bin_path, project_path, 'select', workspace)


def remove_workspace(bin_path, project_path, workspace):
    _workspace_cmd(bin_path, project_path, 'delete', workspace)


def build_plan(command, project_path, variables_args, state_file, targets, state, plan_path=None):
    if plan_path is None:
        f, plan_path = tempfile.mkstemp(suffix='.tfplan')

    plan_command = [command[0], 'plan', '-input=false', '-no-color', '-detailed-exitcode', '-out', plan_path]

    for t in (module.params.get('targets') or []):
        plan_command.extend(['-target', t])

    plan_command.extend(_state_args(state_file, project_path, False))

    rc, out, err = module.run_command(plan_command + variables_args, cwd=project_path, use_unsafe_shell=True)

    if rc == 0:
        # no changes
        return plan_path, False, out, err, plan_command if state == 'planned' else command
    elif rc == 1:
        # failure to plan
        module.fail_json(msg='Terraform plan could not be created\r\nSTDOUT: {0}\r\n\r\nSTDERR: {1}'.format(out, err))
    elif rc == 2:
        # changes, but successful
        return plan_path, True, out, err, plan_command if state == 'planned' else command

    module.fail_json(msg='Terraform plan failed with unexpected exit code {0}. \r\nSTDOUT: {1}\r\n\r\nSTDERR: {2}'.format(rc, out, err))


def main():
    global module
    module = AnsibleModule(
        argument_spec=dict(
            project_path=dict(required=True, type='path'),
            binary_path=dict(type='path'),
            workspace=dict(required=False, type='str', default='default'),
            purge_workspace=dict(type='bool', default=False),
            state=dict(default='present', choices=['present', 'absent', 'planned']),
            variables=dict(type='dict'),
            variables_file=dict(type='path'),
            plan_file=dict(type='path'),
            state_file=dict(type='path'),
            targets=dict(type='list', default=[]),
            lock=dict(type='bool', default=True),
            lock_timeout=dict(type='int',),
            force_init=dict(type='bool', default=False),
            backend_config=dict(type='dict', default=None),
        ),
        required_if=[('state', 'planned', ['plan_file'])],
        supports_check_mode=True,
    )

    project_path = module.params.get('project_path')
    bin_path = module.params.get('binary_path')
    workspace = module.params.get('workspace')
    purge_workspace = module.params.get('purge_workspace')
    state = module.params.get('state')
    variables = module.params.get('variables') or {}
    variables_file = module.params.get('variables_file')
    plan_file = module.params.get('plan_file')
    state_file = module.params.get('state_file')
    force_init = module.params.get('force_init')
    backend_config = module.params.get('backend_config')

    if bin_path is not None:
        command = [bin_path]
    else:
        command = [module.get_bin_path('terraform', required=True)]

    if force_init:
        init_plugins(command[0], project_path, backend_config)

    workspace_ctx = get_workspace_context(command[0], project_path)
    if workspace_ctx["current"] != workspace:
        if workspace not in workspace_ctx["all"]:
            create_workspace(command[0], project_path, workspace)
        else:
            select_workspace(command[0], project_path, workspace)

    if state == 'present':
        command.extend(APPLY_ARGS)
        if state_file:
            command.extend(['-state-out', state_file])
    elif state == 'absent':
        command.extend(DESTROY_ARGS)

        if state_file:
            command.extend(_state_args(state_file, project_path))

    variables_args = []
    for k, v in variables.items():
        variables_args.extend([
            '-var',
            '{0}={1}'.format(k, v)
        ])
    if variables_file:
        variables_args.extend(['-var-file', variables_file])

    preflight_validation(command[0], project_path, variables_args)

    if module.params.get('lock') is not None:
        if module.params.get('lock'):
            command.append('-lock=true')
        else:
            command.append('-lock=true')
    if module.params.get('lock_timeout') is not None:
        command.append('-lock-timeout=%ds' % module.params.get('lock_timeout'))

    for t in (module.params.get('targets') or []):
        command.extend(['-target', t])

    # we aren't sure if this plan will result in changes, so assume yes
    needs_application, changed = True, False

    if state == 'absent':
        command.extend(variables_args)
    elif state == 'present' and plan_file:
        plan_file_present = ""
        if os.path.isabs(plan_file):
            plan_file_present = plan_file
        else:
            plan_file_present = project_path + "/" + plan_file

        if os.path.exists(plan_file_present):
            command.append(plan_file)
        else:
            module.fail_json(msg='Could not find plan_file "{0}", check the path and try again.'.format(plan_file))
    else:
        plan_file, needs_application, out, err, command = build_plan(command, project_path, variables_args, state_file,
                                                                     module.params.get('targets'), state, plan_file)
        command.append(plan_file)

    if needs_application and not module.check_mode and not state == 'planned':
        rc, out, err = module.run_command(command, cwd=project_path)
        # checks out to decide if changes were made during execution
        if '0 added, 0 changed' not in out and not state == "absent" or '0 destroyed' not in out:
            changed = True
        if rc != 0:
            module.fail_json(
                msg="Failure when executing Terraform command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(rc, out, err),
                command=' '.join(command)
            )

    outputs_command = [command[0], 'output', '-no-color', '-json'] + _state_args(state_file, project_path, False)
    rc, outputs_text, outputs_err = module.run_command(outputs_command, cwd=project_path)
    if rc == 1:
        module.warn("Could not get Terraform outputs. This usually means none have been defined.\nstdout: {0}\nstderr: {1}".format(outputs_text, outputs_err))
        outputs = {}
    elif rc != 0:
        module.fail_json(
            msg="Failure when getting Terraform outputs. "
                "Exited {0}.\nstdout: {1}\nstderr: {2}".format(rc, outputs_text, outputs_err),
            command=' '.join(outputs_command))
    else:
        outputs = json.loads(outputs_text)

    # Restore the Terraform workspace found when running the module
    if workspace_ctx["current"] != workspace:
        select_workspace(command[0], project_path, workspace_ctx["current"])
    if state == 'absent' and workspace != 'default' and purge_workspace is True:
        remove_workspace(command[0], project_path, workspace)

    module.exit_json(changed=changed, state=state, workspace=workspace, outputs=outputs, stdout=out, stderr=err, command=' '.join(command))


if __name__ == '__main__':
    main()
