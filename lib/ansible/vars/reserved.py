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

_INTERNAL_HARDCODED = frozenset(('local_action',))
_e = Templar(None).environment
_JINJA_RESERVED = frozenset(set(_e.globals).union(_e.filters, _e.tests))
# FIXME: remove these exceptions if we can
_RESERVE_EXCEPTIONS = frozenset(('environment', 'gather_subset', 'vars'))
_WITH_LOOKUPS = frozenset('with_%s' % l.__module__.rsplit('.', 1)[-1] for l in lookup_loader.all())


def get_reserved_names(include_private=True):
    """Return the list of reserved names associated with play objects and internal template functions"""
    result = set(_INTERNAL_HARDCODED).union(_JINJA_RESERVED, _WITH_LOOKUPS)

    # FIXME: find a way to 'not hardcode', possibly need role deps/includes
    class_list = (Play, Role, Block, Task, Handler)

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


def handle_reserved_vars(myvars):
    """Warn if any variable passed conflicts with internally reserved names"""
    if C.RESERVED_VAR_NAMES != 'ignore':
        varnames = set(myvars)
        reserved_varnames_used = varnames.intersection(_RESERVED_NAMES).difference(_RESERVE_EXCEPTIONS)
        for varname in reserved_varnames_used:
            msg = 'Found variable using reserved name: %s' % to_text(varname)
            if C.RESERVED_VAR_NAMES == 'warn':
                display.warning(msg)
            elif C.RESERVED_VAR_NAMES == 'error':
                raise AnsibleError(msg)


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
    display.deprecated(
        'ansible.vars.reserved.is_reserved_name function is deprecated. '
        'Use functions from ansible.vars.reserved to replace its functionality.',
        version='2.16'
    )
    return name in _RESERVED_NAMES


_RESERVED_NAMES = frozenset(get_reserved_names())
