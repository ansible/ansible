# coding: utf-8
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


from collections.abc import Iterable

from ansible.errors import AnsibleAssertionError


def validate_variable_names(names):
    """
    This checks that all variable names are valid or raises an error.

    :arg data: iterable of names
    :raises TypeError: if one of the variable names is not valid
    :raises AnsibleError: if one of the variable names is a reserved name and ANSIBLE_RESERVED_VAR_NAMES=error
    """

    # avoid circular imports
    from ansible.utils.vars import isidentifier
    from ansible.vars.reserved import handle_reserved_vars

    if not isinstance(names, Iterable):
        raise AnsibleAssertionError("'names' must be of type <Iterable>, was: %s" % type(names))

    for name in names:
        if not isidentifier(name):
            raise TypeError(
                "The variable name '%s' is not valid. Variables must start with a letter or underscore "
                "character, and contain only letters, numbers and underscores." % name
            )

    handle_reserved_vars(names)
