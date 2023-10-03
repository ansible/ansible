# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.playbook.role.definition import RoleDefinition
from ansible.utils.display import Display
from ansible.utils.galaxy import scm_archive_resource

__all__ = ['RoleRequirement']

VALID_SPEC_KEYS = [
    'name',
    'role',
    'scm',
    'src',
    'version',
]

display = Display()


class RoleRequirement(RoleDefinition):

    """
    Helper class for Galaxy, which is used to parse both dependencies
    specified in meta/main.yml and requirements.yml files.
    """

    def __init__(self):
        pass

    @staticmethod
    def repo_url_to_role_name(repo_url):
        # gets the role name out of a repo like
        # http://git.example.com/repos/repo.git" => "repo"

        if '://' not in repo_url and '@' not in repo_url:
            return repo_url
        trailing_path = repo_url.split('/')[-1]
        if trailing_path.endswith('.git'):
            trailing_path = trailing_path[:-4]
        if trailing_path.endswith('.tar.gz'):
            trailing_path = trailing_path[:-7]
        if ',' in trailing_path:
            trailing_path = trailing_path.split(',')[0]
        return trailing_path

    @staticmethod
    def role_yaml_parse(role):
        """
        Parse the 'role' parameter and extract relevant information.

        This function supports both old style and new style role requirements.
        If the 'role' parameter is a string, it is parsed based on the presence of commas.
        If the 'role' parameter is a dictionary, it is processed based on the keys present.

        Parameters:
            role (Union[str, dict]): The role parameter to parse.

        Returns:
            dict: A dictionary containing the extracted role information.
        """

        if isinstance(role, string_types):
            name = None
            scm = None
            src = None
            version = None
            if ',' in role:
                if role.count(',') == 1:
                    (src, version) = role.strip().split(',', 1)
                elif role.count(',') == 2:
                    (src, version, name) = role.strip().split(',', 2)
                else:
                    raise AnsibleError("Invalid role line (%s). Proper format is 'role_name[,version[,name]]'" % role)
            else:
                src = role

            if name is None:
                name = RoleRequirement.repo_url_to_role_name(src)
            if '+' in src:
                (scm, src) = src.split('+', 1)

            return dict(name=name, src=src, scm=scm, version=version)

        if 'role' in role:
            name = role['role']
            if ',' in name:
                raise AnsibleError("Invalid old style role requirement: %s" % name)
            else:
                del role['role']
                role['name'] = name
        else:
            role = role.copy()

            if 'src' in role:
                # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
                if 'github.com' in role["src"] and 'http' in role["src"] and '+' not in role["src"] and not role["src"].endswith('.tar.gz'):
                    role["src"] = "git+" + role["src"]

                if '+' in role["src"]:
                    role["scm"], dummy, role["src"] = role["src"].partition('+')

                if 'name' not in role:
                    role["name"] = RoleRequirement.repo_url_to_role_name(role["src"])

            if 'version' not in role:
                role['version'] = ''

            if 'scm' not in role:
                role['scm'] = None

        for key in list(role.keys()):
            if key not in VALID_SPEC_KEYS:
                role.pop(key)

        return role

    @staticmethod
    def scm_archive_role(src, scm='git', name=None, version='HEAD', keep_scm_meta=False):
        """
        This static method is used to archive a role in a source control management system.

        Parameters:
            src (str): The source location of the role.
            scm (str, optional): The type of source control management system. Defaults to 'git'.
            name (str, optional): The name of the role. Defaults to None.
            version (str, optional): The version of the role. Defaults to 'HEAD'.
            keep_scm_meta (bool, optional): Whether to keep the source control
                management metadata. Defaults to False.

        Returns:
            The result of scm_archive_resource function.
        """

        return scm_archive_resource(src, scm=scm, name=name, version=version, keep_scm_meta=keep_scm_meta)
