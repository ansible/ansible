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
        stripped = terms.strip()
        templar = Templar(loader=loader, variables=variables)
        terms = templar.template(terms, convert_bare=True)

        terms = safe_eval(terms)

        if isinstance(terms, basestring):
            terms = [ terms ]

    return terms
