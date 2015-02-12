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

from six import iteritems, string_types

import os

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.playbook.role.definition import RoleDefinition

__all__ = ['RoleRequirement']


class RoleRequirement(RoleDefinition):

    """
    FIXME: document various ways role specs can be specified
    """

    def __init__(self):
        pass

    def _get_valid_spec_keys(self):
        return (
            'name',
            'role',
            'scm',
            'src',
            'version',
        )

    def parse(self, ds):
        '''
        FIXME: docstring
        '''

        assert type(ds) == dict or isinstance(ds, string_types)

        role_name    = ''
        role_params  = dict()
        new_ds       = dict()

        if isinstance(ds, string_types):
            role_name = ds
        else:
            ds = self._munge_role_spec(ds)
            (new_ds, role_params) = self._split_role_params(ds)

            # pull the role name out of the ds
            role_name = new_ds.get('role_name')
            del ds['role_name']

        return (new_ds, role_name, role_params)

    def _munge_role_spec(self, ds):
        if 'role' in ds:
            # Old style: {role: "galaxy.role,version,name", other_vars: "here" }
            role_info = self._role_spec_parse(ds['role'])
            if isinstance(role_info, dict):
                # Warning: Slight change in behaviour here.  name may be being
                # overloaded.  Previously, name was only a parameter to the role.
                # Now it is both a parameter to the role and the name that
                # ansible-galaxy will install under on the local system.
                if 'name' in ds and 'name' in role_info:
                    del role_info['name']
                ds.update(role_info)
        else:
            # New style: { src: 'galaxy.role,version,name', other_vars: "here" }
            if 'github.com' in ds["src"] and 'http' in ds["src"] and '+' not in ds["src"] and not ds["src"].endswith('.tar.gz'):
                ds["src"] = "git+" + ds["src"]

            if '+' in ds["src"]:
                (scm, src) = ds["src"].split('+')
                ds["scm"] = scm
                ds["src"] = src

            if 'name' in role:
                ds["role"] = ds["name"]
                del ds["name"]
            else:
                ds["role"] = self._repo_url_to_role_name(ds["src"])

            # set some values to a default value, if none were specified
            ds.setdefault('version', '')
            ds.setdefault('scm', None)

        return ds

    def _repo_url_to_role_name(self, repo_url):
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

    def _role_spec_parse(self, role_spec):
        # takes a repo and a version like
        # git+http://git.example.com/repos/repo.git,v1.0
        # and returns a list of properties such as:
        # {
        #   'scm': 'git',
        #   'src': 'http://git.example.com/repos/repo.git',
        #   'version': 'v1.0',
        #   'name': 'repo'
        # }

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
            role_name = self._repo_url_to_role_name(tokens[0])

        if scm and not role_version:
            role_version = default_role_versions.get(scm, '')

        return dict(scm=scm, src=role_url, version=role_version, role_name=role_name)


