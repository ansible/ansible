# coding: utf-8
# Copyright: (c) 2022, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from collections.abc import Iterable

from ansible.module_utils.six import string_types
from ansible.utils.display import Display


display = Display()


def validate_variable_names(names, where=None, obj=None):
    """Check that given variable names are valid otherwise raise an error."""
    # avoid circular imports
    from ansible.utils.vars import isidentifier
    from ansible.vars.reserved import is_reserved_name

    var_names = names
    if not isinstance(var_names, Iterable) or isinstance(var_names, string_types):
        var_names = [var_names]

    invalid_names = ', '.join(
        f'\'{vn}\'' for vn in filter(
            lambda x: not isidentifier(x) or is_reserved_name(x),
            var_names
        )
    )

    if not invalid_names:
        return

    where_msg = '' if where is None else f'in {where} '
    msg = (
        f'Invalid variable names {where_msg}specified: {invalid_names}. '
        'Variables must start with a letter or underscore character, '
        'and contain only letters, numbers and underscores. '
        'Variable names also must not conflict with Python, Jinja and '
        'Ansible keywords. This will be an error in 2.16.'
    )

    # FIXME raise an error in 2.16
    display.deprecated(msg, version=2.16)
