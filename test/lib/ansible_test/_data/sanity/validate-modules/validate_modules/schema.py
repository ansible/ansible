# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Matt Martz <matt@sivel.net>
# Copyright: (c) 2015, Rackspace US, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import datetime
import re

from functools import partial

from voluptuous import ALLOW_EXTRA, PREVENT_EXTRA, All, Any, Invalid, Length, Required, Schema, Self, ValueInvalid
from ansible.module_utils.six import string_types
from ansible.module_utils.common.collections import is_iterable
from ansible.utils.version import SemanticVersion
from distutils.version import StrictVersion

from .utils import parse_isodate

list_string_types = list(string_types)
tuple_string_types = tuple(string_types)
any_string_types = Any(*string_types)

# Valid DOCUMENTATION.author lines
# Based on Ansibulbot's extract_github_id()
#   author: First Last (@name) [optional anything]
#     "Ansible Core Team" - Used by the Bot
#     "Michael DeHaan" - nop
#     "Name (!UNKNOWN)" - For the few untraceable authors
author_line = re.compile(r'^\w.*(\(@([\w-]+)\)|!UNKNOWN)(?![\w.])|^Ansible Core Team$|^Michael DeHaan$')


def _add_ansible_error_code(exception, error_code):
    setattr(exception, 'ansible_error_code', error_code)
    return exception


def semantic_version(v, error_code=None):
    if not isinstance(v, string_types):
        raise _add_ansible_error_code(Invalid('Semantic version must be a string'), error_code or 'collection-invalid-version')
    if not v:
        raise _add_ansible_error_code(
            Invalid('Empty string is not a valid semantic version'),
            error_code or 'collection-invalid-version')
    try:
        SemanticVersion(v)
    except ValueError as e:
        raise _add_ansible_error_code(Invalid(str(e)), error_code or 'collection-invalid-version')
    return v


def ansible_version(v, error_code=None):
    # Assumes argument is a string or float
    if 'historical' == v:
        return v
    try:
        StrictVersion(str(v))
    except ValueError as e:
        raise _add_ansible_error_code(Invalid(str(e)), error_code or 'ansible-invalid-version')
    return v


def isodate(v, error_code=None):
    try:
        parse_isodate(v)
    except ValueError as e:
        raise _add_ansible_error_code(Invalid(str(e)), error_code or 'ansible-invalid-date')
    return v


TAGGED_VERSION_RE = re.compile('^([^.]+.[^.]+):(.*)$')


def tagged_version(v, error_code=None):
    if not isinstance(v, string_types):
        # Should never happen to versions tagged by code
        raise _add_ansible_error_code(Invalid('Tagged version must be a string'), 'invalid-tagged-version')
    m = TAGGED_VERSION_RE.match(v)
    if not m:
        # Should never happen to versions tagged by code
        raise _add_ansible_error_code(Invalid('Tagged version does not match format'), 'invalid-tagged-version')
    collection = m.group(1)
    version = m.group(2)
    if collection != 'ansible.builtin':
        semantic_version(version, error_code=error_code)
    else:
        ansible_version(version, error_code=error_code)
    return v


def tagged_isodate(v, error_code=None):
    if not isinstance(v, string_types):
        # Should never happen to dates tagged by code
        raise _add_ansible_error_code(Invalid('Tagged date must be a string'), 'invalid-tagged-date')
    m = TAGGED_VERSION_RE.match(v)
    if not m:
        # Should never happen to dates tagged by code
        raise _add_ansible_error_code(Invalid('Tagged date does not match format'), 'invalid-tagged-date')
    isodate(m.group(2), error_code=error_code)
    return v


def version(for_collection=False, tagged='never', error_code=None):
    if tagged == 'always':
        return Any(partial(tagged_version, error_code=error_code))
    if for_collection:
        return Any(partial(semantic_version, error_code=error_code))
    return All(Any(float, *string_types), partial(ansible_version, error_code=error_code))


def date(tagged='never', error_code=None):
    if tagged == 'always':
        return Any(partial(tagged_isodate, error_code=error_code))
    return Any(isodate)


def is_callable(v):
    if not callable(v):
        raise ValueInvalid('not a valid value')
    return v


def sequence_of_sequences(min=None, max=None):
    return All(
        Any(
            None,
            [Any(list, tuple)],
            tuple([Any(list, tuple)]),
        ),
        Any(
            None,
            [Length(min=min, max=max)],
            tuple([Length(min=min, max=max)]),
        ),
    )


seealso_schema = Schema(
    [
        Any(
            {
                Required('module'): Any(*string_types),
                'description': Any(*string_types),
            },
            {
                Required('ref'): Any(*string_types),
                Required('description'): Any(*string_types),
            },
            {
                Required('name'): Any(*string_types),
                Required('link'): Any(*string_types),
                Required('description'): Any(*string_types),
            },
        ),
    ]
)


