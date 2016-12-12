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
module: tower_credential
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower credential.
description:
    - Create, update, or destroy Ansible Tower credentials. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name string to use for the credential.
      required: True
      default: null
    description:
      description:
        - Description of the credential.
    user:
      description:
        - User that should own this credential.
      required: False
      default: null
    team:
      description:
        - Team that should own this credential.
      required: False
      default: null
    project:
      description:
        - Project that should for this credential.
      required: False
      default: null
    organization:
      description:
        - Organization that should own the credential.
      required: False
      default: null
    kind:
      description:
        - Type of credential being added.
      required: True
      choices: ["ssh", "net", "scm", "aws", "rax", "vmware", "foreman", "cloudforms", "gce", "azure", "azure_rm", "openstack"]
    host:
      description:
        - Host for this credential.
      required: False
      default: null
    username:
      description:
        - Username for this credential. access_key for AWS.
      required: False
      default: null
    password:
      description:
        - Password for this credential. Use ASK for prompting. secret_key for AWS. api_key for RAX.
      required: False
      default: null
    ssh_key_data:
      description:
        - Path to SSH private key.
      required: False
      default: null
    ssh_key_unlock:
      description:
        - Unlock password for ssh_key. Use ASK for prompting.
    authorize:
      description:
        - Should use authroize for net type.
      required: False
      default: False
    authorize_password:
      description:
        - Password for net credentials that require authroize.
      required: False
      default: null
    client:
      description:
        - Client or application ID for azure_rm type.
      required: False
      default: null
    secret:
      description:
        - Secret token for azure_rm type.
      required: False
      default: null
    subscription:
      description:
        - Subscription ID for azure_rm type.
      required: False
      default: null
    tenant:
      description:
        - Tenant ID for azure_rm type.
      required: False
      default: null
    domain:
      description:
        - Domain for openstack type.
      required: False
      default: null
    become_method:
      description:
        - Become method to Use for privledge escalation.
      required: False
      choices: ["None", "sudo", "su", "pbrun", "pfexec"]
      default: "None"
    become_username:
      description:
        - Become username. Use ASK for prompting.
      required: False
      default: null
    become_password:
      description:
        - Become password. Use ASK for prompting.
      required: False
      default: null
    vault_password:
      description:
        - Valut password. Use ASK for prompting.
    state:
      description:
        - Desired state of the resource.
      required: False
      default: "present"
      choices: ["present", "absent"]
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
    tower_credential:
        name: Team Name
        description: Team Description
        organization: test-org
        state: present
        config_file: "~/tower_cli.cfg"
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
            name = dict(required=True),
            user = dict(),
            team = dict(),
            kind = dict(required=True,
                        choices=["ssh", "net", "scm", "aws", "rax", "vmware", "foreman",
                                 "cloudforms", "gce", "azure", "azure_rm", "openstack"]),
            host = dict(),
            username = dict(),
            password = dict(no_log=True),
            ssh_key_data = dict(no_log=True),
            ssh_key_unlock = dict(no_log=True),
            authorize = dict(type='bool', default=False),
            authorize_password = dict(no_log=True),
            client = dict(),
            secret = dict(),
            tenant = dict(),
            domain = dict(),
            become_method = dict(),
            become_username = dict(),
            become_password = dict(no_log=True),
            vault_password = dict(no_log=True),
            description = dict(),
            organization = dict(required=True),
            project = dict(),
            config_file = dict(),
            state = dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    if not HAS_TOWER_CLI:
        module.fail_json(msg='ansible-tower-cli required for this module')

    name = module.params.get('name')
    organization = module.params.get('organization')
    state = module.params.get('state')

    json_output = {'credential': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        credential = tower_cli.get_resource('credential')
        try:
            params = module.params.copy()
            params['create_on_missing'] = True

            if organization:
                org_res = tower_cli.get_resource('organization')
                org = org_res.get(name=organization)
                params['organization'] = org['id']

            if module.check_mode:
                try:
                    credential.get(name=params.get('name'), kind=params.get('kind'),
                                   organization=params.get('organization'))
                    changed=False if state == 'present' else True
                except exc.NotFound:
                    changed=False if state == 'absent' else True

                module.exit_json(changed=changed)

            if params['ssh_key_data']:
                filename = params['ssh_key_data']
                filename = os.path.expanduser(filename)
                if not os.path.exists(filename):
                    module.fail_json(msg='file not found: %s' % filename)
                if os.path.isdir(filename):
                    module.fail_json(msg='attempted to read contents of directory: %s' % filename)
                with open(filename, 'rb') as f:
                    params['ssh_key_data'] = f.read()

            if state == 'present':
                result = credential.modify(**params)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = credential.delete(**params)
        except (exc.NotFound) as excinfo:
            module.fail_json(msg='{} Organization {}'.format(excinfo, organization), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='{}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
