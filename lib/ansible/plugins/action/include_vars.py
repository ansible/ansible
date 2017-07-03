# (c) 2016, Allen Sanabria <asanabria@linuxdynasty.org>
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from os import path, walk
import re

from ansible.errors import AnsibleError
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native, to_text
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    VALID_FILE_EXTENSIONS = ['yaml', 'yml', 'json']
    VALID_DIR_ARGUMENTS = ['dir', 'depth', 'files_matching', 'ignore_files', 'extensions']
    VALID_FILE_ARGUMENTS = ['file', '_raw_params']
    VALID_ALL = ['name']

    def _set_dir_defaults(self):
        if not self.depth:
            self.depth = 0

        if self.files_matching:
            self.matcher = re.compile(r'{0}'.format(self.files_matching))
        else:
            self.matcher = None

        if not self.ignore_files:
            self.ignore_files = list()

        if isinstance(self.ignore_files, str):
            self.ignore_files = self.ignore_files.split()

        elif isinstance(self.ignore_files, dict):
            return {
                'failed': True,
                'message': '{0} must be a list'.format(self.ignore_files)
            }

    def _set_args(self):
        """ Set instance variables based on the arguments that were passed """

        self.return_results_as_name = self._task.args.get('name', None)
        self.source_dir = self._task.args.get('dir', None)
        self.source_file = self._task.args.get('file', None)
        if not self.source_dir and not self.source_file:
            self.source_file = self._task.args.get('_raw_params')

        self.depth = self._task.args.get('depth', None)
        self.files_matching = self._task.args.get('files_matching', None)
        self.ignore_files = self._task.args.get('ignore_files', None)
        self.valid_extensions = self._task.args.get('extensions', self.VALID_FILE_EXTENSIONS)

        # convert/validate extensions list
        if isinstance(self.valid_extensions, string_types):
            self.valid_extensions = list(self.valid_extensions)
        if not isinstance(self.valid_extensions, list):
            raise AnsibleError('Invalid type for "extensions" option, it must be a list')

    def run(self, tmp=None, task_vars=None):
        """ Load yml files recursively from a directory.
        """
        if task_vars is None:
            task_vars = dict()

        self.show_content = True
        self.included_files = []

        # Validate arguments
        dirs = 0
        files = 0
        for arg in self._task.args:
            if arg in self.VALID_DIR_ARGUMENTS:
                dirs += 1
            elif arg in self.VALID_FILE_ARGUMENTS:
                files += 1
            elif arg in self.VALID_ALL:
                pass
            else:
                raise AnsibleError('{0} is not a valid option in debug'.format(arg))

        if dirs and files:
            raise AnsibleError("Your are mixing file only and dir only arguments, these are incompatible")

        # set internal vars from args
        self._set_args()

        results = dict()
        if self.source_dir:
            self._set_dir_defaults()
            self._set_root_dir()
            if path.exists(self.source_dir):
                for root_dir, filenames in self._traverse_dir_depth():
                    failed, err_msg, updated_results = (self._load_files_in_dir(root_dir, filenames))
                    if failed:
                        break
                    results.update(updated_results)
            else:
                failed = True
                err_msg = ('{0} directory does not exist'.format(self.source_dir))
        else:
            try:
                self.source_file = self._find_needle('vars', self.source_file)
                failed, err_msg, updated_results = (
                    self._load_files(self.source_file)
                )
                if not failed:
                    results.update(updated_results)

            except AnsibleError as e:
                failed = True
                err_msg = to_native(e)

        if self.return_results_as_name:
            scope = dict()
            scope[self.return_results_as_name] = results
            results = scope

        result = super(ActionModule, self).run(tmp, task_vars)

        if failed:
            result['failed'] = failed
            result['message'] = err_msg

        result['ansible_included_var_files'] = self.included_files
        result['ansible_facts'] = results
        result['_ansible_no_log'] = not self.show_content

        return result

    def _set_root_dir(self):
        if self._task._role:
            if self.source_dir.split('/')[0] == 'vars':
                path_to_use = (
                    path.join(self._task._role._role_path, self.source_dir)
                )
                if path.exists(path_to_use):
                    self.source_dir = path_to_use
            else:
                path_to_use = (
                    path.join(
                        self._task._role._role_path, 'vars', self.source_dir
                    )
                )
                self.source_dir = path_to_use
        else:
            current_dir = (
                "/".join(self._task._ds._data_source.split('/')[:-1])
            )
            self.source_dir = path.join(current_dir, self.source_dir)

    def _traverse_dir_depth(self):
        """ Recursively iterate over a directory and sort the files in
            alphabetical order. Do not iterate pass the set depth.
            The default depth is unlimited.
        """
        current_depth = 0
        sorted_walk = list(walk(self.source_dir))
        sorted_walk.sort(key=lambda x: x[0])
        for current_root, current_dir, current_files in sorted_walk:
            current_depth += 1
            if current_depth <= self.depth or self.depth == 0:
                current_files.sort()
                yield (current_root, current_files)
            else:
                break

    def _ignore_file(self, filename):
        """ Return True if a file matches the list of ignore_files.
        Args:
            filename (str): The filename that is being matched against.

        Returns:
            Boolean
        """
        for file_type in self.ignore_files:
            try:
                if re.search(r'{0}$'.format(file_type), filename):
                    return True
            except Exception:
                err_msg = 'Invalid regular expression: {0}'.format(file_type)
                raise AnsibleError(err_msg)
        return False

    def _is_valid_file_ext(self, source_file):
        """ Verify if source file has a valid extension
        Args:
            source_file (str): The full path of source file or source file.
        Returns:
            Bool
        """
        file_ext = path.splitext(source_file)
        print(file_ext[-1][2:])
        return bool(len(file_ext) > 1 and file_ext[-1][1:] in self.valid_extensions)

    def _load_files(self, filename, validate_extensions=False):
        """ Loads a file and converts the output into a valid Python dict.
        Args:
            filename (str): The source file.

        Returns:
            Tuple (bool, str, dict)
        """
        results = dict()
        failed = False
        err_msg = ''
        if validate_extensions and not self._is_valid_file_ext(filename):
            failed = True
            err_msg = ('{0} does not have a valid extension: {1}' .format(filename, ', '.join(self.valid_extensions)))
        else:
            b_data, show_content = self._loader._get_file_contents(filename)
            data = to_text(b_data, errors='surrogate_or_strict')

            self.show_content = show_content
            data = self._loader.load(data, show_content)
            if not data:
                data = dict()
            if not isinstance(data, dict):
                failed = True
                err_msg = ('{0} must be stored as a dictionary/hash' .format(filename))
            else:
                self.included_files.append(filename)
                results.update(data)

        return failed, err_msg, results

    def _load_files_in_dir(self, root_dir, var_files):
        """ Load the found yml files and update/overwrite the dictionary.
        Args:
            root_dir (str): The base directory of the list of files that is being passed.
            var_files: (list): List of files to iterate over and load into a dictionary.

        Returns:
            Tuple (bool, str, dict)
        """
        results = dict()
        failed = False
        err_msg = ''
        for filename in var_files:
            stop_iter = False
            # Never include main.yml from a role, as that is the default included by the role
            if self._task._role:
                if filename == 'main.yml':
                    stop_iter = True
                    continue

            filepath = path.join(root_dir, filename)
            if self.files_matching:
                if not self.matcher.search(filename):
                    stop_iter = True

            if not stop_iter and not failed:
                if path.exists(filepath) and not self._ignore_file(filename):
                    failed, err_msg, loaded_data = self._load_files(filepath, validate_extensions=True)
                    if not failed:
                        results.update(loaded_data)

        return failed, err_msg, results
