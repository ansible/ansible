#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_credential
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower credential.
description:
    - Create, update, or destroy Ansible Tower credentials. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - The name to use for the credential.
      required: True
    description:
      description:
        - The description to use for the credential.
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
      choices: ["ssh", "net", "scm", "aws", "rax", "vmware", "satellite6", "cloudforms", "gce", "azure", "azure_rm", "openstack"]
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
      choices: ["None", "sudo", "su", "pbrun", "pfexec", "pmrun"]
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
    tower_host:
      description:
        - URL to your Tower instance.
      required: False
      default: null
    tower_username:
        description:
          - Username for your Tower instance.
        required: False
        default: null
    tower_password:
        description:
          - Password for your Tower instance.
        required: False
        default: null
    tower_verify_ssl:
        description:
          - Dis/allow insecure connections to Tower. If C(no), SSL certificates will not be validated.
            This should only be used on personally controlled sites using self-signed certificates.
        required: False
        default: True
    tower_config_file:
      description:
        - Path to the Tower config file. See notes.
      required: False
      default: null


requirements:
  - "python >= 2.6"
  - "ansible-tower-cli >= 3.0.2"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
- name: Add tower credential
  tower_credential:
    name: Team Name
    description: Team Description
    organization: test-org
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

try:
    import os
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
    from ansible.module_utils.ansible_tower import tower_auth_config, tower_check_mode

    HAS_TOWER_CLI = True
except ImportError:
    HAS_TOWER_CLI = False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            user=dict(),
            team=dict(),
            kind=dict(required=True,
                      choices=["ssh", "net", "scm", "aws", "rax", "vmware", "satellite6",
                               "cloudforms", "gce", "azure", "azure_rm", "openstack"]),
            host=dict(),
            username=dict(),
            password=dict(no_log=True),
            ssh_key_data=dict(no_log=True),
            ssh_key_unlock=dict(no_log=True),
            authorize=dict(type='bool', default=False),
            authorize_password=dict(no_log=True),
            client=dict(),
            secret=dict(),
            tenant=dict(),
            subscription=dict(),
            domain=dict(),
            become_method=dict(),
            become_username=dict(),
            become_password=dict(no_log=True),
            vault_password=dict(no_log=True),
            description=dict(),
            organization=dict(required=True),
            project=dict(),
            tower_host=dict(),
            tower_username=dict(),
            tower_password=dict(no_log=True),
            tower_verify_ssl=dict(type='bool', default=True),
            tower_config_file=dict(type='path'),
            state=dict(choices=['present', 'absent'], default='present'),
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
        tower_check_mode(module)
        credential = tower_cli.get_resource('credential')
        try:
            params = module.params.copy()
            params['create_on_missing'] = True

            if organization:
                org_res = tower_cli.get_resource('organization')
                org = org_res.get(name=organization)
                params['organization'] = org['id']

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
            module.fail_json(msg='Failed to update credential, organization not found: {0}'.format(excinfo), changed=False)
        except (exc.ConnectionError, exc.BadRequest, exc.NotFound) as excinfo:
            module.fail_json(msg='Failed to update credential: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
