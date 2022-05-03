# coding: utf-8
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible import constants as C
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_text
from ansible.playbook import Play
from ansible.playbook.block import Block
from ansible.playbook.handler import Handler
from ansible.playbook.role import Role
from ansible.playbook.task import Task
from ansible.plugins.loader import lookup_loader
from ansible.template import Templar
from ansible.utils.display import Display

display = Display()

_INTERNAL_HARDCODED = frozenset(('local_action', 'ansible'))
_LOOKUPS = frozenset(l.__module__.rsplit('.', 1)[-1] for l in lookup_loader.all())
_WITH_LOOKUPS = frozenset('with_%s' % l for l in _LOOKUPS)

_e = Templar(None).environment
_e.filters._load_ansible_plugins()
_e.tests._load_ansible_plugins()

_ANSIBLE_JINJA_RESERVED = frozenset(set(_e.globals).union(_e.filters, _e.tests, _LOOKUPS, _WITH_LOOKUPS))

# FIXME: remove these exceptions if we can
_RESERVE_EXCEPTIONS = frozenset(('environment', 'gather_subset', 'vars'))


def get_reserved_names(include_private=True):
    """Return the list of reserved names associated with play objects and internal template functions"""
    result = set(_INTERNAL_HARDCODED).union(_ANSIBLE_JINJA_RESERVED)

    # FIXME: find a way to 'not hardcode', possibly need role deps/includes
    for aclass in (Play, Role, Block, Task, Handler):
        for name, attr in aclass.fattributes.items():
            if attr.private or include_private:
                result.add(name)

    return result


def warn_if_reserved(myvars, additional=None):
    ''' this function warns if any variable passed conflicts with internally reserved names '''
    display.deprecated(
        'ansible.vars.reserved.warn_if_reserved function is deprecated. '
        'Use functions from ansible.vars.reserved to replace its functionality.',
        version='2.16'
    )
    if additional is None:
        reserved = _RESERVED_NAMES
    else:
        reserved = _RESERVED_NAMES.union(additional)

    varnames = set(myvars)
    varnames.discard('vars')  # we add this one internally, so safe to ignore
    for varname in varnames.intersection(reserved):
        display.warning('Found variable using reserved name: %s' % varname)


def is_reserved_name(name):
    return name in _RESERVED_NAMES


_RESERVED_NAMES = frozenset(set(get_reserved_names()).difference(_RESERVE_EXCEPTIONS))
