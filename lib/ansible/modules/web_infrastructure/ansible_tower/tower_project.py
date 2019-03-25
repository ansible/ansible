#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2017, Wayne Witzel III <wayne@riotousliving.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
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
    description:
      description:
        - Description to use for the project.
    scm_type:
      description:
        - Type of SCM resource.
      choices: ["manual", "git", "hg", "svn"]
      default: "manual"
    scm_url:
      description:
        - URL of SCM resource.
    local_path:
      description:
        - The server playbook directory for manual projects.
    scm_branch:
      description:
        - The branch to use for the SCM resource.
    scm_credential:
      description:
        - Name of the credential to use with this SCM resource.
    scm_clean:
      description:
        - Remove local modifications before updating.
      type: bool
      default: 'no'
    scm_delete_on_update:
      description:
        - Remove the repository completely before updating.
      type: bool
      default: 'no'
    scm_update_on_launch:
      description:
        - Before an update to the local repository before launching a job with this project.
      type: bool
      default: 'no'
    scm_update_cache_timeout:
      version_added: "2.8"
      description:
        - Cache Timeout to cache prior project syncs for a certain number of seconds.
            Only valid if scm_update_on_launch is to True, otherwise ignored.
      default: 0
    job_timeout:
      version_added: "2.8"
      description:
        - The amount of time (in seconds) to run before the SCM Update is canceled. A value of 0 means no timeout.
      default: 0
    custom_virtualenv:
      version_added: "2.8"
      description:
        - Local absolute file path containing a custom Python virtualenv to use
    organization:
      description:
        - Primary key of organization for project.
    state:
      description:
        - Desired state of the resource.
      default: "present"
      choices: ["present", "absent"]
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Add tower project
  tower_project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    state: present
    tower_config_file: "~/tower_cli.cfg"

- name: Add Tower Project with cache timeout and custom virtualenv
  tower_project:
    name: "Foo"
    description: "Foo bar project"
    organization: "test"
    scm_update_on_launch: True
    scm_update_cache_timeout: 60
    custom_virtualenv: "/var/lib/awx/venv/ansible-2.2"
    state: present
    tower_config_file: "~/tower_cli.cfg"
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
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
        scm_update_cache_timeout=dict(type='int', default=0),
        job_timeout=dict(type='int', default=0),
        custom_virtualenv=dict(),
        local_path=dict(),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    module = TowerModule(argument_spec=argument_spec, supports_check_mode=True)

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
    scm_update_cache_timeout = module.params.get('scm_update_cache_timeout')
    job_timeout = module.params.get('job_timeout')
    custom_virtualenv = module.params.get('custom_virtualenv')
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

                if scm_credential:
                    try:
                        cred_res = tower_cli.get_resource('credential')
                        try:
                            cred = cred_res.get(name=scm_credential)
                        except (tower_cli.exceptions.MultipleResults) as multi_res_excinfo:
                            module.warn('Multiple credentials found for {0}, falling back looking in project organization'.format(scm_credential))
                            cred = cred_res.get(name=scm_credential, organization=org['id'])
                        scm_credential = cred['id']
                    except (exc.NotFound) as excinfo:
                        module.fail_json(msg='Failed to update project, credential not found: {0}'.format(scm_credential), changed=False)

                if (scm_update_cache_timeout is not None) and (scm_update_on_launch is not True):
                    module.warn('scm_update_cache_timeout will be ignored since scm_update_on_launch was not set to true')

                result = project.modify(name=name, description=description,
                                        organization=org['id'],
                                        scm_type=scm_type, scm_url=scm_url, local_path=local_path,
                                        scm_branch=scm_branch, scm_clean=scm_clean, credential=scm_credential,
                                        scm_delete_on_update=scm_delete_on_update,
                                        scm_update_on_launch=scm_update_on_launch,
                                        scm_update_cache_timeout=scm_update_cache_timeout,
                                        job_timeout=job_timeout,
                                        custom_virtualenv=custom_virtualenv,
                                        create_on_missing=True)
                json_output['id'] = result['id']
            elif state == 'absent':
                result = project.delete(name=name)
        except (exc.ConnectionError, exc.BadRequest, exc.AuthError) as excinfo:
            module.fail_json(msg='Failed to update project: {0}'.format(excinfo), changed=False)

    json_output['changed'] = result['changed']
    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
