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
from __future__ import annotations

DOCUMENTATION = '''
    name: host_group_vars
    version_added: "2.4"
    short_description: In charge of loading group_vars and host_vars
    requirements:
        - Enabled in configuration
    description:
        - Loads YAML vars into corresponding groups/hosts in group_vars/ and host_vars/ directories.
        - Files are restricted by extension to one of .yaml, .json, .yml or no extension.
        - Hidden (starting with '.') and backup (ending with '~') files and directories are ignored.
        - Only applies to inventory sources that are existing paths.
        - Starting in 2.10, this plugin requires enabling and is enabled by default.
    options:
      stage:
        ini:
          - key: stage
            section: vars_host_group_vars
        env:
          - name: ANSIBLE_VARS_PLUGIN_STAGE
      _valid_extensions:
        default: [".yml", ".yaml", ".json"]
        description:
          - "Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these."
          - 'This affects vars_files, include_vars, inventory and vars plugins among others.'
        env:
          - name: ANSIBLE_YAML_FILENAME_EXT
        ini:
          - key: yaml_valid_extensions
            section: defaults
        type: list
        elements: string
    extends_documentation_fragment:
      - vars_plugin_staging
'''

import os
from ansible.errors import AnsibleParserError
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.vars import BaseVarsPlugin
from ansible.utils.path import basedir
from ansible.inventory.group import InventoryObjectType
from ansible.utils.vars import combine_vars

CANONICAL_PATHS = {}  # type: dict[str, str]
FOUND = {}  # type: dict[str, list[str]]
NAK = set()  # type: set[str]
PATH_CACHE = {}  # type: dict[tuple[str, str], str]


class VarsModule(BaseVarsPlugin):

    REQUIRES_ENABLED = True
    is_stateless = True

    def load_found_files(self, loader, data, found_files):
        for found in found_files:
            new_data = loader.load_from_file(found, cache='all', unsafe=True)
            if new_data:  # ignore empty files
                data = combine_vars(data, new_data)
        return data

    def get_vars(self, loader, path, entities, cache=True):
        ''' parses the inventory file '''

        if not isinstance(entities, list):
            entities = [entities]

        # realpath is expensive
        try:
            realpath_basedir = CANONICAL_PATHS[path]
        except KeyError:
            CANONICAL_PATHS[path] = realpath_basedir = os.path.realpath(basedir(path))

        data = {}
        for entity in entities:
            try:
                entity_name = entity.name
            except AttributeError:
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            try:
                first_char = entity_name[0]
            except (TypeError, IndexError, KeyError):
                raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

            # avoid 'chroot' type inventory hostnames /path/to/chroot
            if first_char != os.path.sep:
                try:
                    found_files = []
                    # load vars
                    try:
                        entity_type = entity.base_type
                    except AttributeError:
                        raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

                    if entity_type is InventoryObjectType.HOST:
                        subdir = 'host_vars'
                    elif entity_type is InventoryObjectType.GROUP:
                        subdir = 'group_vars'
                    else:
                        raise AnsibleParserError("Supplied entity must be Host or Group, got %s instead" % (type(entity)))

                    if cache:
                        try:
                            opath = PATH_CACHE[(realpath_basedir, subdir)]
                        except KeyError:
                            opath = PATH_CACHE[(realpath_basedir, subdir)] = os.path.join(realpath_basedir, subdir)

                        if opath in NAK:
                            continue
                        key = '%s.%s' % (entity_name, opath)
                        if key in FOUND:
                            data = self.load_found_files(loader, data, FOUND[key])
                            continue
                    else:
                        opath = PATH_CACHE[(realpath_basedir, subdir)] = os.path.join(realpath_basedir, subdir)

                    if os.path.isdir(opath):
                        self._display.debug("\tprocessing dir %s" % opath)
                        FOUND[key] = found_files = loader.find_vars_files(opath, entity_name)
                    elif not os.path.exists(opath):
                        # cache missing dirs so we don't have to keep looking for things beneath the
                        NAK.add(opath)
                    else:
                        self._display.warning("Found %s that is not a directory, skipping: %s" % (subdir, opath))
                        # cache non-directory matches
                        NAK.add(opath)

                    data = self.load_found_files(loader, data, found_files)

                except Exception as e:
                    raise AnsibleParserError(to_native(e))
        return data
