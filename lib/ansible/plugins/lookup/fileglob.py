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
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

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
