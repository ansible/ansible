# Copyright: (c) 2016, Allen Sanabria <asanabria@linuxdynasty.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from os import path, walk
import re
import pathlib

import ansible.constants as C
from ansible.errors import AnsibleError
from ansible._internal._datatag._tags import SourceWasEncrypted
from ansible.module_utils.common.text.converters import to_native
from ansible.plugins.action import ActionBase
from ansible.utils.vars import combine_vars


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    VALID_FILE_EXTENSIONS = ['yaml', 'yml', 'json']
    VALID_DIR_ARGUMENTS = ['dir', 'depth', 'files_matching', 'ignore_files', 'extensions', 'ignore_unknown_extensions']
    VALID_FILE_ARGUMENTS = ['file', '_raw_params']
    VALID_ALL = ['name', 'hash_behaviour']
    _requires_connection = False

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
            self._display.deprecated(
                msg="Specifying 'ignore_files' as a string is deprecated.",
                version="2.24",
                help_text="Use a list of strings instead.",
                obj=self.ignore_files,
            )
            self.ignore_files = self.ignore_files.split()

        if not isinstance(self.ignore_files, list):
            raise AnsibleError("The 'ignore_files' option must be a list.", obj=self.ignore_files)

    def _set_args(self):
        """ Set instance variables based on the arguments that were passed """

        self.hash_behaviour = self._task.args.get('hash_behaviour', None)
        self.return_results_as_name = self._task.args.get('name', None)
        self.source_dir = self._task.args.get('dir', None)
        self.source_file = self._task.args.get('file', None)
        if not self.source_dir and not self.source_file:
            self.source_file = self._task.args.get('_raw_params')
            if self.source_file:
                self.source_file = self.source_file.rstrip('\n')

        self.depth = self._task.args.get('depth', None)
        self.files_matching = self._task.args.get('files_matching', None)
        self.ignore_unknown_extensions = self._task.args.get('ignore_unknown_extensions', False)
        self.ignore_files = self._task.args.get('ignore_files', None)
        self.valid_extensions = self._task.args.get('extensions', self.VALID_FILE_EXTENSIONS)

        if not isinstance(self.valid_extensions, list):
            raise AnsibleError("The 'extensions' option must be a list.", obj=self.valid_extensions)

    def run(self, tmp=None, task_vars=None):
        """ Load yml files recursively from a directory.
        """
        del tmp  # tmp no longer has any effect

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
                raise AnsibleError(f'{arg} is not a valid option in include_vars', obj=arg)

        if dirs and files:
            raise AnsibleError("You are mixing file only and dir only arguments, these are incompatible", obj=self._task.args)

        # set internal vars from args
        self._set_args()

        results = dict()
        failed = False
        if self.source_dir:
            self._set_dir_defaults()
            self._set_root_dir()
            if not path.exists(self.source_dir):
                failed = True
                err_msg = f"{self.source_dir} directory does not exist"
            elif not path.isdir(self.source_dir):
                failed = True
                err_msg = f"{self.source_dir} is not a directory"
            else:
                for root_dir, filenames in self._traverse_dir_depth():
                    failed, err_msg, updated_results = self._load_files_in_dir(root_dir, filenames)
                    if failed:
                        break
                    results.update(updated_results)
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

        result = super(ActionModule, self).run(task_vars=task_vars)

        if failed:
            result['failed'] = failed
            result['message'] = err_msg
        elif self.hash_behaviour is not None and self.hash_behaviour != C.DEFAULT_HASH_BEHAVIOUR:
            merge_hashes = self.hash_behaviour == 'merge'
            existing_variables = {k: v for k, v in task_vars.items() if k in results}
            results = combine_vars(existing_variables, results, merge=merge_hashes)

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
            if (origin := self._task._origin) and origin.path:  # origin.path is not present for ad-hoc tasks
                current_dir = (
                    "/".join(origin.path.split('/')[:-1])
                )
                self.source_dir = path.join(current_dir, self.source_dir)

    def _log_walk(self, error):
        self._display.vvv(f"Issue with walking through {error.filename}: {error}")

    def _traverse_dir_depth(self):
        """ Recursively iterate over a directory and sort the files in
            alphabetical order. Do not iterate pass the set depth.
            The default depth is unlimited.
        """
        sorted_walk = list(walk(self.source_dir, onerror=self._log_walk, followlinks=True))
        sorted_walk.sort(key=lambda x: x[0])
        for current_root, current_dir, current_files in sorted_walk:
            # Depth 1 is the root, relative_to omits the root
            current_depth = len(pathlib.Path(current_root).relative_to(self.source_dir).parts) + 1
            if self.depth != 0 and current_depth > self.depth:
                continue
            current_files.sort()
            yield (current_root, current_files)

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
            except Exception as ex:
                raise AnsibleError(f'Invalid regular expression: {file_type!r}', obj=file_type) from ex
        return False

    def _is_valid_file_ext(self, source_file):
        """ Verify if source file has a valid extension
        Args:
            source_file (str): The full path of source file or source file.
        Returns:
            Bool
        """
        file_ext = path.splitext(source_file)
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
            err_msg = f"{filename!r} does not have a valid extension: {', '.join(self.valid_extensions)}"
        else:
            data = self._loader.load_from_file(filename, cache='none', trusted_as_template=True)

            self.show_content &= not SourceWasEncrypted.is_tagged_on(data)

            if data is None:  # support empty files, but not falsey values
                data = dict()

            if not isinstance(data, dict):
                failed = True
                err_msg = f"{filename!r} must be stored as a dictionary/hash"
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
                if path.join(self._task._role._role_path, filename) == path.join(root_dir, 'vars', 'main.yml'):
                    stop_iter = True
                    continue

            filepath = path.join(root_dir, filename)
            if self.files_matching:
                if not self.matcher.search(filename):
                    stop_iter = True

            if not stop_iter and not failed:
                if self.ignore_unknown_extensions:
                    if path.exists(filepath) and not self._ignore_file(filename) and self._is_valid_file_ext(filename):
                        failed, err_msg, loaded_data = self._load_files(filepath, validate_extensions=True)
                        if not failed:
                            results.update(loaded_data)
                else:
                    if path.exists(filepath) and not self._ignore_file(filename):
                        failed, err_msg, loaded_data = self._load_files(filepath, validate_extensions=True)
                        if not failed:
                            results.update(loaded_data)

        return failed, err_msg, results
