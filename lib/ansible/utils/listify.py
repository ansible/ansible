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

from collections import Iterable
from ansible.template import Templar
from ansible.template.safe_eval import safe_eval

__all__ = ['listify_lookup_plugin_terms']

#FIXME: probably just move this into lookup plugin base class
def listify_lookup_plugin_terms(terms, templar, loader, fail_on_undefined=False, convert_bare=True):

    if isinstance(terms, basestring):
        stripped = terms.strip()
        #FIXME: warn/deprecation on bare vars in with_ so we can eventually remove fail on undefined override
        terms = templar.template(terms, convert_bare=convert_bare, fail_on_undefined=fail_on_undefined)
    else:
        terms = templar.template(terms, fail_on_undefined=fail_on_undefined)

    if isinstance(terms, basestring) or not isinstance(terms, Iterable):
        terms = [ terms ]

    return terms
