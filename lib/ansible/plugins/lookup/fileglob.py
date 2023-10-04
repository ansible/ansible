# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

DOCUMENTATION = """
    name: fileglob
    author: Michael DeHaan
    version_added: "1.4"
    short_description: list files matching a pattern
    description:
        - Matches all files in a single directory, non-recursively, that match a pattern.
          It calls Python's "glob" library.
    options:
      _terms:
        description: path(s) of files to read
        required: True
    notes:
      - Patterns are only supported on files, not directory/paths.
      - See R(Ansible task paths,playbook_task_paths) to understand how file lookup occurs with paths.
      - Matching is against local system files on the Ansible controller.
        To iterate a list of files on a remote node, use the M(ansible.builtin.find) module.
      - Returns a string list of paths joined by commas, or an empty list if no files match. For a 'true list' pass O(ignore:wantlist=True) to the lookup.
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative files.
"""

EXAMPLES = """
- name: Display paths of all .txt files in dir
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', '/my/path/*.txt') }}

- name: Copy each file over that matches the given pattern
  ansible.builtin.copy:
    src: "{{ item }}"
    dest: "/etc/fooapp/"
    owner: "root"
    mode: 0600
  with_fileglob:
    - "/playbooks/files/fooapp/*"
"""

RETURN = """
  _list:
    description:
      - list of files
    type: list
    elements: path
"""

import os
import glob

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_bytes, to_text


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            term_file = os.path.basename(term)
            found_paths = []
            if term_file != term:
                found_paths.append(self.find_file_in_search_path(variables, 'files', os.path.dirname(term)))
            else:
                # no dir, just file, so use paths and 'files' paths instead
                if 'ansible_search_path' in variables:
                    paths = variables['ansible_search_path']
                else:
                    paths = [self.get_basedir(variables)]
                for p in paths:
                    found_paths.append(os.path.join(p, 'files'))
                    found_paths.append(p)

            for dwimmed_path in found_paths:
                if dwimmed_path:
                    globbed = glob.glob(to_bytes(os.path.join(dwimmed_path, term_file), errors='surrogate_or_strict'))
                    term_results = [to_text(g, errors='surrogate_or_strict') for g in globbed if os.path.isfile(g)]
                    if term_results:
                        ret.extend(term_results)
                        break
        return ret
