#!/usr/bin/python
# (c) 2016, Werner Dijkerman (ikben@werner-dijkerman.nl)
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

DOCUMENTATION = '''
---
module: gitlab_tag
short_description: Creates/deletes tags on Gitlab projects
description:
   - When the tag does not exists in Gitlab, it will be created.
   - When the tag does exists and state=absent, the hook will be deleted.
   - The project and group should already exists when executing this module.
version_added: "2.3"
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
            - The name of the group of which the projects belongs to.
            - If the project belongs to a user, the username should be used for this.
        required: true
        default: null
    project:
        description:
            - The name of the project on which the hook needs to be added or updated.
        required: true
        default: null
    name:
        description:
            - The name of the tag you want to create
        required: true
        default: null
    ref:
        description:
            - Create tag using commit SHA, another tag name, or branch name
        required: false
        default: "master"
    description:
        description:
            - A description of the tag.
        required: false
        default: null
    state:
        description:
            - create or delete hooks.
        required: false
        default: "present"
        choices: ["present", "absent"]

'''

EXAMPLES = '''
- name: "Create tags"
  local_action:
    module: gitlab_tag
    server_url="http://gitlab.dj-wasabi.local"
    validate_certs=false
    login_token="WnUzDsxjy8230-Dy_k"
    group: my_first_group
    project: my_first_project
    name: v1.0
    ref: master
    description: My First Release
    state: present

- name: "Delete tag"
  local_action:
    module: gitlab_tag
    server_url="http://gitlab.dj-wasabi.local"
    validate_certs=false
    login_token="WnUzDsxjy8230-Dy_k"
    group: my_first_group
    project: my_first_project
    name: v0.9a
    ref: master
    description: My very bad release
    state: absent

'''

RETURN = '''# '''

try:
    import gitlab
    HAS_GITLAB_PACKAGE = True
except:
    HAS_GITLAB_PACKAGE = False

from ansible.module_utils.basic import *
from ansible.module_utils.pycompat24 import get_exception


class GitLabTag(object):
    def __init__(self, module, git):
        self._module = module
        self._gitlab = git
        self.projectObject = None
        self.tagObject = None

    def existsTag(self, name):
        """Validate is tag exists"""
        project = self.projectObject

        tags = project.tags.list()
        if len(tags) >= 1:
            for tag in tags:
                if tag.name == name:
                    self.tagObject = tag
                    return True
        return False

    def deleteTag(self):
        """Delete a tag"""
        tag = self.tagObject
        if tag.delete():
            return True
        else:
            return False

    def createTag(self, name, ref, description):
        """Create a tag"""
        project = self.projectObject
        tag = self.tagObject

        if tag is None:
            create_tag = project.tags.create({'tag_name': name, 'ref': ref})
            create_tag.set_release_description(description)
            return True
        return False

    def getProject(self, group, project):
        """Validates if a project exists."""
        project_name = project
        projects = self._gitlab.projects.search(project_name)
        if len(projects) >= 1:
            for project in projects:
                if project.namespace.name == group:
                    self.projectObject = project
                    return True
        return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(required=True),
            validate_certs=dict(required=False, default=True, type='bool', aliases=['verify_ssl']),
            login_user=dict(required=False, no_log=True),
            login_password=dict(required=False, no_log=True),
            login_token=dict(required=False, no_log=True),
            group=dict(required=True),
            project=dict(required=True),
            name=dict(required=True),
            ref=dict(required=False, default="master"),
            description=dict(required=False),
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
    project = module.params['project']
    group = module.params['group']
    name = module.params['name']
    ref = module.params['ref']
    description = module.params['description']
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
            git = gitlab.Gitlab(server_url, email=login_user, password=login_password, ssl_verify=verify_ssl)
            git.auth()
        else:
            git = gitlab.Gitlab(server_url, private_token=login_token, ssl_verify=verify_ssl)
            git.auth()
    except Exception:
        e = get_exception()
        module.fail_json(msg="Failed to connect to Gitlab server: %s " % e)

    tag = GitLabTag(module, git)
    project = tag.getProject(group=group, project=project)
    if not project:
        module.fail_json(msg="The project or the group does not exists. We can not create a tag.")

    project_tag = tag.existsTag(name=name)
    if project_tag:
        if state == "present":
            module.exit_json(changed=False, result="Tag is already created.")
        else:
            if module.check_mode:
                module.exit_json(changed=True, result="Tag should have been deleted.")
            if tag.deleteTag():
                module.exit_json(changed=True, result="Tag is deleted.")
            else:
                module.exit_json(changed=False, result="Something went wrong deleting the tag.")
    else:
        if state == "absent":
            module.exit_json(changed=False, result="There is no tag available.")
        else:
            if module.check_mode:
                module.exit_json(changed=True, result="Tag should have been created.")
            if tag.createTag(name=name, ref=ref, description=description):
                module.exit_json(changed=True, result="Tag is created.")
            else:
                module.exit_json(changed=False, result="Something went wrong creating the tag.")

if __name__ == '__main__':
    main()
