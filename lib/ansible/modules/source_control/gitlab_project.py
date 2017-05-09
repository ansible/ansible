#!/usr/bin/python
# (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: gitlab_project
short_description: Creates/updates/deletes Gitlab Projects
description:
   - When the project does not exists in Gitlab, it will be created.
   - When the project does exists and state=absent, the project will be deleted.
   - When changes are made to the project, the project will be updated.
version_added: "2.1"
author: "Werner Dijkerman (@dj-wasabi)"
requirements:
    - python-gitlab python module
options:
    server_url:
        description:
            - Url of Gitlab server, with protocol (http or https).
        required: true
    validate_certs:
        description:
            - When using https if SSL certificate needs to be verified.
        required: false
        default: true
        aliases:
            - verify_ssl
    login_user:
        description:
            - Gitlab user name.
        required: false
        default: null
    login_password:
        description:
            - Gitlab password for login_user
        required: false
        default: null
    login_token:
        description:
            - Gitlab token for logging in.
        required: false
        default: null
    group:
        description:
            - The name of the group of which this projects belongs to.
            - When not provided, project will belong to user which is configured in 'login_user' or 'login_token'
            - When provided with username, project will be created for this user. 'login_user' or 'login_token' needs admin rights.
        required: false
        default: null
    name:
        description:
            - The name of the project
        required: true
    path:
        description:
            - The path of the project you want to create, this will be server_url/<group>/path
            - If not supplied, name will be used.
        required: false
        default: null
    description:
        description:
            - An description for the project.
        required: false
        default: null
    issues_enabled:
        description:
            - Whether you want to create issues or not.
        required: false
        choices: ["true", "false"]
        default: true
    merge_requests_enabled:
        description:
            - If merge requests can be made or not.
        required: false
        choices: ["true", "false"]
        default: true
    wiki_enabled:
        description:
            - If an wiki for this project should be available or not.
        required: false
        choices: ["true", "false"]
        default: true
    builds_enabled:
        description:
            - If a build creation for this project should be available or not.
        choices: ["true", "false"]
        default: false
        version_added: "2.3"
    public_builds:
        description:
            - If true, builds can be viewed by non-project-members.
            - Will only work when C(builds_enabled=True).
        choices: ["true", "false"]
        default: false
        version_added: "2.3"
    only_allow_merge_if_build_succeeds:
        description:
            - Set whether merge requests can only be merged with successful builds.
            - Will only work when C(builds_enabled=True).
        choices: ["true", "false"]
        default: false
        version_added: "2.3"
    container_registry_enabled:
        description:
            - Enable container registry for this project.
            - Will only work when C(builds_enabled=True).
        choices: ["true", "false"]
        default: false
        version_added: "2.3"
    snippets_enabled:
        description:
            - If creating snippets should be available or not.
        required: false
        choices: ["true", "false"]
        default: true
    public:
        description:
            - If the project is public available or not.
            - Setting this to true is same as setting visibility_level to 20.
            - Possible values are true and false.
        required: false
        choices: ["true", "false"]
        default: false
    visibility_level:
        description:
            - Private. visibility_level is 0. Project access must be granted explicitly for each user.
            - Internal. visibility_level is 10. The project can be cloned by any logged in user.
            - Public. visibility_level is 20. The project can be cloned without any authentication.
            - Possible values are 0, 10 and 20.
        required: false
        choices: [0, 10, 20]
        default: 0
    import_url:
        description:
            - Git repository which will be imported into gitlab.
            - Gitlab server needs read access to this git repository.
        required: false
        default: false
    state:
        description:
            - create or delete project.
            - Possible values are present and absent.
        required: false
        default: "present"
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

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception


