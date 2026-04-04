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
        - Matches all files in directory that match a pattern.
          It calls Python's "L(Path.glob, https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob)" library.
    options:
      _terms:
        description: path(s) of files to read
        required: True
    notes:
      - See R(Ansible task paths,playbook_task_paths) to understand how file lookup occurs with paths.
      - Matching is against local system files on the Ansible controller.
        To iterate a list of files on a remote node, use the M(ansible.builtin.find) module.
      - Returns a list of string paths, or an empty list if no files match.
    seealso:
      - ref: playbook_task_paths
        description: Search paths used for relative files.
"""

EXAMPLES = """
- name: Display paths of all .txt files in dir
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', '/my/path/*.txt') }}

- name: Display paths of all bar.py files in all directories
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', '*/bar.py') }}

- name: Display paths of all .md files in recursively directories
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', '**/*.md') }}

- name: Display paths of .json start name with « 2 », « 3 » or « 23 »
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', 'path/[23]-foobar.json') }}

- name: Display paths of .json start name without « 2 », « 3 » or « 23 »
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', 'path/[!23]-foobar.json') }}

- name: Display paths of .txt files matches any single character in foo directory
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', 'foo/b?r.txt') }}

- name: Display paths of all .json start name with « 2 », « 3 » or « 23 » recursively in matches any single character dir
  ansible.builtin.debug: msg={{ lookup('ansible.builtin.fileglob', 'f?o/**/[23]-*.json') }}

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

from pathlib import Path

from ansible.plugins.lookup import LookupBase
from ansible.module_utils.common.text.converters import to_text


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        file_paths = []

        if "ansible_search_path" in variables:
            paths = [Path(p) for p in variables["ansible_search_path"]]
        else:
            paths = [Path(self.get_basedir(variables))]

        found_paths = []
        for path in paths:
            p = Path(path) / "files"
            found_paths.append(p)
            found_paths.append(p.parent)

        for term in terms:
            for path in found_paths:
                term_results = [
                    to_text(str(g), errors="surrogate_or_strict")
                    for g in path.glob(term)
                    if g.is_file()
                ]
                if term_results:
                    file_paths.extend(term_results)
                    break

        return file_paths
