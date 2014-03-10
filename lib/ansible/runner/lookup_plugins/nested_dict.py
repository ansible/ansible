# (c) 2013, Robert Verspuy <robert@exa.nl>
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

        if not isinstance(terms, list) or not len(terms) > 1:
            raise errors.AnsibleError(
                "nested_dict lookup expects a list of at least two items")
        terms[0] = utils.listify_lookup_plugin_terms(terms[0], self.basedir, inject)
        if not isinstance(terms[0], dict):
            raise errors.AnsibleError(
                "nested_dict lookup expects a list of two items, first a dict")

        if terms[0].get('skipped',False) != False:
            # the registered result was completely skipped
            return []
        elementlist = terms[0]
        subelement = terms[1]

        ret = []
        for key0,item0 in elementlist.iteritems():
            if not isinstance(item0, dict):
                raise errors.AnsibleError("subelements lookup expects a dictionary, got '%s'" %item0)
            if item0.get('skipped',False) != False:
                # this particular item is to be skipped
                continue 
            if not subelement in item0:
                # if subelement not exist, we can skip this element and not raise an error... ???
                #raise errors.AnsibleError("could not find '%s' key in iterated item '%s'" % (subelement, item0))
                continue
            if not isinstance(item0[subelement], (list,dict)):
                raise errors.AnsibleError("the key %s should point to a list or dict, got '%s'" % (subelement, item0[subelement]))
            subdict = dict()
            if isinstance(item0[subelement], dict):
                subdict = item0.pop(subelement, [])
            elif isinstance(item0[subelement], list):
                i=0
                for val in item0[subelement]:
                    subdict[i] = val
                    i+=1

            for key1,item1 in subdict.iteritems():
                subret = []
                subret.append((key0, item0))
                subret.append((key1, item1))
                ret.append(subret)

        return ret

