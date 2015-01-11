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


def check_list_of_one_list(term):
    # make sure term is not a list of one (list of one..) item
    # return the final non list item if so

    if isinstance(term,list) and len(term) == 1:
        term = term[0]
        if isinstance(term,list):
            term = check_list_of_one_list(term)

    return term



class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir


    def flatten(self, terms, inject):

        ret = []
        for term in terms:
            term = check_list_of_one_list(term)

            if term == 'None' or term == 'null':
                # ignore undefined items
                break

            if isinstance(term, basestring):
                # convert a variable to a list
                term2 = utils.listify_lookup_plugin_terms(term, self.basedir, inject)
                # but avoid converting a plain string to a list of one string
                if term2 != [ term ]:
                    term = term2

            if isinstance(term, list):
                # if it's a list, check recursively for items that are a list
                term = self.flatten(term, inject)
                ret.extend(term)
            else:
                ret.append(term)

        return ret


    def run(self, terms, inject=None, **kwargs):

        # see if the string represents a list and convert to list if so
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        if not isinstance(terms, list):
            raise errors.AnsibleError("with_flattened expects a list")

        ret = self.flatten(terms, inject)
        return ret

