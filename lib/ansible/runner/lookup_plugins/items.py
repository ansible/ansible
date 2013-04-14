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

from ansible.utils import safe_eval
import ansible.utils.template as template

def flatten(terms):
    ret = []
    for term in terms:
        if isinstance(term, list):
            ret.extend(term)
        else:
            ret.append(term)
    return ret

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):
        if isinstance(terms, basestring):
            # somewhat did:
            #    with_items: alist
            # OR
            #    with_items: {{ alist }}
            if not '{' in terms and not '[' in terms:
                terms = '{{ %s }}' % terms
                terms = template.template(self.basedir, terms, inject)
            if '{' or '[' in terms:
                # Jinja2 already evaluated a variable to a list.
                # Jinja2-ified list needs to be converted back to a real type
                # TODO: something a bit less heavy than eval
                terms = safe_eval(terms)
            terms = [ terms ]
        return flatten(terms)


