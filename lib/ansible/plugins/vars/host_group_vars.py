# Copyright 2017 RedHat, inc
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
#############################################
'''
DOCUMENTATION:
    vars: host_group_vars
    version_added: "2.4"
    short_description: In charge of loading group_vars and host_vars
    description:
        - Loads YAML vars into corresponding groups/hosts in group_vars/ and host_vars/ directories.
        - Files are restricted by extension to one of .yaml, .json, .yml or no extension.
        - Hidden (starting with '.') and backup (ending with '~') files and directories are ignored.
        - Only applies to inventory sources that are existing paths.
    notes:
        - It takes the place of the previously hardcoded group_vars/host_vars loading.
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
from ansible import constants as C
from ansible.errors import AnsibleParserError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.host import Host
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars

FOUND = {}


class VarsModule(BaseVarsPlugin):

    def get_vars(self, loader, path, entities, cache=True):
        ''' parses the inventory file '''

        if not isinstance(entities, list):
            entities = [entities]

        super(VarsModule, self).get_vars(loader, path, entities)

        data = {}
        for entity in entities:
            if isinstance(entity, Host):
                subdir = 'host_vars'
            elif isinstance(entity, Group):
                subdir = 'group_vars'
            else:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            try:
                found_files = []
                # load vars
                opath = os.path.realpath(os.path.join(self._basedir, subdir))
                key = '%s.%s' % (entity.name, opath)
                if cache and key in FOUND:
                    found_files = FOUND[key]
                else:
                    b_opath = to_bytes(opath)
                    # no need to do much if path does not exist for basedir
                    if os.path.exists(b_opath):
                        if os.path.isdir(b_opath):
                            self._display.debug("\tprocessing dir %s" % opath)
                            found_files = self._find_vars_files(opath, entity.name)
                            FOUND[key] = found_files
                        else:
                            self._display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))

                for found in found_files:
                    new_data = loader.load_from_file(found, cache=True, unsafe=True)
                    if new_data:  # ignore empty files
                        data = combine_vars(data, new_data)

            except Exception as e:
                raise AnsibleParserError(to_native(e))
        return data

    def _find_vars_files(self, path, name):
        """ Find {group,host}_vars files """

        b_path = to_bytes(os.path.join(path, name))
        found = []

        # first look for w/o extensions
        if os.path.exists(b_path):
            if os.path.isdir(b_path):
                found.extend(self._get_dir_files(to_text(b_path)))
            else:
                found.append(b_path)
        else:
            # add valid extensions to name
            for ext in C.YAML_FILENAME_EXTENSIONS:

                if '.' in ext:
                    full_path = b_path + to_bytes(ext)
                elif ext:
                    full_path = b'.'.join([b_path, to_bytes(ext)])
                else:
                    full_path = b_path

                if os.path.exists(full_path) and os.path.isfile(full_path):
                    found.append(full_path)
                    break
        return found

    def _get_dir_files(self, path):

        found = []
        for spath in os.listdir(path):
            if not spath.startswith(b'.') and not spath.endswith(b'~'):  # skip hidden and backups

                ext = os.path.splitext(spath)[-1]
                full_spath = os.path.join(path, spath)

                if os.path.isdir(full_spath) and not ext:  # recursive search if dir
                    found.extend(self._get_dir_files(full_spath))
                elif os.path.isfile(full_spath) and (not ext or to_text(ext) in C.YAML_FILENAME_EXTENSIONS):
                    # only consider files with valid extensions or no extension
                    found.append(full_spath)

        return found
