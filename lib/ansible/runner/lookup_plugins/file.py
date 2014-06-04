# (c) 2012, Daniel Hokka Zakrisson <daniel@hozac.com>
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

from ansible import utils, errors
import os
import codecs

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        ret = []

        # this can happen if the variable contains a string, strictly not desired for lookup
        # plugins, but users may try it, so make it work.
        if not isinstance(terms, list):
            terms = [ terms ]

        for term in terms:
            basedir_path  = utils.path_dwim(self.basedir, term)
            relative_path = None
            playbook_path = None

            # Special handling of the file lookup, used primarily when the
            # lookup is done from a role. If the file isn't found in the
            # basedir of the current file, use dwim_relative to look in the
            # role/files/ directory, and finally the playbook directory
            # itself (which will be relative to the current working dir)
            if '_original_file' in inject:
                relative_path = utils.path_dwim_relative(inject['_original_file'], 'files', term, self.basedir, check=False)
            if 'playbook_dir' in inject:
                playbook_path = os.path.join(inject['playbook_dir'], term)

            for path in (basedir_path, relative_path, playbook_path):
                if path and os.path.exists(path):
                    ret.append(codecs.open(path, encoding="utf8").read().rstrip())
                    break
            else:
                raise errors.AnsibleError("could not locate file in lookup: %s" % term)

        return ret
