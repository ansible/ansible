# (c) 2015, Alejandro Guirao <lekumberri@gmail.com>
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

import shelve

from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_bytes, to_text


class LookupModule(LookupBase):

    def read_shelve(self, shelve_filename, key):
        """
        Read the value of "key" from a shelve file
        """
        d = shelve.open(to_bytes(shelve_filename))
        res = d.get(key, None)
        d.close()
        return res

    def run(self, terms, variables=None, **kwargs):

        if not isinstance(terms, list):
            terms = [terms]

        ret = []

        for term in terms:
            paramvals = {"file": None, "key": None}
            params = term.split()

            try:
                for param in params:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value

            except (ValueError, AssertionError) as e:
                # In case "file" or "key" are not present
                raise AnsibleError(e)

            key = paramvals['key']

            # Search also in the role/files directory and in the playbook directory
            shelvefile = self.find_file_in_search_path(variables, 'files', paramvals['file'])

            if shelvefile:
                res = self.read_shelve(shelvefile, key)
                if res is None:
                    raise AnsibleError("Key %s not found in shelve file %s" % (key, shelvefile))
                # Convert the value read to string
                ret.append(to_text(res))
                break
            else:
                raise AnsibleError("Could not locate shelve file in lookup: %s" % paramvals['file'])

        return ret
