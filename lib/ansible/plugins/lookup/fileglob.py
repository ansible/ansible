# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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
'''
DOCUMENTATION:
    author:
        - Michael DeHaan <michael.dehaan@gmail.com>
    lookup: fileglob
    version_added: historical
    short_description: return a list of matched files
    description:
        - Given a shell glob (?, * [1-9]) return a list of files that matched from the local filesystem.
        - Uses the python glob library to accomplish this .
    options:
        _raw:
            description:
                - the list of path globs to match
            type: list
            element_type: string
            required: True
    notes:
        - The first top relative path to match will be used using normal lookup search paths, i.e if in a role and looking for files/*
          the files/ directory in the role will be chosen over files/ directory in play.
EXAMPLES:
    - name: "copy configs"
      copy: src={{item}} dest=/etc/conf.d/
      with_fileglob:
        - 'files/conf.d/*.conf'

    - name: "list all yaml files"
      debug: msg="{{ lookup('fileglob', ['/etc/*.yml', 'vars/*.yml', 'vars/*/*.yml' ]) }}"
RETURN:
    _list:
        description:
            - list of files matched
        type: list
        element_type: string
'''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import glob

from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes, to_text


class LookupModule(LookupBase):

    GLOBS = frozenset(['?', '*', '['])

    def run(self, terms, variables=None, **kwargs):

        ret = []
        for term in terms:

            # find smallest unglobbed match
            min_spot = len(term)
            for symbol in self.GLOBS:
                x = term.find(symbol, 0, min_spot)
                if x > 0:
                    min_spot = x

            if min_spot == len(term):
                dwimmed_path = self.find_file_in_search_path(variables, 'files', term)
                ret.append(dwimmed_path)
            else:
                term_root = term[:min_spot]
                dwimmed_path = self.find_file_in_search_path(variables, 'files', os.path.dirname(term_root))
                globbed = glob.glob(to_bytes(os.path.join(dwimmed_path, os.path.basename(term_root)) + term[min_spot:], errors='surrogate_or_strict'))
                ret.extend(to_text(g, errors='surrogate_or_strict') for g in globbed if os.path.isfile(g))

        return ret
