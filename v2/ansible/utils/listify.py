# (c) 2014 Michael DeHaan, <michael@ansible.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from six import iteritems, string_types

import re

from ansible.template import Templar
from ansible.template.safe_eval import safe_eval

__all__ = ['listify_lookup_plugin_terms']

LOOKUP_REGEX = re.compile(r'lookup\s*\(')

def listify_lookup_plugin_terms(terms, variables, loader):

    if isinstance(terms, basestring):
        # someone did:
        #    with_items: alist
        # OR
        #    with_items: {{ alist }}

        stripped = terms.strip()
        templar = Templar(loader=loader, variables=variables)
        if not (stripped.startswith('{') or stripped.startswith('[')) and not stripped.startswith("/") and not stripped.startswith('set([') and not LOOKUP_REGEX.search(terms):
            # if not already a list, get ready to evaluate with Jinja2
            # not sure why the "/" is in above code :)
            try:
                new_terms = templar.template("{{ %s }}" % terms)
                if isinstance(new_terms, basestring) and "{{" in new_terms:
                    pass
                else:
                    terms = new_terms
            except:
                pass
        else:
            terms = templar.template(terms)

        if '{' in terms or '[' in terms:
            # Jinja2 already evaluated a variable to a list.
            # Jinja2-ified list needs to be converted back to a real type
            return safe_eval(terms)

        if isinstance(terms, basestring):
            terms = [ terms ]

    return terms

