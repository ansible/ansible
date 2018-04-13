# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import ast
import random
import uuid

from collections import MutableMapping
from json import dumps


from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_native, to_text
from ansible.parsing.splitter import parse_kv


_MAXSIZE = 2 ** 32
cur_id = 0
node_mac = ("%012x" % uuid.getnode())[:12]
random_int = ("%08x" % random.randint(0, _MAXSIZE))[:8]


def get_unique_id():
    global cur_id
    cur_id += 1
    return "-".join([
        node_mac[0:8],
        node_mac[8:12],
        random_int[0:4],
        random_int[4:8],
        ("%012x" % cur_id)[:12],
    ])


def _validate_mutable_mappings(a, b):
    """
    Internal convenience function to ensure arguments are MutableMappings

    This checks that all arguments are MutableMappings or raises an error

    :raises AnsibleError: if one of the arguments is not a MutableMapping
    """

    # If this becomes generally needed, change the signature to operate on
    # a variable number of arguments instead.

    if not (isinstance(a, MutableMapping) and isinstance(b, MutableMapping)):
        myvars = []
        for x in [a, b]:
            try:
                myvars.append(dumps(x))
            except:
                myvars.append(to_native(x))
        raise AnsibleError("failed to combine variables, expected dicts but got a '{0}' and a '{1}': \n{2}\n{3}".format(
            a.__class__.__name__, b.__class__.__name__, myvars[0], myvars[1])
        )


def combine_vars(a, b):
    """
    Return a copy of dictionaries of variables based on configured hash behavior
    """

    if C.DEFAULT_HASH_BEHAVIOUR == "merge":
        return merge_hash(a, b)
    else:
        # HASH_BEHAVIOUR == 'replace'
        _validate_mutable_mappings(a, b)
        result = a.copy()
        result.update(b)
        return result


def merge_hash(a, b):
    """
    Recursively merges hash b into a so that keys from b take precedence over keys from a
    """

    _validate_mutable_mappings(a, b)

    # if a is empty or equal to b, return b
    if a == {} or a == b:
        return b.copy()

    # if b is empty the below unfolds quickly
    result = a.copy()

    # next, iterate over b keys and values
    for k, v in iteritems(b):
        # if there's already such key in a
        # and that key contains a MutableMapping
        if k in result and isinstance(result[k], MutableMapping) and isinstance(v, MutableMapping):
            # merge those dicts recursively
            result[k] = merge_hash(result[k], v)
        else:
            # otherwise, just copy the value from b to a
            result[k] = v

    return result


def load_extra_vars(loader, options):
    extra_vars = {}
    if hasattr(options, 'extra_vars'):
        for extra_vars_opt in options.extra_vars:
            data = None
            extra_vars_opt = to_text(extra_vars_opt, errors='surrogate_or_strict')
            if extra_vars_opt.startswith(u"@"):
                # Argument is a YAML file (JSON is a subset of YAML)
                data = loader.load_from_file(extra_vars_opt[1:])
            elif extra_vars_opt and extra_vars_opt[0] in u'[{':
                # Arguments as YAML
                data = loader.load(extra_vars_opt)
            else:
                # Arguments as Key-value
                data = parse_kv(extra_vars_opt)

            if isinstance(data, MutableMapping):
                extra_vars = combine_vars(extra_vars, data)
            else:
                raise AnsibleOptionsError("Invalid extra vars data supplied. '%s' could not be made into a dictionary" % extra_vars_opt)

    return extra_vars


def load_options_vars(options, version):

    options_vars = {'ansible_version': version}
    attrs = {'check': 'check_mode',
             'diff': 'diff_mode',
             'forks': 'forks',
             'inventory': 'inventory_sources',
             'skip_tags': 'skip_tags',
             'subset': 'limit',
             'tags': 'run_tags',
             'verbosity': 'verbosity'}

    for attr, alias in attrs.items():
        opt = getattr(options, attr, None)
        if opt is not None:
            options_vars['ansible_%s' % alias] = opt

    return options_vars


def isidentifier(ident):
    """
    Determines, if string is valid Python identifier using the ast module.
    Originally posted at: http://stackoverflow.com/a/29586366
    """

    if not isinstance(ident, string_types):
        return False

    try:
        root = ast.parse(ident)
    except SyntaxError:
        return False

    if not isinstance(root, ast.Module):
        return False

    if len(root.body) != 1:
        return False

    if not isinstance(root.body[0], ast.Expr):
        return False

    if not isinstance(root.body[0].value, ast.Name):
        return False

    if root.body[0].value.id != ident:
        return False

    return True
