# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: file_found
    author: Pierre Monsimier <pierre.monsimier@capgemini.com>
    short_description: return first file found from list
    description:
      - this lookup checks a list of files and paths and returns a list of full paths of those found.
      - As all lookups, when fed relative paths it will try use the current task's location first and go up the chain
        to the containing role/play/include/etc's location.
      - The list of files has precedence over the paths searched.
        i.e, A task in a  role has a 'file1' in the play's relative path, this will be used, 'file2' in role's relative path will not.
    options:
      _terms:
        description: list of file names
        required: True
      paths:
        description: list of paths in which to look for the files
"""

EXAMPLES = """
- name: show all existing files
  debug: msg={{lookup('file_found', listOfFiles)}}
  vars:
    listOfFiles:
      - "/path/to/foo.txt"
      - "bar.txt"  # will be looked in files/ dir relative to role and/or play
      - "/path/to/biz.txt"


- name: "Includes vars from all existing files"
  include_vars:
    file: "{{ item }}"
  with_file_found:
    - "/path/to/varFile.yml"
    - "/path/to/anotherVarFile.yml"
"""

RETURN = """
  _raw:
    description:
      - paths of files found
"""
import os

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleFileNotFound, AnsibleLookupError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        skip = False

        skip, total_search = self.build_paths_to_search(skip, terms)

        all_files_found = []
        for fn in total_search:
            try:
                fn = self._templar.template(fn)
            except (AnsibleUndefinedVariable, UndefinedError):
                continue

            # get subdir if set by task executor, default to files otherwise
            subdir = getattr(self, '_subdir', 'files')
            path = None
            path = self.find_file_in_search_path(variables, subdir, fn, ignore_missing=True)
            if path is not None:
                all_files_found.append(path)
        if len(all_files_found)>0:
            return all_files_found
        if skip:
            return []
        raise AnsibleLookupError("No file was found when using with_file_found. Use the 'skip: true' option to allow this task to be skipped if no "
                                 "files are found")

    def build_paths_to_search(self, skip, terms):
        all_params_are_files = True
        total_search = []
        for term in terms:
            if isinstance(term, dict):
                all_params_are_files = False
                files = term.get('files', [])
                paths = term.get('paths', [])
                skip = boolean(term.get('skip', False), strict=False)

                total_search = self.concat_paths_and_files(files, paths, total_search)
            else:
                total_search.append(term)

        if all_params_are_files:
            # Allows to use this lookup plugin when used jinja style (see #14190)
            total_search = self._flatten(terms)
        return skip, total_search

    def concat_paths_and_files(self, files, paths, total_search):
        filelist = files
        if isinstance(files, string_types):
            files = files.replace(',', ' ')
            files = files.replace(';', ' ')
            filelist = files.split(' ')
        pathlist = paths
        if paths:
            if isinstance(paths, string_types):
                paths = paths.replace(',', ' ')
                paths = paths.replace(':', ' ')
                paths = paths.replace(';', ' ')
                pathlist = paths.split(' ')
        if not pathlist:
            total_search = filelist
        else:
            for path in pathlist:
                for fn in filelist:
                    f = os.path.join(path, fn)
                    total_search.append(f)
        return total_search
