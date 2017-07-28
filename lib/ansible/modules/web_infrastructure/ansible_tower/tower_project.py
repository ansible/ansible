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
module: tower_project
author: "Wayne Witzel III (@wwitzel3)"
version_added: "2.3"
short_description: create, update, or destroy Ansible Tower projects
description:
    - Create, update, or destroy Ansible Tower projects. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name to use for the project.
      required: True
      default: null
    description:
      description:
        - Description to use for the project.
      required: False
      default: null
    scm_type:
      description:
        - Type of scm resource.
      required: False
      default: "manual"
      choices: ["manual", "git", "hg", "svn"]
    scm_url:
      description:
        - URL of scm resource.
      required: False
      default: null
    local_path:
      description:
        - The server playbook directory for manual projects.
      required: False
      default: null
    scm_branch:
      description:
        - The branch to use for the scm resource.
      required: False
      default: null
    scm_credential:
      description:
        - Name of the credential to use with this scm resource.
      required: False
      default: null
    scm_clean:
      description:
        - Remove local modifications before updating.
      required: False
      default: False
    scm_delete_on_update:
      description:
        - Remove the repository completely before updating.
      required: False
      default: False
    scm_update_on_launch:
      description:
        - Before an update to the local repository before launching a job with this project.
      required: False
      default: False
    organization:
      description:
        - Primary key of organization for project.
      required: False
      default: null
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
  - "ansible-tower-cli >= 3.0.3"

notes:
  - If no I(config_file) is provided we will attempt to use the tower-cli library
    defaults to find your Tower host information.
  - I(config_file) should contain Tower configuration in the following format
      host=hostname
      username=username
      password=password
'''


EXAMPLES = '''
- name: Add tower project
  tower_project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

try:
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
            name=dict(),
            description=dict(),
            organization=dict(),
            scm_type=dict(choices=['manual', 'git', 'hg', 'svn'], default='manual'),
            scm_url=dict(),
            scm_branch=dict(),
            scm_credential=dict(),
            scm_clean=dict(type='bool', default=False),
            scm_delete_on_update=dict(type='bool', default=False),
            scm_update_on_launch=dict(type='bool', default=False),
            local_path=dict(),
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
    description = module.params.get('description')
    organization = module.params.get('organization')
    scm_type = module.params.get('scm_type')
    if scm_type == "manual":
        scm_type = ""
    scm_url = module.params.get('scm_url')
    local_path = module.params.get('local_path')
    scm_branch = module.params.get('scm_branch')
    scm_credential = module.params.get('scm_credential')
    scm_clean = module.params.get('scm_clean')
    scm_delete_on_update = module.params.get('scm_delete_on_update')
    scm_update_on_launch = module.params.get('scm_update_on_launch')
    state = module.params.get('state')

    json_output = {'project': name, 'state': state}

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        project = tower_cli.get_resource('project')
        try:
            if state == 'present':
                try:
                    org_res = tower_cli.get_resource('organization')
                    org = org_res.get(name=organization)
                except (exc.NotFound) as excinfo:
                    module.fail_json(msg='Failed to update project, organization not found: {0}'.format(organization), changed=False)
                try:
                    cred_res = tower_cli.get_resource('credential')
                    cred = cred_res.get(name=scm_credential)
                except (exc.NotFound) as excinfo:
                    module.fail_json(msg='Failed to update project, credential not found: {0}'.format(scm_credential), changed=False)

                result = project.modify(name=name, description=description,
                                        organization=org['id'],
                                        scm_type=scm_type, scm_url=scm_url, local_path=local_path,
                                        scm_branch=scm_branch, scm_clean=scm_clean, credential=cred['id'],
                                        scm_delete_on_update=scm_delete_on_update,
                                        scm_update_on_launch=scm_update_on_launch,
                                        create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = project.delete(name=name)
        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to update project: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
