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

import os
import glob
from ansible import utils

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, **kwargs):
        if isinstance(terms, basestring):
            terms = [ terms ]
        ret = []
        for term in terms:
            dwimterms = utils.path_dwim(self.basedir, term)
            # This skips whatever prefix the dwim added, leaving just the filename for the item
            i = -1
            while dwimterms[i] == term[i] and -i < len(term) and -i < len(dwimterms):
                i = i - 1
            orig_prefix_len = i + 1
            dwim_prefix_len = len(dwimterms) + i + 1
            ret.extend([ term[:orig_prefix_len] + f[dwim_prefix_len:]
                         for f in glob.glob(dwimterms) if os.path.isfile(f) ])
        return ret
