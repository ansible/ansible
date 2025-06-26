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

from __future__ import annotations

import keyword
import secrets
import uuid
import typing as t

from collections.abc import MutableMapping, MutableSequence
from json import dumps

from ansible import constants as C
from ansible import context
from ansible._internal import _json
from ansible._internal._templating import _jinja_bits
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.module_utils.datatag import native_type_name
from ansible.module_utils.common.text.converters import to_native, to_text
from ansible.parsing.splitter import parse_kv
from ansible.parsing.dataloader import DataLoader

_MAXSIZE = 2 ** 32
cur_id = 0
node_mac = ("%012x" % uuid.getnode())[:12]
random_int = ("%08x" % secrets.randbelow(_MAXSIZE))[:8]


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
            except Exception:
                myvars.append(to_native(x))
        raise AnsibleError("failed to combine variables, expected dicts but got a '{0}' and a '{1}': \n{2}\n{3}".format(
            a.__class__.__name__, b.__class__.__name__, myvars[0], myvars[1])
        )


def combine_vars(a, b, merge=None):
    """
    Return a copy of dictionaries of variables based on configured hash behavior
    """

    if merge or merge is None and C.DEFAULT_HASH_BEHAVIOUR == "merge":
        return merge_hash(a, b)

    # HASH_BEHAVIOUR == 'replace'
    _validate_mutable_mappings(a, b)
    result = a | b
    return result


def merge_hash(x, y, recursive=True, list_merge='replace'):
    """
    Return a new dictionary result of the merges of y into x,
    so that keys from y take precedence over keys from x.
    (x and y aren't modified)
    """
    if list_merge not in ('replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp'):
        raise AnsibleError("merge_hash: 'list_merge' argument can only be equal to 'replace', 'keep', 'append', 'prepend', 'append_rp' or 'prepend_rp'")

    # verify x & y are dicts
    _validate_mutable_mappings(x, y)

    # to speed things up: if x is empty or equal to y, return y
    # (this `if` can be remove without impact on the function
    #  except performance)
    if x == {} or x == y:
        return y.copy()
    if y == {}:
        return x

    # in the following we will copy elements from y to x, but
    # we don't want to modify x, so we create a copy of it
    x = x.copy()

    # to speed things up: use dict.update if possible
    # (this `if` can be remove without impact on the function
    #  except performance)
    if not recursive and list_merge == 'replace':
        x.update(y)
        return x

    # insert each element of y in x, overriding the one in x
    # (as y has higher priority)
    # we copy elements from y to x instead of x to y because
    # there is a high probability x will be the "default" dict the user
    # want to "patch" with y
    # therefore x will have much more elements than y
    for key, y_value in y.items():
        # if `key` isn't in x
        # update x and move on to the next element of y
        if key not in x:
            x[key] = y_value
            continue
        # from this point we know `key` is in x

        x_value = x[key]

        # if both x's element and y's element are dicts
        # recursively "combine" them or override x's with y's element
        # depending on the `recursive` argument
        # and move on to the next element of y
        if isinstance(x_value, MutableMapping) and isinstance(y_value, MutableMapping):
            if recursive:
                x[key] = merge_hash(x_value, y_value, recursive, list_merge)
            else:
                x[key] = y_value
            continue

        # if both x's element and y's element are lists
        # "merge" them depending on the `list_merge` argument
        # and move on to the next element of y
        if isinstance(x_value, MutableSequence) and isinstance(y_value, MutableSequence):
            if list_merge == 'replace':
                # replace x value by y's one as it has higher priority
                x[key] = y_value
            elif list_merge == 'append':
                x[key] = x_value + y_value
            elif list_merge == 'prepend':
                x[key] = y_value + x_value
            elif list_merge == 'append_rp':
                # append all elements from y_value (high prio) to x_value (low prio)
                # and remove x_value elements that are also in y_value
                # we don't remove elements from x_value nor y_value that were already in double
                # (we assume that there is a reason if there where such double elements)
                # _rp stands for "remove present"
                x[key] = [z for z in x_value if z not in y_value] + y_value
            elif list_merge == 'prepend_rp':
                # same as 'append_rp' but y_value elements are prepend
                x[key] = y_value + [z for z in x_value if z not in y_value]
            # else 'keep'
            #   keep x value even if y it's of higher priority
            #   it's done by not changing x[key]
            continue

        # else just override x's element with y's one
        x[key] = y_value

    return x


