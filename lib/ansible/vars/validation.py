# coding: utf-8
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import itertools

from collections.abc import Iterable

from ansible.errors import AnsibleInvalidVarNameError
from ansible.module_utils.six import string_types


def validate_variable_names(names, where=None, obj=None):
    """Check that given variable names are valid otherwise raise an error."""
    # avoid circular imports
    from ansible.utils.vars import isidentifier
    from ansible.vars.reserved import handle_reserved_vars

    var_names = names
    if not isinstance(var_names, Iterable) or isinstance(var_names, string_types):
        var_names = [var_names]

    where_msg = '' if where is None else f'in \'{where}\' '
    for name in itertools.filterfalse(isidentifier, var_names):
        raise AnsibleInvalidVarNameError(
            f'Invalid variable name {where_msg}specified: "{name}". '
            'Variables must start with a letter or underscore character, '
            'and contain only letters, numbers and underscores.',
            obj=obj,
        )

    handle_reserved_vars(var_names)
