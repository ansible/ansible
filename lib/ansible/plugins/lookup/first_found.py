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
            but potentially others) return V(None) or an empty list respectively.
          - When V(True) and C(lookup) or C(query) specifies O(ignore:errors='ignore'), no file found will return an empty
            list and other potential errors return V(None) or empty list depending on the template call
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

import collections.abc as c
import os
import re
import typing as t

from ansible._internal import _task
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible._internal._templating import _jinja_common
from ansible._internal._templating import _jinja_plugins
from ansible import template as _template
from ansible.utils.path import unfrackpath
from ansible.utils.display import Display
from ansible.module_utils.datatag import native_type_name


def _split_on(target: str, terms: str | list[str], splitters: str) -> list[str]:
    termlist: list[str] = []

    if isinstance(terms, str):
        split_terms = re.split(r'[%s]' % ''.join(map(re.escape, splitters)), terms)

        if split_terms == [terms]:
            termlist = [terms]
        else:
            Display().deprecated(
                msg=f'Automatic splitting of {target} on {splitters!r} is deprecated.',
                help_text=f'Provide a list of paths for {target} instead.',
                version='2.23',
                obj=terms,
            )

            termlist = split_terms
    else:
        # added since options will already listify
        for term in terms:
            termlist.extend(_split_on(target, term, splitters))

    return termlist


class LookupModule(LookupBase):
    accept_args_markers = True  # terms are allowed to be undefined
    accept_lazy_markers = True  # terms are allowed to be undefined

    def _process_terms(self, terms: c.Sequence, variables: dict[str, t.Any]) -> list[str]:

        total_search = []

        # can use a dict instead of list item to pass inline config
        for term in terms:
            if isinstance(term, c.Mapping):
                self.set_options(var_options=variables, direct=term)
                files = self.get_option('files')
                files_description = "the 'files' option"
            elif isinstance(term, str):
                files = [term]
                files_description = "files"
            elif isinstance(term, c.Sequence):
                partial = self._process_terms(term, variables)
                total_search.extend(partial)
                continue
            else:
                raise AnsibleError(f"Invalid term supplied. A string, dict or list is required, not {native_type_name(term)!r}).")

            paths = self.get_option('paths')

            # magic extra splitting to create lists
            filelist = _split_on(files_description, files, ',;')
            pathlist = _split_on('the "paths" option', paths, ',:;')

            # create search structure
            if pathlist:
                for path in pathlist:
                    for fn in filelist:
                        f = os.path.join(path, fn)
                        total_search.append(f)
            else:
                # NOTE: this is now 'extend', previously it would clobber all options, but we deemed that a bug
                total_search.extend(filelist)

        return total_search

    def run(self, terms: list, variables=None, **kwargs):
        if (first_marker := _template.get_first_marker_arg((), kwargs)) is not None:
            first_marker.trip()

        if _jinja_plugins._LookupContext.current().invoked_as_with:
            # we're being invoked by TaskExecutor.get_loop_items(), special backwards compatibility behavior
            terms = _recurse_terms(terms, omit_undefined=True)  # recursively drop undefined values from terms for backwards compatibility

            # invoked_as_with shouldn't be possible outside a TaskContext
            te_action = _task.TaskContext.current().task.action  # FIXME: this value has not been templated, it should be (historical problem)...

            # based on the presence of `var`/`template`/`file` in the enclosing task action name, choose a subdir to search
            for subdir in ['template', 'var', 'file']:
                if subdir in te_action:
                    break

            subdir += "s"  # convert to the matching directory name
        else:
            terms = _recurse_terms(terms, omit_undefined=False)  # undefined values are only omitted when invoked using `with`

            subdir = None

        self.set_options(var_options=variables, direct=kwargs)

        if not terms:
            terms = self.get_option('files')

        total_search = self._process_terms(terms, variables)

        # NOTE: during refactor noticed that the 'using a dict' as term
        # is designed to only work with 'one' otherwise inconsistencies will appear.
        # see other notes below.

        for fn in total_search:
            # get subdir if set by task executor, default to files otherwise
            path = self.find_file_in_search_path(variables, subdir, fn, ignore_missing=True)

            # exit if we find one!
            if path is not None:
                return [unfrackpath(path, follow=False)]

        skip = self.get_option('skip')

        # if we get here, no file was found
        if skip:
            # NOTE: global skip won't matter, only last 'skip' value in dict term
            return []

        raise AnsibleError("No file was found when using first_found.")


def _recurse_terms(o: t.Any, omit_undefined: bool) -> t.Any:
    """Recurse through supported container types, optionally omitting undefined markers and tripping all remaining markers, returning the result."""
    match o:
        case dict():
            return {k: _recurse_terms(v, omit_undefined) for k, v in o.items() if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker))}
        case list():
            return [_recurse_terms(v, omit_undefined) for v in o if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker))]
        case tuple():
            return tuple(_recurse_terms(v, omit_undefined) for v in o if not (omit_undefined and isinstance(v, _jinja_common.UndefinedMarker)))
        case _jinja_common.Marker():
            o.trip()
        case _:
            return o
