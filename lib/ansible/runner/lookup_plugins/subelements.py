# (c) 2013, Serge van Ginderachter <serge@vanginderachter.be>
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

import ansible.utils as utils
import ansible.errors as errors


class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir


    def run(self, terms, inject=None, **kwargs):
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        terms[0] = utils.listify_lookup_plugin_terms(terms[0], self.basedir, inject)

        if not isinstance(terms, list) or not len(terms) == 2:
            raise errors.AnsibleError(
                "subelements lookup expects a list of two items, first a dict or a list, and second a string")
        terms[0] = utils.listify_lookup_plugin_terms(terms[0], self.basedir, inject)
        if not isinstance(terms[0], (list, dict)) or not isinstance(terms[1], basestring):
            raise errors.AnsibleError(
                "subelements lookup expects a list of two items, first a dict or a list, and second a string")

        if isinstance(terms[0], dict): # convert to list:
            if terms[0].get('skipped',False) != False:
                # the registered result was completely skipped
                return []
            elementlist = []
            for key in terms[0].iterkeys():
                elementlist.append(terms[0][key])
        else: 
            elementlist = terms[0]
        subelement = terms[1]

        ret = []
        for item0 in elementlist:
            if not isinstance(item0, dict):
                raise errors.AnsibleError("subelements lookup expects a dictionary, got '%s'" %item0)
            if item0.get('skipped',False) != False:
                # this particular item is to be skipped
                continue 
            if not subelement in item0:
                raise errors.AnsibleError("could not find '%s' key in iterated item '%s'" % (subelement, item0))
            if not isinstance(item0[subelement], list):
                raise errors.AnsibleError("the key %s should point to a list, got '%s'" % (subelement, item0[subelement]))
            sublist = item0.pop(subelement, [])
            for item1 in sublist:
                ret.append((item0, item1))

        return ret

