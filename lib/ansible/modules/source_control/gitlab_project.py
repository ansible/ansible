#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Guillaume Martinez (guillaume.lunik@gmail.com)
# Copyright: (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gitlab_project
short_description: Creates/updates/deletes Gitlab Projects
description:
  - When the project does not exist in Gitlab, it will be created.
  - When the project does exists and state=absent, the project will be deleted.
  - When changes are made to the project, the project will be updated.
version_added: "2.1"
author:
  - Werner Dijkerman (@dj-wasabi)
  - Guillaume Martinez (@Lunik)
requirements:
  - python >= 2.7
  - python-gitlab python module
options:
  server_url:
    description:
      - The URL of the Gitlab server, with protocol (i.e. http or https).
    required: true
    type: str
  validate_certs:
    description:
      - When using https if SSL certificate needs to be verified.
    type: bool
    default: yes
    aliases:
      - verify_ssl
  login_user:
    description:
      - Gitlab user name.
    type: str
  login_password:
    description:
      - Gitlab password for login_user
    type: str
  login_token:
    description:
      - Gitlab token for logging in.
    type: str
  group:
    description:
      - Id or The full path of the group of which this projects belongs to.
    type: str
  name:
    description:
      - The name of the project
    required: true
    type: str
  path:
    description:
      - The path of the project you want to create, this will be server_url/<group>/path
      - If not supplied, name will be used.
    type: str
  description:
    description:
      - An description for the project.
    type: str
  issues_enabled:
    description:
      - Whether you want to create issues or not.
      - Possible values are true and false.
    type: bool
    default: yes
  merge_requests_enabled:
    description:
      - If merge requests can be made or not.
      - Possible values are true and false.
    type: bool
    default: yes
  wiki_enabled:
    description:
      - If an wiki for this project should be available or not.
      - Possible values are true and false.
    type: bool
    default: yes
  snippets_enabled:
    description:
      - If creating snippets should be available or not.
      - Possible values are true and false.
    type: bool
    default: yes
  visibility:
    description:
      - Private. Project access must be granted explicitly for each user.
      - Internal. The project can be cloned by any logged in user.
      - Public. The project can be cloned without any authentication.
    default: private
    type: str
    choices: ["private", "internal", "public"]
    aliases:
      - visibility_level
  import_url:
    description:
      - Git repository which will be imported into gitlab.
      - Gitlab server needs read access to this git repository.
    required: false
    type: str
  state:
    description:
      - create or delete project.
      - Possible values are present and absent.
    default: present
    type: str
    choices: ["present", "absent"]
'''

EXAMPLES = '''
- name: Delete Gitlab Project
  gitlab_project:
    server_url: http://gitlab.example.com
    validate_certs: False
    login_token: WnUzDsxjy8230-Dy_k
    name: my_first_project
    state: absent
  delegate_to: localhost

- name: Create Gitlab Project in group Ansible
  gitlab_project:
    server_url: https://gitlab.example.com
    validate_certs: True
    login_user: dj-wasabi
    login_password: MySecretPassword
    name: my_first_project
    group: ansible
    issues_enabled: False
    wiki_enabled: True
    snippets_enabled: True
    import_url: http://git.example.com/example/lab.git
    state: present
  delegate_to: localhost
'''

RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: str
  sample: "Success"

result:
  description: json parsed response from the server
  returned: always
  type: dict

error:
  description: the error message returned by the Gitlab API
  returned: failed
  type: str
  sample: "400: path is already in use"

project:
  description: API object
  returned: always
  type: dict
'''

import os

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except Exception:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native

from ansible.module_utils.gitlab import findGroup, findProject


