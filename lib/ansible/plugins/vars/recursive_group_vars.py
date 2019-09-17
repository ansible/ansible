from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    vars: recursive_group_vars
    version_added: "2.9"
    short_description: Loads r_group_vars recursively
    description:
        - In comparison to host_group_vars plugin, this plugin traverses the `r_group_vars` directory
          and instead of matching all files and directories within the first matching directory it
          traverses the directory tree and recursively matches directories to groups during directory
          traversal and applies all files within a matching directory.
        - During traversal in a directory first all files are applied and then matching directories
          traversed. The existing priorities for groups apply during directory traversal.
        - If several matching directories are found on the same directory level they are traversed
          consecutively in a depth-first fashion.
        - The following points are identical to host_group_vars plugin -
        - Files are restricted by extension to one of .yaml, .json, .yml or no extension.
        - Hidden (starting with '.') and backup (ending with '~') files and directories are ignored.
        - Only applies to inventory sources that are existing paths.
    options:
      _valid_extensions:
        default: [".yml", ".yaml", ".json"]
        description:
          - "Check all of these extensions when looking for 'variable' files which should be YAML or JSON or vaulted versions of these."
          - 'This affects vars_files, include_vars, inventory and vars plugins among others.'
        env:
          - name: ANSIBLE_YAML_FILENAME_EXT
        ini:
          - section: yaml_valid_extensions
            key: defaults
        type: list
'''

import os
from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.errors import AnsibleParserError
from ansible.plugins.vars import BaseVarsPlugin
from ansible.inventory.group import Group
from ansible.utils.vars import combine_vars


class VarsModule(BaseVarsPlugin):

    FOUND = {}

    def load_vars_files(self, loader, group, path):
        data = {}

        found_files = loader.find_vars_files(path, group, allow_dir=True, depth=[1])
        for found in found_files:
            self._display.debug("recursive_group_vars - Loading file : %s" % to_text(found))
            try:
                new_data = loader.load_from_file(found, cache=True, unsafe=True)
                if new_data:
                    data = combine_vars(data, new_data)
            except Exception as e:
                raise AnsibleParserError("Failed to apply variable file %s : %s" % (found, to_native(e)))

        return data

    def find_vars_recurse(self, loader, groups, path):
        data = {}

        self._display.debug("recursive_group_vars - Traversing dir : %s with groups : %s" % (path, to_text(groups)))

        # Recurse into directories
        for group in groups:
            try:
                b_opath = os.path.realpath(to_bytes(os.path.join(path, group)))
                if os.path.exists(b_opath):
                    if os.path.isdir(b_opath):
                        # Load all files from matched group directory
                        data = combine_vars(data, self.load_vars_files(loader, group, path))
                        # Traversing further down
                        data = combine_vars(data, self.find_vars_recurse(loader, groups, to_text(b_opath)))
            except Exception as e:
                raise AnsibleParserError("Failure during traversal of group directory '%s' in '%s' : %s" % (group, path, to_native(e)))

        return data

    def get_vars(self, loader, path, entities, cache=True):

        if not isinstance(entities, list):
            entities = [entities]

        groups = [e.name for e in entities if isinstance(e, Group)]

        if not groups:
            return {}

        super(VarsModule, self).get_vars(loader, path, entities)
        b_opath = os.path.realpath(os.path.join(to_bytes(self._basedir), b'r_group_vars'))

        data = {}
        if os.path.exists(b_opath):
            key = tuple(groups) + (b_opath,)
            if cache and key in self.FOUND:
                data = self.FOUND[key]
            else:
                data = self.find_vars_recurse(loader, groups, to_text(b_opath))
                self.FOUND[key] = data

        return data
