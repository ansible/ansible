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

import ansible.utils as utils
import ansible.errors as errors
import re

# regular expression to match jinja expressions that contain
# "item[*]" or "item.*" subexpressions
item_regex = re.compile(r"[^a-zA-Z0-9_]*item(\[\d+\]|\.\d+)")

def flatten(terms):
    ret = []
    for term in terms:
        if isinstance(term, list):
            ret.extend(term)
        elif isinstance(term, tuple):
            ret.extend(term)
        else:
            ret.append(term)
    return ret

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def __lookup_injects(self, terms, inject):
        # loop_paths:
        #   A list of all possible paths/branches in the nested loop.
        #   Each path/branch is represented as a list of the values that are
        #   in effect at each step in the path. The index in a path's
        #   list denotes the step number (loop level). So, for example,
        #   loop_items[0][0] is set to the value that is in effect at the
        #   first step of the first possible path in the loop.
        loop_paths = [[]]

        for loop_index, term in enumerate(terms):
            new_paths = []
            for path in loop_paths:
                if loop_index != 0 and isinstance(term, basestring) and item_regex.search(term):
                    # Inject values of previous steps in the current loop
                    # path, so that, at each step, the value of the previous
                    # steps can be used when evaluating expressions that 
                    # contain "item[*]" or "item.*"
                    item = []
                    for step in path:
                        item.append(step)
                    inject['item'] = item
                intermediate = utils.listify_lookup_plugin_terms(term, self.basedir, inject)
                values = flatten(intermediate)
                for value in values:
                    new_paths.append(path + [value])
            loop_paths = new_paths

        return loop_paths

    def run(self, terms, inject=None, **kwargs):
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        loop_paths = self.__lookup_injects(terms, inject)

        # There must be at least one possible path in the loop
        if not loop_paths[0]:
            raise errors.AnsibleError("with_nested requires at least one element in the first (nesting) list")

        return loop_paths