class GitLabProject(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.groupObject = None

    def createOrUpdateProject(self, project, name, group_id, issues, wiki, merge_request, description,
                              snippets, builds, public_builds, public, only_allow_merge_if_build_succeeds,
                              container_registry_enabled, visibility_level, import_url, path):
        """Create or update a project."""
        changed = False
        if not project:
            project = self.createProject(name=name, group_id=group_id, import_url=import_url)

        if project.path != path:
            project.path = path
            changed = True
        if project.wiki_enabled != wiki:
            project.wiki_enabled = wiki
            changed = True
        if project.issues_enabled != issues:
            project.issues_enabled = issues
            changed = True
        if project.merge_requests_enabled != merge_request:
            project.merge_requests_enabled = merge_request
            changed = True
        if project.snippets_enabled != snippets:
            project.snippets_enabled = snippets
            changed = True
        if project.builds_enabled != builds:
            project.builds_enabled = builds
            changed = True
            if project.public_builds != public_builds:
                project.public_builds = public_builds
                changed = True
            if project.only_allow_merge_if_build_succeeds != only_allow_merge_if_build_succeeds:
                project.only_allow_merge_if_build_succeeds = only_allow_merge_if_build_succeeds
                changed = True
            if project.container_registry_enabled != container_registry_enabled:
                project.container_registry_enabled = container_registry_enabled
                changed = True
        if project.description != description:
            project.description = description
            changed = True
        if project.public != public:
            project.public = public
            changed = True
        if project.visibility_level != visibility_level:
            project.visibility_level = int(visibility_level)

        if changed:
            if self._module.check_mode:
                module.exit_json(changed=True, result="Project should have updated.")
            try:
                project.save()
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to update a project: %s " % e)
            return True
        else:
            return False

    def createProject(self, name, group_id, import_url):
        """Creates a project"""
        project = None
        if import_url is None:
            try:
                project = self._gitlab.projects.create({'name': name, 'namespace_id': group_id})
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to create a project: %s " % e)
        else:
            try:
                project = self._gitlab.projects.create(
                    {'name': name, 'namespace_id': group_id, 'import_url': import_url})
            except Exception:
                e = get_exception()
                self._module.fail_json(msg="Failed to create a project: %s " % e)
        return project

    def deleteProject(self, project):
        """Deletes a project."""
        try:
            project.delete()
        except Exception:
            e = get_exception()
            self._module.fail_json(msg="Failed to dekla project: %s " % e)
        return True

    def existsProject(self, group, project, state):
        """Validates if a project exists."""
        project_name = project
        if not self.existsGroup(name=group):
            if state == "present":
                self._module.fail_json(msg="The group " + group + " doesnt exists in Gitlab. Please create it first.")

        projects = self._gitlab.projects.search(project_name)
        if len(projects) >= 1:
            for project in projects:
                group_project_name = group + "/" + project_name
                if group_project_name == project.path_with_namespace:
                    return project
        return False

    def existsGroup(self, name):
        """When group/user exists, object will be stored in self.groupObject."""
        groups = self._gitlab.groups.search(name)
        if len(groups) == 1:
            self.groupObject = groups[0]
            return True
        users = self._gitlab.users.list(username=name)
        if len(users) == 1:
            self.groupObject = users[0]
            return True
        return False

    def getGroupId(self):
        """Returns the id of the groupobject."""
        return int(self.groupObject.id)

    def getUserData(self):
        """Returns the userid and username."""
        user_data = self._gitlab.user
        return str(user_data.id), user_data.username


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool', aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            group=dict(required=False),
            name=dict(required=True),
            path=dict(required=False),
            description=dict(required=False),
            issues_enabled=dict(default=True, type='bool'),
            merge_requests_enabled=dict(default=True, type='bool'),
            wiki_enabled=dict(default=True, type='bool'),
            builds_enabled=dict(default=False, type='bool'),
            public_builds=dict(default=False, type='bool'),
            only_allow_merge_if_build_succeeds=dict(default=False, type='bool'),
            container_registry_enabled=dict(default=False, type='bool'),
            snippets_enabled=dict(default=True, type='bool'),
            public=dict(default=False, type='bool'),
            visibility_level=dict(default="0", choices=["0", "10", "20"]),
            import_url=dict(required=False),
            state=dict(default="present", choices=["present", 'absent']),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install python-gitlab")

    server_url = module.params['server_url']
    verify_ssl = module.params['validate_certs']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    login_token = module.params['login_token']
    group_name = module.params['group']
    project_name = module.params['name']
    project_path = module.params['path']
    description = module.params['description']
    issues_enabled = module.params['issues_enabled']
    merge_requests_enabled = module.params['merge_requests_enabled']
    wiki_enabled = module.params['wiki_enabled']
    builds_enabled = module.params['builds_enabled']
    public_builds = module.params['public_builds']
    only_allow_merge_if_build_succeeds = module.params['only_allow_merge_if_build_succeeds']
    container_registry_enabled = module.params['container_registry_enabled']
    snippets_enabled = module.params['snippets_enabled']
    public = module.params['public']
    visibility_level = module.params['visibility_level']
    import_url = module.params['import_url']
    state = module.params['state']
    use_credentials = None

    # Validate some credentials configuration parameters.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    if login_token and login_user:
        module.fail_json(msg="You can either use 'login_token' or 'login_user' and 'login_password'")

    try:
        if use_credentials:
            git = gitlab.Gitlab(url=server_url, email=login_user, password=login_password, ssl_verify=verify_ssl)
            git.auth()
        else:
            git = gitlab.Gitlab(url=server_url, private_token=login_token, ssl_verify=verify_ssl)
            git.auth()
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    project = GitLabProject(module, git)
    # Gather information if we have a group, or we have to add the project to the current user.
    if group_name is None:
        group_id, group_name = project.getUserData()
        project_data = project.existsProject(group=group_name, project=project_name, state=state)
    else:
        project_data = project.existsProject(group=group_name, project=project_name, state=state)
        if state == "present":
            group_id = project.getGroupId()

    if project_path is None:
        project_path = project_name.replace(" ", "_")

    if project_data and state == "absent":
        if module.check_mode:
            module.exit_json(changed=True, result="Project should have been deleted.")
        if project.deleteProject(project=project_data):
            module.exit_json(changed=True, result="Successfully deleted project %s" % project_name)
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Project deleted or does not exists")
        else:
            if project.createOrUpdateProject(project=project_data, name=project_name, group_id=group_id,
                                             issues=issues_enabled, wiki=wiki_enabled, path=project_path,
                                             merge_request=merge_requests_enabled, description=description,
                                             snippets=snippets_enabled, builds=builds_enabled, public_builds=public_builds,
                                             only_allow_merge_if_build_succeeds=only_allow_merge_if_build_succeeds,
                                             container_registry_enabled=container_registry_enabled, public=public,
                                             visibility_level=visibility_level, import_url=import_url):
                module.exit_json(changed=True, result="Successfully created or updated the project %s" % project_name)
            else:
                module.exit_json(changed=False, result="No configuration updates for project %s" % project_name)

if __name__ == '__main__':
    main()
