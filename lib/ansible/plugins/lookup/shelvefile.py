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

import shelve
import os
from ansible import utils, errors

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def read_shelve(self, shelve_filename, key):
        """
        Read the value of "key" from a shelve file
        """
        d = shelve.open(shelve_filename)
        res = d.get(key, None)
        d.close()
        return res

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        ret = []

        if not isinstance(terms, list):
            terms = [ terms ]

        for term in terms:
            playbook_path = None
            relative_path = None
            paramvals = {"file": None, "key": None}
            params = term.split()

            try:
                for param in params:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value

            except (ValueError, AssertionError), e:
                # In case "file" or "key" are not present
                raise errors.AnsibleError(e)

            file = paramvals['file']
            key = paramvals['key']
            basedir_path  = utils.path_dwim(self.basedir, file)

            # Search also in the role/files directory and in the playbook directory
            if '_original_file' in inject:
                relative_path = utils.path_dwim_relative(inject['_original_file'], 'files', file, self.basedir, check=False)
            if 'playbook_dir' in inject:
                playbook_path = os.path.join(inject['playbook_dir'], file)

            for path in (basedir_path, relative_path, playbook_path):
                if path and os.path.exists(path):
                    res = self.read_shelve(path, key)
                    if res is None:
                        raise errors.AnsibleError("Key %s not found in shelve file %s" % (key, file))
                    # Convert the value read to string
                    ret.append(str(res))
                    break
            else:
                raise errors.AnsibleError("Could not locate shelve file in lookup: %s" % file)

        return ret
