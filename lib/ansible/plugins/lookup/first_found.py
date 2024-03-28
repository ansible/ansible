# (c) 2013, seth vidal <skvidal@fedoraproject.org> red hat, inc
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: first_found
    author: Seth Vidal (!UNKNOWN) <skvidal@fedoraproject.org>
    version_added: historical
    short_description: return first file found from list
    description:
      - This lookup checks a list of files and paths and returns the full path to the first combination found.
      - As all lookups, when fed relative paths it will try use the current task's location first and go up the chain
        to the containing locations of role / play / include and so on.
      - The list of files has precedence over the paths searched.
        For example, A task in a role has a 'file1' in the play's relative path, this will be used, 'file2' in role's relative path will not.
      - Either a list of files O(_terms) or a key O(files) with a list of files is required for this plugin to operate.
    notes:
      - This lookup can be used in 'dual mode', either passing a list of file names or a dictionary that has O(files) and O(paths).
    options:
      _terms:
        description: A list of file names.
      files:
        description: A list of file names.
        type: list
        elements: string
        default: []
      paths:
        description: A list of paths in which to look for the files.
        type: list
        elements: string
        default: []
      skip:
        type: boolean
        default: False
        description:
          - When V(True), return an empty list when no files are matched.
          - This is useful when used with C(with_first_found), as an empty list return to C(with_) calls
            causes the calling task to be skipped.
          - When used as a template via C(lookup) or C(query), setting O(skip=True) will *not* cause the task to skip.
            Tasks must handle the empty list return from the template.
          - When V(False) and C(lookup) or C(query) specifies O(ignore:errors='ignore') all errors (including no file found,
            but potentially others) return an empty string or an empty list respectively.
          - When V(True) and C(lookup) or C(query) specifies O(ignore:errors='ignore'), no file found will return an empty
            list and other potential errors return an empty string or empty list depending on the template call
            (in other words return values of C(lookup) vs C(query)).
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative paths/files.
"""

EXAMPLES = """
- name: Set _found_file to the first existing file, raising an error if a file is not found
  ansible.builtin.set_fact:
    _found_file: "{{ lookup('ansible.builtin.first_found', findme) }}"
  vars:
    findme:
      - /path/to/foo.txt
      - bar.txt  # will be looked in files/ dir relative to role and/or play
      - /path/to/biz.txt

- name: Set _found_file to the first existing file, or an empty list if no files found
  ansible.builtin.set_fact:
    _found_file: "{{ lookup('ansible.builtin.first_found', files, paths=['/extra/path'], skip=True) }}"
  vars:
    files:
      - /path/to/foo.txt
      - /path/to/bar.txt

- name: Include tasks only if one of the files exist, otherwise skip the task
  ansible.builtin.include_tasks:
    file: "{{ item }}"
  with_first_found:
    - files:
      - path/tasks.yaml
      - path/other_tasks.yaml
      skip: True

- name: Include tasks only if one of the files exists, otherwise skip
  ansible.builtin.include_tasks: '{{ tasks_file }}'
  when: tasks_file != ""
  vars:
    tasks_file: "{{ lookup('ansible.builtin.first_found', files=['tasks.yaml', 'other_tasks.yaml'], errors='ignore') }}"

- name: |
        copy first existing file found to /some/file,
        looking in relative directories from where the task is defined and
        including any play objects that contain it
  ansible.builtin.copy:
    src: "{{ lookup('ansible.builtin.first_found', findme) }}"
    dest: /some/file
  vars:
    findme:
      - foo
      - "{{ inventory_hostname }}"
      - bar

- name: same copy but specific paths
  ansible.builtin.copy:
    src: "{{ lookup('ansible.builtin.first_found', params) }}"
    dest: /some/file
  vars:
    params:
      files:
        - foo
        - "{{ inventory_hostname }}"
        - bar
      paths:
        - /tmp/production
        - /tmp/staging

- name: INTERFACES | Create Ansible header for /etc/network/interfaces
  ansible.builtin.template:
    src: "{{ lookup('ansible.builtin.first_found', findme)}}"
    dest: "/etc/foo.conf"
  vars:
    findme:
      - "{{ ansible_virtualization_type }}_foo.conf"
      - "default_foo.conf"

- name: read vars from first file found, use 'vars/' relative subdir
  ansible.builtin.include_vars: "{{lookup('ansible.builtin.first_found', params)}}"
  vars:
    params:
      files:
        - '{{ ansible_distribution }}.yml'
        - '{{ ansible_os_family }}.yml'
        - default.yml
      paths:
        - 'vars'
"""

RETURN = """
  _raw:
    description:
      - path to file found
    type: list
    elements: path
"""
import os

from collections.abc import Mapping, Sequence

from jinja2.exceptions import UndefinedError

from ansible.errors import AnsibleLookupError, AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.plugins.lookup import LookupBase
from ansible.utils.path import unfrackpath


def _splitter(value, chars):
    chars = set(chars)
    v = ''
    for c in value:
        if c in chars:
            yield v
            v = ''
            continue
        v += c
    yield v


def _split_on(terms, spliters=','):
    termlist = []
    if isinstance(terms, string_types):
        termlist = list(_splitter(terms, spliters))
    else:
        # added since options will already listify
        for t in terms:
            termlist.extend(_split_on(t, spliters))
    return termlist


class LookupModule(LookupBase):

    def _process_terms(self, terms, variables, kwargs):

        total_search = []
        skip = False

        # can use a dict instead of list item to pass inline config
        for term in terms:
            if isinstance(term, Mapping):
                self.set_options(var_options=variables, direct=term)
                files = self.get_option('files')
            elif isinstance(term, string_types):
                files = [term]
            elif isinstance(term, Sequence):
                partial, skip = self._process_terms(term, variables, kwargs)
                total_search.extend(partial)
                continue
            else:
                raise AnsibleLookupError("Invalid term supplied, can handle string, mapping or list of strings but got: %s for %s" % (type(term), term))

            paths = self.get_option('paths')

            # NOTE: this is used as 'global' but  can be set many times?!?!?
            skip = self.get_option('skip')

            # magic extra splitting to create lists
            filelist = _split_on(files, ',;')
            pathlist = _split_on(paths, ',:;')

            # create search structure
            if pathlist:
                for path in pathlist:
                    for fn in filelist:
                        f = os.path.join(path, fn)
                        total_search.append(f)
            elif filelist:
                # NOTE: this is now 'extend', previously it would clobber all options, but we deemed that a bug
                total_search.extend(filelist)
            else:
                total_search.append(term)

        return total_search, skip

    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        if not terms:
            terms = self.get_option('files')

        total_search, skip = self._process_terms(terms, variables, kwargs)

        # NOTE: during refactor noticed that the 'using a dict' as term
        # is designed to only work with 'one' otherwise inconsistencies will appear.
        # see other notes below.

        # actually search
        subdir = getattr(self, '_subdir', 'files')

        path = None
        for fn in total_search:

            try:
                fn = self._templar.template(fn)
            except (AnsibleUndefinedVariable, UndefinedError):
                # NOTE: backwards compat ff behaviour is to ignore errors when vars are undefined.
                #       moved here from task_executor.
                continue

            # get subdir if set by task executor, default to files otherwise
            path = self.find_file_in_search_path(variables, subdir, fn, ignore_missing=True)

            # exit if we find one!
            if path is not None:
                return [unfrackpath(path, follow=False)]

        # if we get here, no file was found
        if skip:
            # NOTE: global skip won't matter, only last 'skip' value in dict term
            return []
        raise AnsibleLookupError("No file was found when using first_found.")
