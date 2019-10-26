#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2016, Ryan Scott Brown <ryansb@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: serverless
short_description: Manages a Serverless Framework project
description:
     - Provides support for managing Serverless Framework (https://serverless.com/) project deployments and stacks.
version_added: "2.3"
options:
  state:
    description:
      - Goal state of given stage/project.
    type: str
    choices: [ absent, present ]
    default: present
  serverless_bin_path:
    description:
      - The path of a serverless framework binary relative to the 'service_path' eg. node_module/.bin/serverless
    type: path
    version_added: "2.4"
  service_path:
    description:
      - The path to the root of the Serverless Service to be operated on.
    type: path
    required: true
  stage:
    description:
      - The name of the serverless framework project stage to deploy to.
      - This uses the serverless framework default "dev".
    type: str
  functions:
    description:
      - A list of specific functions to deploy.
      - If this is not provided, all functions in the service will be deployed.
    type: list
    default: []
  region:
    description:
      - AWS region to deploy the service to.
      - This parameter defaults to C(us-east-1).
    type: str
  deploy:
    description:
      - Whether or not to deploy artifacts after building them.
      - When this option is C(false) all the functions will be built, but no stack update will be run to send them out.
      - This is mostly useful for generating artifacts to be stored/deployed elsewhere.
    type: bool
    default: yes
  force:
    description:
      - Whether or not to force full deployment, equivalent to serverless C(--force) option.
    type: bool
    default: no
    version_added: "2.7"
  verbose:
    description:
      - Shows all stack events during deployment, and display any Stack Output.
    type: bool
    default: no
    version_added: "2.7"
notes:
   - Currently, the C(serverless) command must be in the path of the node executing the task.
     In the future this may be a flag.
requirements:
- serverless
- yaml
author:
- Ryan Scott Brown (@ryansb)
'''

EXAMPLES = r'''
- name: Basic deploy of a service
  serverless:
    service_path: '{{ project_dir }}'
    state: present

- name: Deploy specific functions
  serverless:
    service_path: '{{ project_dir }}'
    functions:
      - my_func_one
      - my_func_two

- name: Deploy a project, then pull its resource list back into Ansible
  serverless:
    stage: dev
    region: us-east-1
    service_path: '{{ project_dir }}'
  register: sls

# The cloudformation stack is always named the same as the full service, so the
# cloudformation_info module can get a full list of the stack resources, as
# well as stack events and outputs
- cloudformation_info:
    region: us-east-1
    stack_name: '{{ sls.service_name }}'
    stack_resources: true

- name: Deploy a project using a locally installed serverless binary
  serverless:
    stage: dev
    region: us-east-1
    service_path: '{{ project_dir }}'
    serverless_bin_path: node_modules/.bin/serverless
'''

RETURN = r'''
service_name:
  type: str
  description: The service name specified in the serverless.yml that was just deployed.
  returned: always
  sample: my-fancy-service-dev
state:
  type: str
  description: Whether the stack for the serverless project is present/absent.
  returned: always
command:
  type: str
  description: Full `serverless` command run by this module, in case you want to re-run the command outside the module.
  returned: always
  sample: serverless deploy --stage production
'''

import os

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from ansible.module_utils.basic import AnsibleModule


def read_serverless_config(module):
    path = module.params.get('service_path')

    try:
        with open(os.path.join(path, 'serverless.yml')) as sls_config:
            config = yaml.safe_load(sls_config.read())
            return config
    except IOError as e:
        module.fail_json(msg="Could not open serverless.yml in {0}. err: {1}".format(path, str(e)))

    module.fail_json(msg="Failed to open serverless config at {0}".format(
        os.path.join(path, 'serverless.yml')))


def get_service_name(module, stage):
    config = read_serverless_config(module)
    if config.get('service') is None:
        module.fail_json(msg="Could not read `service` key from serverless.yml file")

    if stage:
        return "{0}-{1}".format(config['service'], stage)

    return "{0}-{1}".format(config['service'], config.get('stage', 'dev'))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_path=dict(type='path', required=True),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            functions=dict(type='list'),
            region=dict(type='str', default=''),
            stage=dict(type='str', default=''),
            deploy=dict(type='bool', default=True),
            serverless_bin_path=dict(type='path'),
            force=dict(type='bool', default=False),
            verbose=dict(type='bool', default=False),
        ),
    )

    if not HAS_YAML:
        module.fail_json(msg='yaml is required for this module')

    service_path = module.params.get('service_path')
    state = module.params.get('state')
    functions = module.params.get('functions')
    region = module.params.get('region')
    stage = module.params.get('stage')
    deploy = module.params.get('deploy', True)
    force = module.params.get('force', False)
    verbose = module.params.get('verbose', False)
    serverless_bin_path = module.params.get('serverless_bin_path')

    if serverless_bin_path is not None:
        command = serverless_bin_path + " "
    else:
        command = "serverless "

    if state == 'present':
        command += 'deploy '
    elif state == 'absent':
        command += 'remove '
    else:
        module.fail_json(msg="State must either be 'present' or 'absent'. Received: {0}".format(state))

    if state == 'present':
        if not deploy:
            command += '--noDeploy '
        elif force:
            command += '--force '

    if region:
        command += '--region {0} '.format(region)
    if stage:
        command += '--stage {0} '.format(stage)
    if verbose:
        command += '--verbose '

    rc, out, err = module.run_command(command, cwd=service_path)
    if rc != 0:
        if state == 'absent' and "-{0}' does not exist".format(stage) in out:
            module.exit_json(changed=False, state='absent', command=command,
                             out=out, service_name=get_service_name(module, stage))

        module.fail_json(msg="Failure when executing Serverless command. Exited {0}.\nstdout: {1}\nstderr: {2}".format(rc, out, err))

    # gather some facts about the deployment
    module.exit_json(changed=True, state='present', out=out, command=command,
                     service_name=get_service_name(module, stage))


if __name__ == '__main__':
    main()
