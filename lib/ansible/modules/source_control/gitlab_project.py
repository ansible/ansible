#!/usr/bin/python
# (c) 2015, Werner Dijkerman (ikben@werner-dijkerman.nl)
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
author: "Werner Dijkerman (@dj-wasabi)"
requirements:
    - pyapi-gitlab python module
options:
    server_url:
        description:
            - Url of Gitlab server, with protocol (http or https).
        required: true
    validate_certs:
        description:
            - When using https if SSL certificate needs to be verified.
        type: bool
        default: 'yes'
        aliases:
            - verify_ssl
    login_user:
        description:
            - Gitlab user name.
    login_password:
        description:
            - Gitlab password for login_user
    login_token:
        description:
            - Gitlab token for logging in.
    group:
        description:
            - The name of the group of which this projects belongs to.
            - When not provided, project will belong to user which is configured in 'login_user' or 'login_token'
            - When provided with username, project will be created for this user. 'login_user' or 'login_token' needs admin rights.
    name:
        description:
            - The name of the project
        required: true
    path:
        description:
            - The path of the project you want to create, this will be server_url/<group>/path
            - If not supplied, name will be used.
    description:
        description:
            - An description for the project.
    issues_enabled:
        description:
            - Whether you want to create issues or not.
            - Possible values are true and false.
        type: bool
        default: 'yes'
    merge_requests_enabled:
        description:
            - If merge requests can be made or not.
            - Possible values are true and false.
        type: bool
        default: 'yes'
    wiki_enabled:
        description:
            - If an wiki for this project should be available or not.
            - Possible values are true and false.
        type: bool
        default: 'yes'
    snippets_enabled:
        description:
            - If creating snippets should be available or not.
            - Possible values are true and false.
        type: bool
        default: 'yes'
    public:
        description:
            - If the project is public available or not.
            - Setting this to true is same as setting visibility_level to 20.
            - Possible values are true and false.
        type: bool
        default: 'no'
    visibility_level:
        description:
            - Private. visibility_level is 0. Project access must be granted explicitly for each user.
            - Internal. visibility_level is 10. The project can be cloned by any logged in user.
            - Public. visibility_level is 20. The project can be cloned without any authentication.
            - Possible values are 0, 10 and 20.
        default: 0
    import_url:
        description:
            - Git repository which will be imported into gitlab.
            - Gitlab server needs read access to this git repository.
        type: bool
        default: 'no'
    state:
        description:
            - create or delete project.
            - Possible values are present and absent.
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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_native


