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

from __future__ import annotations

from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()


def get_reserved_names(include_private: bool = True) -> set[str]:
    """ this function returns the list of reserved names associated with play objects"""

    templar = Templar(loader=None)
    public = set(templar.environment.globals.keys())
    private = set()
    result = set()

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

    # due to Collectors always adding, need to ignore this
    # eventually should remove after we deprecate it in setup.py
    result.remove('gather_subset')

    return result


def warn_if_reserved(myvars: list[str], additional: list[str] | None = None) -> None:
    """ this function warns if any variable passed conflicts with internally reserved names """

    if additional is None:
        reserved = _RESERVED_NAMES
    else:
        reserved = _RESERVED_NAMES.union(additional)

    varnames = set(myvars)
    varnames.discard('vars')  # we add this one internally, so safe to ignore
    for varname in varnames.intersection(reserved):
        display.warning('Found variable using reserved name: %s' % varname)


def is_reserved_name(name: str) -> bool:
    return name in _RESERVED_NAMES


_RESERVED_NAMES = frozenset(get_reserved_names())