argument_spec_types = ['bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw',
                       'sid', 'str']


argument_spec_modifiers = {
    'mutually_exclusive': sequence_of_sequences(min=2),
    'required_together': sequence_of_sequences(min=2),
    'required_one_of': sequence_of_sequences(min=2),
    'required_if': sequence_of_sequences(min=3, max=4),
    'required_by': Schema({str: Any(list_string_types, tuple_string_types, *string_types)}),
}


def no_required_with_default(v):
    if v.get('default') and v.get('required'):
        raise Invalid('required=True cannot be supplied with a default')
    return v


def elements_with_list(v):
    if v.get('elements') and v.get('type') != 'list':
        raise Invalid('type must be list to use elements')
    return v


def options_with_apply_defaults(v):
    if v.get('apply_defaults') and not v.get('options'):
        raise Invalid('apply_defaults=True requires options to be set')
    return v


def argument_spec_schema(for_collection, dates_tagged=True):
    dates_tagged = 'always' if dates_tagged else 'never'
    any_string_types = Any(*string_types)
    schema = {
        any_string_types: {
            'type': Any(is_callable, *argument_spec_types),
            'elements': Any(*argument_spec_types),
            'default': object,
            'fallback': Any(
                (is_callable, list_string_types),
                [is_callable, list_string_types],
            ),
            'choices': Any([object], (object,)),
            'required': bool,
            'no_log': bool,
            'aliases': Any(list_string_types, tuple(list_string_types)),
            'apply_defaults': bool,
            'removed_in_version': version(for_collection, tagged='always'),
            'removed_at_date': date(tagged=dates_tagged),
            'options': Self,
            'deprecated_aliases': Any([Any(
                {
                    Required('name'): Any(*string_types),
                    Required('date'): date(tagged=dates_tagged),
                },
                {
                    Required('name'): Any(*string_types),
                    Required('version'): version(for_collection, tagged='always'),
                },
            )]),
        }
    }
    schema[any_string_types].update(argument_spec_modifiers)
    schemas = All(
        schema,
        Schema({any_string_types: no_required_with_default}),
        Schema({any_string_types: elements_with_list}),
        Schema({any_string_types: options_with_apply_defaults}),
    )
    return Schema(schemas)


def ansible_module_kwargs_schema(for_collection, dates_tagged=True):
    schema = {
        'argument_spec': argument_spec_schema(for_collection, dates_tagged=dates_tagged),
        'bypass_checks': bool,
        'no_log': bool,
        'check_invalid_arguments': Any(None, bool),
        'add_file_common_args': bool,
        'supports_check_mode': bool,
    }
    schema.update(argument_spec_modifiers)
    return Schema(schema)


json_value = Schema(Any(
    None,
    int,
    float,
    [Self],
    *(list({str_type: Self} for str_type in string_types) + list(string_types))
))


def list_dict_option_schema(for_collection):
    suboption_schema = Schema(
        {
            Required('description'): Any(list_string_types, *string_types),
            'required': bool,
            'choices': list,
            'aliases': Any(list_string_types),
            'version_added': version(for_collection, tagged='always', error_code='option-invalid-version-added'),
            'default': json_value,
            # Note: Types are strings, not literal bools, such as True or False
            'type': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
            # in case of type='list' elements define type of individual item in list
            'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
            # Recursive suboptions
            'suboptions': Any(None, *list({str_type: Self} for str_type in string_types)),
        },
        extra=PREVENT_EXTRA
    )

    # This generates list of dicts with keys from string_types and suboption_schema value
    # for example in Python 3: {str: suboption_schema}
    list_dict_suboption_schema = [{str_type: suboption_schema} for str_type in string_types]

    option_schema = Schema(
        {
            Required('description'): Any(list_string_types, *string_types),
            'required': bool,
            'choices': list,
            'aliases': Any(list_string_types),
            'version_added': version(for_collection, tagged='always', error_code='option-invalid-version-added'),
            'default': json_value,
            'suboptions': Any(None, *list_dict_suboption_schema),
            # Note: Types are strings, not literal bools, such as True or False
            'type': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
            # in case of type='list' elements define type of individual item in list
            'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
        },
        extra=PREVENT_EXTRA
    )

    # This generates list of dicts with keys from string_types and option_schema value
    # for example in Python 3: {str: option_schema}
    return [{str_type: option_schema} for str_type in string_types]


def return_contains(v):
    schema = Schema(
        {
            Required('contains'): Any(dict, list, *string_types)
        },
        extra=ALLOW_EXTRA
    )
    if v.get('type') == 'complex':
        return schema(v)
    return v


