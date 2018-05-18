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

import os
import tempfile
import tarfile

from subprocess import Popen, PIPE

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_native
from ansible.module_utils.six import string_types
from ansible.playbook.role.definition import RoleDefinition


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
        display.deprecated("The comma separated role spec format, use the yaml/explicit format instead. Line that trigger this: %s" % role_spec,
                           version="2.7")

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
            name = role['role']
            if ',' in name:
                # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
                role = RoleRequirement.role_spec_parse(role['role'])
            else:
                del role['role']
                role['name'] = name
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

        for key in list(role.keys()):
            if key not in VALID_SPEC_KEYS:
                role.pop(key)

        return role

    @staticmethod
    def scm_archive_role(src, scm='git', name=None, version='HEAD', keep_scm_meta=False):

        def run_scm_cmd(cmd, tempdir):
            try:
                popen = Popen(cmd, cwd=tempdir, stdout=PIPE, stderr=PIPE)
                stdout, stderr = popen.communicate()
            except Exception as e:
                ran = " ".join(cmd)
                display.debug("ran %s:" % ran)
                display.debug("\tstdout: " + stdout)
                display.debug("\tstderr: " + stderr)
                raise AnsibleError("when executing %s: %s" % (ran, to_native(e)))
            if popen.returncode != 0:
                raise AnsibleError("- command %s failed in directory %s (rc=%s)" % (' '.join(cmd), tempdir, popen.returncode))

        if scm not in ['hg', 'git']:
            raise AnsibleError("- scm %s is not currently supported" % scm)

        tempdir = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
        clone_cmd = [scm, 'clone', src, name]
        run_scm_cmd(clone_cmd, tempdir)

        if scm == 'git' and version:
            checkout_cmd = [scm, 'checkout', version]
            run_scm_cmd(checkout_cmd, os.path.join(tempdir, name))

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.tar', dir=C.DEFAULT_LOCAL_TMP)
        archive_cmd = None
        if keep_scm_meta:
            display.vvv('tarring %s from %s to %s' % (name, tempdir, temp_file.name))
            with tarfile.open(temp_file.name, "w") as tar:
                tar.add(os.path.join(tempdir, name), arcname=name)
        elif scm == 'hg':
            archive_cmd = ['hg', 'archive', '--prefix', "%s/" % name]
            if version:
                archive_cmd.extend(['-r', version])
            archive_cmd.append(temp_file.name)
        elif scm == 'git':
            archive_cmd = ['git', 'archive', '--prefix=%s/' % name, '--output=%s' % temp_file.name]
            if version:
                archive_cmd.append(version)
            else:
                archive_cmd.append('HEAD')

        if archive_cmd is not None:
            display.vvv('archiving %s' % archive_cmd)
            run_scm_cmd(archive_cmd, os.path.join(tempdir, name))

        return temp_file.name
