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

from ansible.compat.six import string_types

import yaml

from ansible.errors import AnsibleError
from ansible.playbook.role.definition import RoleDefinition
from ansible.galaxy.role import GalaxyRole

__all__ = ['RoleRequirement']


VALID_SPEC_KEYS = [
    'name',
    'role',
    'scm',
    'src',
    'version',
]

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
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
    def role_spec_parse(role_spec):
        # takes a repo and a version like
        # git+http://git.example.com/repos/repo.git,v1.0
        # and returns a list of properties such as:
        # {
        #   'scm': 'git',
        #   'src': 'http://git.example.com/repos/repo.git',
        #   'version': 'v1.0',
        #   'name': 'repo'
        # }

        display.deprecated("The comma separated role spec format, use the yaml/explicit format instead.")

        default_role_versions = dict(git='master', hg='tip')

        role_spec = role_spec.strip()
        role_version = ''
        if role_spec == "" or role_spec.startswith("#"):
            return (None, None, None, None)

        tokens = [s.strip() for s in role_spec.split(',')]

        # assume https://github.com URLs are git+https:// URLs and not
        # tarballs unless they end in '.zip'
        if 'github.com/' in tokens[0] and not tokens[0].startswith("git+") and not tokens[0].endswith('.tar.gz'):
            tokens[0] = 'git+' + tokens[0]

        if '+' in tokens[0]:
            (scm, role_url) = tokens[0].split('+')
        else:
            scm = None
            role_url = tokens[0]

        if len(tokens) >= 2:
            role_version = tokens[1]

        if len(tokens) == 3:
            role_name = tokens[2]
        else:
            role_name = RoleRequirement.repo_url_to_role_name(tokens[0])

        if scm and not role_version:
            role_version = default_role_versions.get(scm, '')

        return dict(scm=scm, src=role_url, version=role_version, name=role_name)

    @staticmethod
    def role_yaml_parse(role):

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
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            role = RoleRequirement.role_spec_parse(role['role'])
        else:
            role = role.copy()

            if 'src'in role:
                # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
                if 'github.com' in role["src"] and 'http' in role["src"] and '+' not in role["src"] and not role["src"].endswith('.tar.gz'):
                    role["src"] = "git+" + role["src"]

                if '+' in role["src"]:
                    (scm, src) = role["src"].split('+')
                    role["scm"] = scm
                    role["src"] = src

                if 'name' not in role:
                    role["name"] = RoleRequirement.repo_url_to_role_name(role["src"])

            if 'version' not in role:
                role['version'] = ''

            if 'scm' not in role:
                role['scm'] = None

        for key in role.keys():
            if key not in VALID_SPEC_KEYS:
                role.pop(key)

        return role


def read_roles_file(galaxy, role_file):
    roles_left = []
    try:
        f = open(role_file, 'r')
        if role_file.endswith('.yaml') or role_file.endswith('.yml'):
            try:
                required_roles = yaml.safe_load(f.read())
            except Exception as e:
                raise AnsibleError("Unable to load data from the requirements file: %s" % role_file)

            if required_roles is None:
                raise AnsibleError("No roles found in file: %s" % role_file)

            for role in required_roles:
                role = RoleRequirement.role_yaml_parse(role)
                if 'name' not in role and 'scm' not in role:
                    raise AnsibleError("Must specify name or src for role")
                roles_left.append(GalaxyRole(galaxy, **role))
        else:
            display.deprecated("going forward only the yaml format will be supported")
            # roles listed in a file, one per line
            for rline in f.readlines():
                if rline.startswith("#") or rline.strip() == '':
                    continue
                role = RoleRequirement.role_yaml_parse(rline.strip())
                roles_left.append(GalaxyRole(galaxy, **role))
        f.close()
    except (IOError, OSError) as e:
        raise AnsibleError('Unable to open %s: %s' % (role_file, str(e)))
    return roles_left


def install_roles(roles_left, galaxy):
    """ Helper function to allow other CLI commands install roles """

    for role in roles_left:
        display.vvv('Installing role %s ' % role.name)
        # query the galaxy API for the role data

        if role.install_info is not None and not galaxy.force:
            if role.install_info['version'] != role.version:
                display.display('- changing role %s from %s to %s' %
                        (role.name, role.install_info['version'], role.version or "unspecified"))
                role.remove()
            else:
                display.display('- %s is already installed, skipping.' % role.version_string)
                continue

        try:
            installed = role.install()
        except AnsibleError as e:
            display.warning("- %s was NOT installed successfully: %s " % (role.name, str(e)))
            exit_without_ignore(galaxy.ignore_errors)
            continue

        # install dependencies, if we want them
        if not galaxy.no_deps and installed:
            role_dependencies = role.metadata.get('dependencies') or []
            for dep in role_dependencies:
                display.debug('Installing dep %s' % dep)
                dep_req = RoleRequirement()
                dep_info = dep_req.role_yaml_parse(dep)
                dep_role = GalaxyRole(galaxy, **dep_info)
                if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                    # we know we can skip this, as it's not going to
                    # be found on galaxy.ansible.com
                    continue
                if dep_role.install_info is None:
                    if dep_role not in roles_left:
                        display.display('- adding dependency: %s' % dep_role.version_string)
                        roles_left.append(dep_role)
                    else:
                        display.display('- dependency %s already pending installation.' % dep_role.name)
                else:
                    if dep_role.install_info['version'] != dep_role.version:
                        display.warning('- dependency %s from role %s differs from already installed version (%s), skipping' %
                                (dep_role.version_string, role.name, dep_role.install_info['version']))
                    else:
                        display.display('- dependency %s is already installed, skipping.' % dep_role.name)

        if not installed:
            display.warning("- %s was NOT installed successfully." % role.name)
            exit_without_ignore(galaxy.ignore_errors)

    return 0


def exit_without_ignore(ignore_errors):
    """
    Exits unless ignore_errors is True
    """
    if not ignore_errors:
        raise AnsibleError('- you can use --ignore-errors to skip failed roles and finish processing the list.')
