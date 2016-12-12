#!/usr/bin/env python
#coding: utf-8 -*-

# (c) 2016, Wayne Witzel III <wayne@riotousliving.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: tower_job_launch
version_added: "2.3"
short_description: Launch an Ansible Job.
description:
    - Launch an Ansible Tower jobs. See
      U(https://www.ansible.com/tower) for an overview.
options:
    job_template:
      description:
        - Name string of the job_template.
      required: True
      default: null
    job_explanation:
      description:
        - Job explanation field.
      required: False
      default: null
    job_type:
      description:
        - Job_type to use for the job, only used if prompt for job_type is set.
      required: False
      choices: ["run", "check", "scan"]
      default: null
    inventory:
      description:
        - Inventory to use for the job, only used if prompt for inventory is set.
      required: False
      default: null
    credential:
      description:
        - Credential to use for job, only used if prompt for credential is set.
      required: False
      default: null
    extra_vars:
      description:
        - Extra_vars to use for the job_template. Use '@' for a file.
      required: False
      default: null
    limit:
      description:
        - Limit to use for the job_template.
      required: False
      default: null
    tags:
      description:
        - Specific tags to use for from playbook.
      required: False
      default: null
    use_job_endpoint:
      description:
        - Disable launching jobs from job template.
      required: False
      default: False
    config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "ansible-tower-cli >= 3.0.2"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format:
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
    tower_job_launch:
        job_template: "My Job Template"
        config_file: "~/tower_cli.cfg"
        register: job
    tower_job_wait:
        job_id: job.id
        timeout: 120
'''

import os

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc
    from tower_cli.utils import parser
    from tower_cli.conf import settings

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def tower_auth_config(module):
    config_file = module.params.get('config_file')
    if not config_file:
        return {}

    config_file = os.path.expanduser(config_file)
    if not os.path.exists(config_file):
        module.fail_json(msg='file not found: %s' % config_file)
    if os.path.isdir(config_file):
        module.fail_json(msg='directory can not be used as config file: %s' % config_file)

    with open(config_file, 'rb') as f:
        return parser.string_to_dict(f.read())


def main():
    module = AnsibleModule(
        argument_spec = dict(
            job_template = dict(required=True),
            job_type = dict(choices=['run', 'check', 'scan']),
            inventory = dict(),
            credential = dict(),
            limit = dict(),
            tags = dict(),
            extra_vars = dict(type='list', required=False),
            config_file = dict(),
        ),
        supports_check_mode=False
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    json_output = {}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        try:
            params = module.params.copy()
            job = tower_cli.get_resource('job')

            try:
                jt_name = params.pop('job_template')
                jt = tower_cli.get_resource('job_template').get(name=jt_name)
            except exc.NotFound as excinfo:
                module.fail_json(msg='{} job_template: {}'.format(excinfo, jt_name), changed=False)

            result = job.launch(jt['id'], no_input=True, **params)
            json_output['id'] = result['id']
            json_output['status'] = result['status']
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
