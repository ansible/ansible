# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: fileglob
    author: Michael DeHaan <michael.dehaan@gmail.com>
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
      - Matching is against local system files on the Ansible controller.
        To iterate a list of files on a remote node, use the M(find) module.
      - Returns a string list of paths joined by commas, or an empty list if no files match. For a 'true list' pass C(wantlist=True) to the lookup.
"""

EXAMPLES = """
- name: Display paths of all .txt files in dir
  debug: msg={{ lookup('fileglob', '/my/path/*.txt') }}

- name: Copy each file over that matches the given pattern
  copy:
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
"""

import os
import glob

from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_text


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:
            term_file = os.path.basename(term)
            dwimmed_path = self.find_file_in_search_path(variables, 'files', os.path.dirname(term))
            if dwimmed_path:
                globbed = glob.glob(to_bytes(os.path.join(dwimmed_path, term_file), errors='surrogate_or_strict'))
                ret.extend(to_text(g, errors='surrogate_or_strict') for g in globbed if os.path.isfile(g))
        return ret
