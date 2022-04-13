# (c) 2017 Ansible By Red Hat
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

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()

_INTERNAL_HARDCODED =  tuple(Templar(None).environment.globals.keys()) + ('local_action',)

# FIXME: remove these exceptions if we can
_RESERVE_EXCEPTIONS = frozenset(('environment', 'gather_subset', 'vars'))


def get_reserved_names(include_private=True):
    ''' this function returns the list of reserved names associated with play objects and internal template functions '''
    # FIXME: deal with Jinja tests and filters and with_<lookups>

    result = set(_INTERNAL_HARDCODED)

    # FIXME: find a way to 'not hardcode', possibly need role deps/includes
    class_list = [Play, Role, Block, Task]

    for aclass in class_list:
        # build ordered list to loop over and dict with attributes
        for name, attr in aclass.fattributes.items():
            if attr.private:
                private.add(name)
            else:
                public.add(name)

    # local_action is implicit with action
    if 'action' in public:
        public.add('local_action')

    # loop implies with_
    # FIXME: remove after with_ is not only deprecated but removed
    if 'loop' in private or 'loop' in public:
        public.add('with_')

    if include_private:
        result = public.union(private)
    else:
        result = public

    return result


def warn_if_reserved(myvars, additional=None):
    ''' this function warns if any variable passed conflicts with internally reserved names '''

    if additional is None:
        reserved = _RESERVED_NAMES
    else:
        reserved = _RESERVED_NAMES.union(additional)

    varnames = set(myvars)
    varnames.discard('vars')  # we add this one internally, so safe to ignore
    for varname in varnames.intersection(reserved):
        display.warning('Found variable using reserved name: %s' % varname)


def handle_reserved_vars(myvars):
    ''' this function warns if any variable passed conflicts with internally reserved names '''

    if C.RESERVED_VAR_NAMES != 'ignore':
        varnames = set(myvars)
        reserved_varnames_used = varnames.intersection(_RESERVED_NAMES).difference(_RESERVE_EXCEPTIONS)
        for varname in reserved_varnames_used:
            msg = 'Found variable using reserved name: %s' % to_text(varname)
            if C.RESERVED_VAR_NAMES == 'warn':
                display.warning(msg)
            elif C.RESERVED_VAR_NAMES == 'error':
                raise AnsibleError(msg)


def is_reserved_name(name):
    return name in _RESERVED_NAMES


_RESERVED_NAMES = frozenset(get_reserved_names())
