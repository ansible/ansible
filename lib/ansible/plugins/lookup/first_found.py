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
    options:
      _terms:
        description: list of file names
        required: True
      paths:
        description: list of paths in which to look for the files
"""

EXAMPLES = """
- name: show first existin file
  debug: var=item
  with_first_found:
    - "/path/to/foo.txt"
    - "bar.txt"  # will be looked in files/ dir relative to play or in role
    - "/path/to/biz.txt"

- name: copy first existing file found to /some/file
  copy: src={{item}} dest=/some/file
  with_first_found:
    - foo
    - "{{inventory_hostname}}
    - bar

- name: same copy but specific paths
  copy: src={{item}} dest=/some/file
  with_first_found:
    files:
      - foo
      - "{{inventory_hostname}}
      - bar
    paths:
      - /tmp/production
      - /tmp/staging

- name: INTERFACES | Create Ansible header for /etc/network/interfaces
  template:
    src: "{{ item }}"
    dest: "/etc/foo.conf"
  with_first_found:
    - "{{ ansible_virtualization_type }}_foo.conf"
    - "default_foo.conf"
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
        else:
            if skip:
                return []
            else:
                raise AnsibleLookupError("No file was found when using with_first_found. Use the 'skip: true' option to allow this task to be skipped if no "
                                         "files are found")
