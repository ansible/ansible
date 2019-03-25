# (c) 2013, seth vidal <skvidal@fedoraproject.org> red hat, inc
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: first_found
    author: Seth Vidal <skvidal@fedoraproject.org>
    version_added: historical
    short_description: return first file found from list
    description:
      - this lookup checks a list of files and paths and returns the full path to the first combination found.
      - As all lookups, when fed relative paths it will try use the current task's location first and go up the chain
        to the containing role/play/include/etc's location.
      - The list of files has precedence over the paths searched.
        i.e, A task in a  role has a 'file1' in the play's relative path, this will be used, 'file2' in role's relative path will not.
      - Either a list of files C(_terms) or a key `files` with a list of files is required for this plugin to operate.
    notes:
      - This lookup can be used in 'dual mode', either passing a list of file names or a dictionary that has C(files) and C(paths).
    options:
      _terms:
        description: list of file names
      files:
        description: list of file names
      paths:
        description: list of paths in which to look for the files
      skip:
        type: boolean
        default: False
        description: Return an empty list if no file is found, instead of an error.
        deprecated:
            why: A generic that applies to all errors exists for all lookups.
            version: "2.8"
            alternative: The generic ``errors=ignore``
"""

EXAMPLES = """
- name: show first existing file or ignore if none do
  debug: msg={{lookup('first_found', findme, errors='ignore')}}
  vars:
    findme:
      - "/path/to/foo.txt"
      - "bar.txt"  # will be looked in files/ dir relative to role and/or play
      - "/path/to/biz.txt"

- name: |
        copy first existing file found to /some/file,
        looking in relative directories from where the task is defined and
        including any play objects that contain it
  copy: src={{lookup('first_found', findme)}} dest=/some/file
  vars:
    findme:
      - foo
      - "{{inventory_hostname}}"
      - bar

- name: same copy but specific paths
  copy: src={{lookup('first_found', params)}} dest=/some/file
  vars:
    params:
      files:
        - foo
        - "{{inventory_hostname}}"
        - bar
      paths:
        - /tmp/production
        - /tmp/staging

- name: INTERFACES | Create Ansible header for /etc/network/interfaces
  template:
    src: "{{ lookup('first_found', findme)}}"
    dest: "/etc/foo.conf"
  vars:
    findme:
      - "{{ ansible_virtualization_type }}_foo.conf"
      - "default_foo.conf"

- name: read vars from first file found, use 'vars/' relative subdir
  include_vars: "{{lookup('first_found', params)}}"
  vars:
    params:
      files:
        - '{{ansible_os_distribution}}.yml'
        - '{{ansible_os_family}}.yml'
        - default.yml
      paths:
        - 'vars'
"""

RETURN = """
  _raw:
    description:
      - path to file found
"""
import os

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleFileNotFound, AnsibleLookupError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        anydict = False
        skip = False

        for term in terms:
            if isinstance(term, dict):
                anydict = True

        total_search = []
        if anydict:
            for term in terms:
                if isinstance(term, dict):

                    if 'skip' in term:
                        self._display.deprecated('Use errors="ignore" instead of skip', version='2.12')

                    files = term.get('files', [])
                    paths = term.get('paths', [])
                    skip = boolean(term.get('skip', False), strict=False)

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
                else:
                    total_search.append(term)
        else:
            total_search = self._flatten(terms)

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
                return [path]
        if skip:
            return []
        raise AnsibleLookupError("No file was found when using first_found. Use the 'skip: true' option to allow this task to be skipped if no "
                                 "files are found")