def return_schema(for_collection):
    return_contains_schema = Any(
        All(
            Schema(
                {
                    Required('description'): Any(list_string_types, *string_types),
                    'returned': Any(*string_types),  # only returned on top level
                    Required('type'): Any('bool', 'complex', 'dict', 'float', 'int', 'list', 'str'),
                    'version_added': version(for_collection, error_code='return-invalid-version-added'),
                    'sample': json_value,
                    'example': json_value,
                    'contains': Any(None, *list({str_type: Self} for str_type in string_types)),
                    # in case of type='list' elements define type of individual item in list
                    'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
                }
            ),
            Schema(return_contains)
        ),
        Schema(type(None)),
    )

    # This generates list of dicts with keys from string_types and return_contains_schema value
    # for example in Python 3: {str: return_contains_schema}
    list_dict_return_contains_schema = [{str_type: return_contains_schema} for str_type in string_types]

    return Any(
        All(
            Schema(
                {
                    any_string_types: {
                        Required('description'): Any(list_string_types, *string_types),
                        Required('returned'): Any(*string_types),
                        Required('type'): Any('bool', 'complex', 'dict', 'float', 'int', 'list', 'str'),
                        'version_added': version(for_collection, error_code='return-invalid-version-added'),
                        'sample': json_value,
                        'example': json_value,
                        'contains': Any(None, *list_dict_return_contains_schema),
                        # in case of type='list' elements define type of individual item in list
                        'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
                    }
                }
            ),
            Schema({any_string_types: return_contains})
        ),
        Schema(type(None)),
    )


def deprecation_schema(for_collection):
    main_fields = {
        Required('why'): Any(*string_types),
        Required('alternative'): Any(*string_types),
        'removed': Any(True),
    }

    date_schema = {
        Required('removed_at_date'): date(tagged='always'),
    }
    date_schema.update(main_fields)

    if for_collection:
        version_schema = {
            Required('removed_in'): version(for_collection, tagged='always'),
        }
    else:
        version_schema = {
            # Only list branches that are deprecated or may have docs stubs in
            # Deprecation cycle changed at 2.4 (though not retroactively)
            # 2.3 -> removed_in: "2.5" + n for docs stub
            # 2.4 -> removed_in: "2.8" + n for docs stub
            Required('removed_in'): Any(
                "ansible.builtin:2.2", "ansible.builtin:2.3", "ansible.builtin:2.4", "ansible.builtin:2.5",
                "ansible.builtin:2.6", "ansible.builtin:2.8", "ansible.builtin:2.9", "ansible.builtin:2.10",
                "ansible.builtin:2.11", "ansible.builtin:2.12", "ansible.builtin:2.13", "ansible.builtin:2.14"),
        }
    version_schema.update(main_fields)

    return Any(
        Schema(version_schema, extra=PREVENT_EXTRA),
        Schema(date_schema, extra=PREVENT_EXTRA),
    )


def author(value):

    if not is_iterable(value):
        value = [value]

    for line in value:
        m = author_line.search(line)
        if not m:
            raise Invalid("Invalid author")


def doc_schema(module_name, for_collection=False, deprecated_module=False):

    if module_name.startswith('_'):
        module_name = module_name[1:]
        deprecated_module = True
    doc_schema_dict = {
        Required('module'): module_name,
        Required('short_description'): Any(*string_types),
        Required('description'): Any(list_string_types, *string_types),
        Required('author'): All(Any(None, list_string_types, *string_types), author),
        'notes': Any(None, list_string_types),
        'seealso': Any(None, seealso_schema),
        'requirements': list_string_types,
        'todo': Any(None, list_string_types, *string_types),
        'options': Any(None, *list_dict_option_schema(for_collection)),
        'extends_documentation_fragment': Any(list_string_types, *string_types)
    }

    if for_collection:
        # Optional
        doc_schema_dict['version_added'] = version(
            for_collection=True, tagged='always', error_code='module-invalid-version-added')
    else:
        doc_schema_dict[Required('version_added')] = version(
            for_collection=False, tagged='always', error_code='module-invalid-version-added')

    if deprecated_module:
        deprecation_required_scheme = {
            Required('deprecated'): Any(deprecation_schema(for_collection=for_collection)),
        }

        doc_schema_dict.update(deprecation_required_scheme)
    return Schema(
        doc_schema_dict,
        extra=PREVENT_EXTRA
    )


# Things to add soon
####################
# 1) Recursively validate `type: complex` fields
#    This will improve documentation, though require fair amount of module tidyup

# Possible Future Enhancements
##############################

# 1) Don't allow empty options for choices, aliases, etc
# 2) If type: bool ensure choices isn't set - perhaps use Exclusive
# 3) both version_added should be quoted floats

#  Tool that takes JSON and generates RETURN skeleton (needs to support complex structures)
