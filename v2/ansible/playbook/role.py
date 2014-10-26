# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

from ansible.errors import AnsibleError
from ansible.parsing.yaml import DataLoader
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.base import Base
from ansible.playbook.block import Block

from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject, AnsibleMapping

class Role(Base):

    _role_name      = FieldAttribute(isa='string')
    _role_path      = FieldAttribute(isa='string')
    _src            = FieldAttribute(isa='string')
    _scm            = FieldAttribute(isa='string')
    _version        = FieldAttribute(isa='string')
    _task_blocks    = FieldAttribute(isa='list', default=[])
    _handler_blocks = FieldAttribute(isa='list', default=[])
    _params         = FieldAttribute(isa='dict', default=dict())
    _metadata       = FieldAttribute(isa='dict', default=dict())
    _default_vars   = FieldAttribute(isa='dict', default=dict())
    _role_vars      = FieldAttribute(isa='dict', default=dict())

    def __init__(self, loader=DataLoader):
        self._role_path = None
        super(Role, self).__init__(loader=loader)

    def __repr__(self):
        return self.get_name()

    def get_name(self):
        return self._attributes['role_name']

    @staticmethod
    def load(data):
        assert isinstance(data, string_types) or isinstance(data, dict)
        r = Role()
        r.load_data(data)
        return r

    #------------------------------------------------------------------------------
    # munge, and other functions used for loading the ds

    def munge(self, ds):
        # create the new ds as an AnsibleMapping, so we can preserve any line/column
        # data from the parser, and copy that info from the old ds (if applicable)
        new_ds = AnsibleMapping()
        if isinstance(ds, AnsibleBaseYAMLObject):
            new_ds.copy_position_info(ds)

        # Role definitions can be strings or dicts, so we fix things up here.
        # Anything that is not a role name, tag, or conditional will also be
        # added to the params sub-dictionary for loading later
        if isinstance(ds, string_types):
            new_ds['role_name'] = ds
        else:
            # munge the role ds here to correctly fill in the various fields which
            # may be used to define the role, like: role, src, scm, etc.
            ds = self._munge_role(ds)

            # now we split any random role params off from the role spec and store
            # them in a dictionary of params for parsing later
            params = dict()
            attr_names = [attr_name for (attr_name, attr_value) in self._get_base_attributes().iteritems()]
            for (key, value) in iteritems(ds):
                if key not in attr_names and key != 'role':
                    # this key does not match a field attribute, so it must be a role param
                    params[key] = value
                else:
                    # this is a field attribute, so copy it over directly
                    new_ds[key] = value
            new_ds['params'] = params

        # Set the role name and path, based on the role definition
        (role_name, role_path) = self._get_role_path(new_ds.get('role_name'))
        new_ds['role_name'] = role_name
        new_ds['role_path'] = role_path

        # load the role's files, if they exist
        new_ds['metadata']       = self._load_role_yaml(role_path, 'meta')
        new_ds['task_blocks']    = self._load_role_yaml(role_path, 'tasks')
        new_ds['handler_blocks'] = self._load_role_yaml(role_path, 'handlers')
        new_ds['default_vars']   = self._load_role_yaml(role_path, 'defaults')
        new_ds['role_vars']      = self._load_role_yaml(role_path, 'vars')

        # and return the newly munged ds
        return new_ds

    def _load_role_yaml(self, role_path, subdir):
        file_path = os.path.join(role_path, subdir)
        if os.path.exists(file_path) and os.path.isdir(file_path):
            main_file = self._resolve_main(file_path)
            if os.path.exists(main_file):
                return self._loader.load_from_file(main_file)
        return None

    def _resolve_main(self, basepath):
        ''' flexibly handle variations in main filenames '''
        possible_mains = (
            os.path.join(basepath, 'main'),
            os.path.join(basepath, 'main.yml'),
            os.path.join(basepath, 'main.yaml'),
            os.path.join(basepath, 'main.json'),
        )

        if sum([os.path.isfile(x) for x in possible_mains]) > 1:
            raise AnsibleError("found multiple main files at %s, only one allowed" % (basepath))
        else:
            for m in possible_mains:
                if os.path.isfile(m):
                    return m # exactly one main file
            return possible_mains[0] # zero mains (we still need to return something)

    def _get_role_path(self, role):
        '''
        the 'role', as specified in the ds (or as a bare string), can either
        be a simple name or a full path. If it is a full path, we use the
        basename as the role name, otherwise we take the name as-given and
        append it to the default role path
        '''

        # FIXME: this should use unfrackpath once the utils code has been sorted out
        role_path = os.path.normpath(role)
        print("first role path is %s" % role_path)
        if os.path.exists(role_path):
            role_name = os.path.basename(role)
            print('returning role path %s' % role_path)
            return (role_name, role_path)
        else:
            for path in ('./roles', '/etc/ansible/roles'):
                role_path = os.path.join(path, role)
		print("current role path is %s" % role_path)
                if os.path.exists(role_path):
                    print('returning role path %s' % role_path)
                    return (role, role_path)

        # FIXME: make the parser smart about list/string entries
        #        in the yaml so the error line/file can be reported
        #        here 
        raise AnsibleError("the role '%s' was not found" % role, obj=role)

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

    def _munge_role(self, ds):
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

    #------------------------------------------------------------------------------
    # attribute loading defs

    def _load_list_of_blocks(self, ds):
        assert type(ds) == list
        block_list = []
        for block in ds:
            b = Block(block)
            block_list.append(b)
        return block_list

    def _load_task_blocks(self, attr, ds):
        if ds is None:
            return []
        return self._load_list_of_blocks(ds)

    def _load_handler_blocks(self, attr, ds):
        if ds is None:
            return []
        return self._load_list_of_blocks(ds)

    #------------------------------------------------------------------------------
    # other functions

    def get_variables(self):
        # returns the merged variables for this role, including
        # recursively merging those of all child roles
        return dict()

    def get_immediate_dependencies(self):
        return self._dependencies

    def get_all_dependencies(self):
        # returns a list built recursively, of all deps from
        # all child dependencies
        all_deps = []
        for dep in self._dependencies:
            list_union(all_deps, dep.get_all_dependencies())
        all_deps = list_union(all_deps, self.dependencies)
        return all_deps