class GitLabProject(object):
    def __init__(self, module, gitlab_instance):
        self._module = module
        self._gitlab = gitlab_instance
        self.projectObject = None

    '''
    @param project_name Name of the project
    @param namespace Namespace Object (User or Group)
    @param options Options of the project
    '''
    def createOrUpdateProject(self, project_name, namespace, options):
        changed = False

        # Because we have already call userExists in main()
        if self.projectObject is None:
            project = self.createProject(namespace, {
                'name': project_name,
                'path': options['path'],
                'description': options['description'],
                'issues_enabled': options['issues_enabled'],
                'merge_requests_enabled': options['merge_requests_enabled'],
                'wiki_enabled': options['wiki_enabled'],
                'snippets_enabled': options['snippets_enabled'],
                'visibility': options['visibility'],
                'import_url': options['import_url']})
            changed = True
        else:
            changed, project = self.updateProject(self.projectObject, {
                'name': project_name,
                'description': options['description'],
                'issues_enabled': options['issues_enabled'],
                'merge_requests_enabled': options['merge_requests_enabled'],
                'wiki_enabled': options['wiki_enabled'],
                'snippets_enabled': options['snippets_enabled'],
                'visibility': options['visibility']})

        self.projectObject = project
        if changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Project should have been updated.")

            try:
                project.save()
            except Exception as e:
                self._module.fail_json(msg="Failed update a project: %s " % e)
            return True
        else:
            return False

    '''
    @param namespace Namespace Object (User or Group)
    @param arguments Attributs of the project
    '''
    def createProject(self, namespace, arguments):
        if self._module.check_mode:
                self._module.exit_json(changed=True, msg="Project should have been created.")

        arguments['namespace_id'] = namespace.id
        try:
            project = self._gitlab.projects.create(arguments)
        except (gitlab.exceptions.GitlabCreateError) as e:
            self._module.fail_json(msg="Failed to create a project: %s " % to_native(e))

        return project

    '''
    @param project Project Object
    @param arguments Attributs of the project
    '''
    def updateProject(self, project, arguments):
        changed = False

        for arg_key, arg_value in arguments.items():
            if arguments[arg_key] is not None:
                if getattr(project, arg_key) != arguments[arg_key]:
                    setattr(project, arg_key, arguments[arg_key])
                    changed = True

        return (changed, project)

    def deleteProject(self):
        if self._module.check_mode:
            self._module.exit_json(changed=True, msg="Project should have been deleted.")

        project = self.projectObject

        return project.delete()

    '''
    @param namespace User/Group object
    @param name Name of the project
    '''
    def existsProject(self, namespace, path):
        # When project exists, object will be stored in self.projectObject.
        project = findProject(self._gitlab, namespace.full_path + '/' + path)
        if project:
            self.projectObject = project
            return True
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True),
            validate_certs=dict(type='bool', default=True, aliases=["verify_ssl"]),
            login_user=dict(type='str', no_log=True),
            login_password=dict(rtype='str', no_log=True),
            login_token=dict(type='str', no_log=True),
            group=dict(type='str'),
            name=dict(type='str', required=True),
            path=dict(type='str'),
            description=dict(type='str'),
            issues_enabled=dict(type='bool', default=True),
            merge_requests_enabled=dict(type='bool', default=True),
            wiki_enabled=dict(type='bool', default=True),
            snippets_enabled=dict(default=True, type='bool'),
            visibility=dict(type='str', default="private", choices=["internal", "private", "public"], aliases=["visibility_level"]),
            import_url=dict(type='str'),
            state=dict(type='str', default="present", choices=["absent", "present"]),
        ),
        mutually_exclusive=[
            ['login_user', 'login_token'],
            ['login_password', 'login_token']
        ],
        required_together=[
            ['login_user', 'login_password']
        ],
        required_one_of=[
            ['login_user', 'login_token']
        ],
        supports_check_mode=True,
    )

    server_url = module.params['server_url']
    validate_certs = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    group_identifier = module.params['group']
    project_name = module.params['name']
    project_path = module.params['path']
    project_description = module.params['description']
    issues_enabled = module.params['issues_enabled']
    merge_requests_enabled = module.params['merge_requests_enabled']
    wiki_enabled = module.params['wiki_enabled']
    snippets_enabled = module.params['snippets_enabled']
    visibility = module.params['visibility']
    import_url = module.params['import_url']
    state = module.params['state']

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    try:
        gitlab_instance = gitlab.Gitlab(url=server_url, ssl_verify=validate_certs, email=login_user, password=login_password,
                                        private_token=login_token, api_version=4)
        gitlab_instance.auth()
    except (gitlab.exceptions.GitlabAuthenticationError, gitlab.exceptions.GitlabGetError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s" % to_native(e))
    except (gitlab.exceptions.GitlabHttpError) as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s. \
            Gitlab remove Session API now that private tokens are removed from user API endpoints since version 10.2." % to_native(e))

    # Set project_path to project_name if it is empty.
    if project_path is None:
        project_path = project_name.replace(" ", "_")

    gitlab_project = GitLabProject(module, gitlab_instance)

    if group_identifier:
        group = findGroup(gitlab_instance, group_identifier)
        if group is None:
            module.fail_json(msg="Failed to create project: group %s doesn't exists" % group_identifier)

        namespace = gitlab_instance.namespaces.get(group.id)
        project_exists = gitlab_project.existsProject(namespace, project_path)
    else:
        user = gitlab_instance.users.list(username=gitlab_instance.user.username)[0]
        namespace = gitlab_instance.namespaces.get(user.id)
        project_exists = gitlab_project.existsProject(namespace, project_path)

    if state == 'absent':
        if project_exists:
            gitlab_project.deleteProject()
            module.exit_json(changed=True, msg="Successfully deleted project %s" % project_name)
        else:
            module.exit_json(changed=False, msg="Project deleted or does not exists")

    if state == 'present':
        if gitlab_project.createOrUpdateProject(project_name, namespace, {
                                                "path": project_path,
                                                "description": project_description,
                                                "issues_enabled": issues_enabled,
                                                "merge_requests_enabled": merge_requests_enabled,
                                                "wiki_enabled": wiki_enabled,
                                                "snippets_enabled": snippets_enabled,
                                                "visibility": visibility,
                                                "import_url": import_url}):

            module.exit_json(changed=True, msg="Successfully created or updated the project %s" % project_name, project=gitlab_project.projectObject._attrs)
        else:
            module.exit_json(changed=False, msg="No need to update the project %s" % project_name, project=gitlab_project.projectObject._attrs)


if __name__ == '__main__':
    main()