def load_extra_vars(loader: DataLoader) -> dict[str, t.Any]:

    if not getattr(load_extra_vars, 'extra_vars', None):
        extra_vars: dict[str, t.Any] = {}
        for extra_vars_opt in context.CLIARGS.get('extra_vars', tuple()):
            extra_vars_opt = to_text(extra_vars_opt, errors='surrogate_or_strict')
            if extra_vars_opt is None or not extra_vars_opt:
                continue

            if extra_vars_opt.startswith(u"@"):
                # Argument is a YAML file (JSON is a subset of YAML)
                data = loader.load_from_file(extra_vars_opt[1:], trusted_as_template=True)
            elif extra_vars_opt[0] in [u'/', u'.']:
                raise AnsibleOptionsError("Please prepend extra_vars filename '%s' with '@'" % extra_vars_opt)
            elif extra_vars_opt[0] in [u'[', u'{']:
                # Arguments as YAML
                data = loader.load(extra_vars_opt)
            else:
                # Arguments as Key-value
                data = parse_kv(extra_vars_opt)

            if isinstance(data, MutableMapping):
                extra_vars = combine_vars(extra_vars, data)
            else:
                raise AnsibleOptionsError("Invalid extra vars data supplied. '%s' could not be made into a dictionary" % extra_vars_opt)

        load_extra_vars.extra_vars = extra_vars

    return load_extra_vars.extra_vars


def load_options_vars(version):

    if not getattr(load_options_vars, 'options_vars', None):
        if version is None:
            version = 'Unknown'
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
            opt = context.CLIARGS.get(attr)
            if opt is not None:
                options_vars['ansible_%s' % alias] = opt

        setattr(load_options_vars, 'options_vars', options_vars)

    return load_options_vars.options_vars


def isidentifier(ident):
    """Determine if string is valid identifier.

    The purpose of this function is to be used to validate any variables created in
    a play to be valid Python identifiers and to not conflict with Python keywords
    to prevent unexpected behavior. Since Python 2 and Python 3 differ in what
    a valid identifier is, this function unifies the validation so playbooks are
    portable between the two. The following changes were made:

        * disallow non-ascii characters (Python 3 allows for them as opposed to Python 2)

    :arg ident: A text string of identifier to check. Note: It is callers
        responsibility to convert ident to text if it is not already.

    Originally posted at https://stackoverflow.com/a/29586366
    """
    # deprecated: description='Use validate_variable_name instead.' core_version='2.23'

    if not isinstance(ident, str):
        return False

    if not ident.isascii():
        return False

    if not ident.isidentifier():
        return False

    if keyword.iskeyword(ident):
        return False

    return True


def validate_variable_name(name: object) -> None:
    """Validate the given variable name is valid, raising an AnsibleError if it is not."""
    if isinstance(name, str) and name.isidentifier() and name.isascii() and name not in _jinja_bits.JINJA_KEYWORDS:
        return

    if isinstance(name, (str, int, float, bool, type(None))):
        key_description = f'name {str(name)!r}'  # show common scalar key names as strings
    else:
        key_description = 'name'

    if not isinstance(name, str):
        key_description += f' of type {native_type_name(name)!r}'  # show the type name of all non-string keys

    raise AnsibleError(
        message=f'Invalid variable {key_description}.',
        help_text='Variable names must be strings starting with a letter or underscore character, and contain only letters, numbers and underscores.',
        obj=name,
    )


def transform_to_native_types(
    value: object,
    redact: bool = True,
) -> t.Any:
    """
    Recursively transform the given value to Python native types.
    Potentially sensitive values such as individually vaulted variables will be redacted unless ``redact=False`` is passed.
    Which values are considered potentially sensitive may change in future releases.
    Types which cannot be converted to Python native types will result in an error.
    """
    avv = _json.AnsibleVariableVisitor(
        convert_mapping_to_dict=True,
        convert_sequence_to_list=True,
        convert_custom_scalars=True,
        convert_to_native_values=True,
        apply_transforms=True,
        visit_keys=True,  # ensure that keys are also converted
        encrypted_string_behavior=_json.EncryptedStringBehavior.REDACT if redact else _json.EncryptedStringBehavior.DECRYPT,
    )

    return avv.visit(value)
