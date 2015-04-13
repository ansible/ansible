# (c) 2015, Brian Coca <bcoca@ansible.com>
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

from ansible.plugins.lookup import LookupBase
import urllib2

class LookupModule(LookupBase):


    def run(self, terms, inject=None, **kwargs):

        if isinstance(terms, basestring):
            terms = [ terms ]

        ret = []
        for term in terms:
            try:
                r = urllib2.Request(term)
                response = urllib2.urlopen(r)
            except URLError as e:
                utils.warnings("Failed lookup url for %s : %s" % (term, str(e)))
                continue
            except HTTPError as e:
                utils.warnings("Recieved HTTP error for %s : %s" % (term, str(e)))
                continue

            for line in response.read().splitlines():
                ret.append(line)

        return ret
