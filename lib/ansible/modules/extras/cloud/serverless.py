#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Ryan Scott Brown <ryansb@redhat.com>
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

DOCUMENTATION = '''
---
module: serverless
short_description: Manages a Serverless Framework project
description:
     - Provides support for managing Serverless Framework (https://serverless.com/) project deployments and stacks.
version_added: "2.3"
options:
  state:
    choices: ['present', 'absent']
    description:
      - Goal state of given stage/project
    required: false
    default: present
  service_path:
    description:
      - The path to the root of the Serverless Service to be operated on.
    required: true
  functions:
    description:
      - A list of specific functions to deploy. If this is not provided, all functions in the service will be deployed.
    required: false
    default: []
  region:
    description:
      - AWS region to deploy the service to
    required: false
    default: us-east-1
  deploy:
    description:
      - Whether or not to deploy artifacts after building them. When this option is `false` all the functions will be built, but no stack update will be run to send them out. This is mostly useful for generating artifacts to be stored/deployed elsewhere.
    required: false
    default: true
notes:
   - Currently, the `serverless` command must be in the path of the node executing the task. In the future this may be a flag.
requirements: [ "serverless" ]
author: "Ryan Scott Brown @ryansb"
'''

EXAMPLES = """
# Basic deploy of a service
- serverless: service_path={{ project_dir }} state=present

# Deploy specific functions
- serverless:
    service_path: "{{ project_dir }}"
    functions:
      - my_func_one
      - my_func_two

# deploy a project, then pull its resource list back into Ansible
- serverless:
    stage: dev
    region: us-east-1
    service_path: "{{ project_dir }}"
  register: sls
# The cloudformation stack is always named the same as the full service, so the
# cloudformation_facts module can get a full list of the stack resources, as
# well as stack events and outputs
- cloudformation_facts:
    region: us-east-1
    stack_name: "{{ sls.service_name }}"
    stack_resources: true
"""

RETURN = """
service_name:
  type: string
  description: Most
  returned: always
  sample: my-fancy-service-dev
state:
  type: string
  description: Whether the stack for the serverless project is present/absent.
  returned: always
command:
  type: string
  description: Full `serverless` command run by this module, in case you want to re-run the command outside the module.
  returned: always
  sample: serverless deploy --stage production
"""


import os
import traceback
import yaml


def read_serverless_config(module):
    path = os.path.expanduser(module.params.get('service_path'))

    try:
        with open(os.path.join(path, 'serverless.yml')) as sls_config:
            config = yaml.safe_load(sls_config.read())
            return config
    except IOError as e:
        module.fail_json(msg="Could not open serverless.yml in {}. err: {}".format(path, str(e)), exception=traceback.format_exc())

    module.fail_json(msg="Failed to open serverless config at {}".format(
        os.path.join(path, 'serverless.yml')))


def get_service_name(module, stage):
    config = read_serverless_config(module)
    if config.get('service') is None:
        module.fail_json(msg="Could not read `service` key from serverless.yml file")

    if stage:
        return "{}-{}".format(config['service'], stage)

    return "{}-{}".format(config['service'], config.get('stage', 'dev'))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_path = dict(required=True),
            state        = dict(default='present', choices=['present', 'absent'], required=False),
            functions    = dict(type='list', required=False),
            region       = dict(default='', required=False),
            stage        = dict(default='', required=False),
            deploy       = dict(default=True, type='bool', required=False),
        ),
    )

    service_path = os.path.expanduser(module.params.get('service_path'))
    state = module.params.get('state')
    functions = module.params.get('functions')
    region = module.params.get('region')
    stage = module.params.get('stage')
    deploy = module.params.get('deploy', True)

    command = "serverless "
    if state == 'present':
        command += 'deploy '
    elif state == 'absent':
        command += 'remove '
    else:
        module.fail_json(msg="State must either be 'present' or 'absent'. Received: {}".format(state))

    if not deploy and state == 'present':
        command += '--noDeploy '
    if region:
        command += '--region {} '.format(region)
    if stage:
        command += '--stage {} '.format(stage)

    rc, out, err = module.run_command(command, cwd=service_path)
    if rc != 0:
        if state == 'absent' and "-{}' does not exist".format(stage) in out:
            module.exit_json(changed=False, state='absent', command=command,
                    out=out, service_name=get_service_name(module, stage))

        module.fail_json(msg="Failure when executing Serverless command. Exited {}.\nstdout: {}\nstderr: {}".format(rc, out, err))

    # gather some facts about the deployment
    module.exit_json(changed=True, state='present', out=out, command=command,
            service_name=get_service_name(module, stage))

# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
