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
from ansible.utils.display import Display

display = Display()

_INTERNAL_HARDCODED = ('local_action', 'lookup', 'query', 'q')
_RESERVE_EXCEPTIONS = frozenset(('environment', 'gather_subset', 'vars'))


def get_reserved_names(include_private=True):
    ''' this function returns the list of reserved names associated with play objects and internal template functions'''
    # FIXME: deal with Jinja tests and filters and with_<lookups>

    result = set(_INTERNAL_HARDCODED)

    # FIXME: find a way to 'not hardcode', possibly need role deps/includes
    class_list = [Play, Role, Block, Task]

    for aclass in class_list:
        aobj = aclass()

        # build ordered list to loop over and dict with attributes
        for attribute in aobj.__dict__['_attributes']:
            if not getattr(attribute, 'private', False):
                result.add(attribute)
            elif include_private:
                result.add(attribute)

    return result


def handle_reserved_vars(myvars):
    ''' this function warns if any variable passed conflicts with internally reserved names '''

    if C.RESERVED_VAR_NAMES != 'ignore':
        varnames = set(myvars)
        for varname in varnames.intersection(_RESERVED_NAMES):
            if varname in _RESERVE_EXCEPTIONS:
                # FIXME: remove these exceptions if we can
                continue
            msg = 'Found variable using reserved name: %s' % to_text(varname)
            if C.RESERVED_VAR_NAMES == 'warn':
                display.warning(msg)
            elif C.RESERVED_VAR_NAMES == 'error':
                raise AnsibleError(msg)


def is_reserved_name(name):
    return name in _RESERVED_NAMES


_RESERVED_NAMES = frozenset(get_reserved_names())