class GitLabProject(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git

    def createOrUpdateProject(self, project_exists, group_name, import_url, arguments):
        is_user = False
        group_id = self.getGroupId(group_name)
        if not group_id:
            group_id = self.getUserId(group_name)
            is_user = True

        if project_exists:
            # Edit project
            return self.updateProject(group_name, arguments)
        else:
            # Create project
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            return self.createProject(is_user, group_id, import_url, arguments)

    def createProject(self, is_user, user_id, import_url, arguments):
        if is_user:
            result = self._gitlab.createprojectuser(user_id=user_id, import_url=import_url, **arguments)
        else:
            group_id = user_id
            result = self._gitlab.createproject(namespace_id=group_id, import_url=import_url, **arguments)

        if not result:
            self._module.fail_json(msg="Failed to create project %r" % arguments['name'])

        return result

    def deleteProject(self, group_name, project_name):
        if self.existsGroup(group_name):
            project_owner = group_name
        else:
            project_owner = self._gitlab.currentuser()['username']

        search_results = self._gitlab.searchproject(search=project_name)
        for result in search_results:
            owner = result['namespace']['name']
            if owner == project_owner:
                return self._gitlab.deleteproject(result['id'])

    def existsProject(self, group_name, project_name):
        if self.existsGroup(group_name):
            project_owner = group_name
        else:
            project_owner = self._gitlab.currentuser()['username']

        search_results = self._gitlab.searchproject(search=project_name)
        for result in search_results:
            owner = result['namespace']['name']
            if owner == project_owner:
                return True
        return False

    def existsGroup(self, group_name):
        if group_name is not None:
            # Find the group, if group not exists we try for user
            for group in self._gitlab.getall(self._gitlab.getgroups):
                if group['name'] == group_name:
                    return True

            user_name = group_name
            user_data = self._gitlab.getusers(search=user_name)
            for data in user_data:
                if 'id' in user_data:
                    return True
        return False

    def getGroupId(self, group_name):
        if group_name is not None:
            # Find the group, if group not exists we try for user
            for group in self._gitlab.getall(self._gitlab.getgroups):
                if group['name'] == group_name:
                    return group['id']

    def getProjectId(self, group_name, project_name):
        if self.existsGroup(group_name):
            project_owner = group_name
        else:
            project_owner = self._gitlab.currentuser()['username']

        search_results = self._gitlab.searchproject(search=project_name)
        for result in search_results:
            owner = result['namespace']['name']
            if owner == project_owner:
                return result['id']

    def getUserId(self, user_name):
        user_data = self._gitlab.getusers(search=user_name)

        for data in user_data:
            if 'id' in data:
                return data['id']
        return self._gitlab.currentuser()['id']

    def to_bool(self, value):
        if value:
            return 1
        else:
            return 0

    def updateProject(self, group_name, arguments):
        project_changed = False
        project_name = arguments['name']
        project_id = self.getProjectId(group_name, project_name)
        project_data = self._gitlab.getproject(project_id=project_id)

        for arg_key, arg_value in arguments.items():
            project_data_value = project_data[arg_key]

            if isinstance(project_data_value, bool) or project_data_value is None:
                to_bool = self.to_bool(project_data_value)
                if to_bool != arg_value:
                    project_changed = True
                    continue
            else:
                if project_data_value != arg_value:
                    project_changed = True

        if project_changed:
            if self._module.check_mode:
                self._module.exit_json(changed=True)
            return self._gitlab.editproject(project_id=project_id, **arguments)
        else:
            return False


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
            snippets_enabled=dict(default=True, type='bool'),
            public=dict(default=False, type='bool'),
            visibility_level=dict(default="0", choices=["0", "10", "20"]),
            import_url=dict(required=False),
            state=dict(default="present", choices=["present", 'absent']),
        ),
        supports_check_mode=True
    )

    if not HAS_GITLAB_PACKAGE:
        module.fail_json(msg="Missing required gitlab module (check docs or install with: pip install pyapi-gitlab")

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
    snippets_enabled = module.params['snippets_enabled']
    public = module.params['public']
    visibility_level = module.params['visibility_level']
    import_url = module.params['import_url']
    state = module.params['state']

    # We need both login_user and login_password or login_token, otherwise we fail.
    if login_user is not None and login_password is not None:
        use_credentials = True
    elif login_token is not None:
        use_credentials = False
    else:
        module.fail_json(msg="No login credentials are given. Use login_user with login_password, or login_token")

    # Set project_path to project_name if it is empty.
    if project_path is None:
        project_path = project_name.replace(" ", "_")

    # Gitlab API makes no difference between upper and lower cases, so we lower them.
    project_name = project_name.lower()
    project_path = project_path.lower()
    if group_name is not None:
        group_name = group_name.lower()

    # Lets make an connection to the Gitlab server_url, with either login_user and login_password
    # or with login_token
    try:
        if use_credentials:
            git = gitlab.Gitlab(host=server_url, verify_ssl=verify_ssl)
            git.login(user=login_user, password=login_password)
        else:
            git = gitlab.Gitlab(server_url, token=login_token, verify_ssl=verify_ssl)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % to_native(e))

    # Check if user is authorized or not before proceeding to any operations
    # if not, exit from here
    auth_msg = git.currentuser().get('message', None)
    if auth_msg is not None and auth_msg == '401 Unauthorized':
        module.fail_json(msg='User unauthorized',
                         details="User is not allowed to access Gitlab server "
                                 "using login_token. Please check login_token")

    # Validate if project exists and take action based on "state"
    project = GitLabProject(module, git)
    project_exists = project.existsProject(group_name, project_name)

    # Creating the project dict
    arguments = {"name": project_name,
                 "path": project_path,
                 "description": description,
                 "issues_enabled": project.to_bool(issues_enabled),
                 "merge_requests_enabled": project.to_bool(merge_requests_enabled),
                 "wiki_enabled": project.to_bool(wiki_enabled),
                 "snippets_enabled": project.to_bool(snippets_enabled),
                 "public": project.to_bool(public),
                 "visibility_level": int(visibility_level)}

    if project_exists and state == "absent":
        project.deleteProject(group_name, project_name)
        module.exit_json(changed=True, result="Successfully deleted project %s" % project_name)
    else:
        if state == "absent":
            module.exit_json(changed=False, result="Project deleted or does not exist")
        else:
            if project.createOrUpdateProject(project_exists, group_name, import_url, arguments):
                module.exit_json(changed=True, result="Successfully created or updated the project %s" % project_name)
            else:
                module.exit_json(changed=False)


if __name__ == '__main__':
    main()
