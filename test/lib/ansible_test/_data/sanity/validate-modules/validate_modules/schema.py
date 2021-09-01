# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Matt Martz <matt@sivel.net>
# Copyright: (c) 2015, Rackspace US, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re

from distutils.version import StrictVersion
from functools import partial

from voluptuous import ALLOW_EXTRA, PREVENT_EXTRA, All, Any, Invalid, Length, Required, Schema, Self, ValueInvalid
from ansible.module_utils.six import string_types
from ansible.module_utils.common.collections import is_iterable
from ansible.utils.version import SemanticVersion

from .utils import parse_isodate

list_string_types = list(string_types)
tuple_string_types = tuple(string_types)
any_string_types = Any(*string_types)

# Valid DOCUMENTATION.author lines
# Based on Ansibulbot's extract_github_id()
#   author: First Last (@name) [optional anything]
#     "Ansible Core Team" - Used by the Bot
#     "Michael DeHaan" - nop
#     "OpenStack Ansible SIG" - OpenStack does not use GitHub
#     "Name (!UNKNOWN)" - For the few untraceable authors
author_line = re.compile(r'^\w.*(\(@([\w-]+)\)|!UNKNOWN)(?![\w.])|^Ansible Core Team$|^Michael DeHaan$|^OpenStack Ansible SIG$')


def _add_ansible_error_code(exception, error_code):
    setattr(exception, 'ansible_error_code', error_code)
    return exception


def isodate(v, error_code=None):
    try:
        parse_isodate(v, allow_date=True)
    except ValueError as e:
        raise _add_ansible_error_code(Invalid(str(e)), error_code or 'ansible-invalid-date')
    return v


COLLECTION_NAME_RE = re.compile('^([^.]+.[^.]+)$')


def collection_name(v, error_code=None):
    if not isinstance(v, string_types):
        raise _add_ansible_error_code(
            Invalid('Collection name must be a string'), error_code or 'collection-invalid-name')
    m = COLLECTION_NAME_RE.match(v)
    if not m:
        raise _add_ansible_error_code(
            Invalid('Collection name must be of format `<namespace>.<name>`'), error_code or 'collection-invalid-name')
    return v


def version(for_collection=False):
    if for_collection:
        # We do not accept floats for versions in collections
        return Any(*string_types)
    return Any(float, *string_types)


def date(error_code=None):
    return Any(isodate, error_code=error_code)


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


def option_deprecation(v):
    if v.get('removed_in_version') or v.get('removed_at_date'):
        if v.get('removed_in_version') and v.get('removed_at_date'):
            raise _add_ansible_error_code(
                Invalid('Only one of removed_in_version and removed_at_date must be specified'),
                error_code='deprecation-either-date-or-version')
        if not v.get('removed_from_collection'):
            raise _add_ansible_error_code(
                Invalid('If removed_in_version or removed_at_date is specified, '
                        'removed_from_collection must be specified as well'),
                error_code='deprecation-collection-missing')
        return
    if v.get('removed_from_collection'):
        raise Invalid('removed_from_collection cannot be specified without either '
                      'removed_in_version or removed_at_date')


def argument_spec_schema(for_collection):
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
            'removed_in_version': version(for_collection),
            'removed_at_date': date(),
            'removed_from_collection': collection_name,
            'options': Self,
            'deprecated_aliases': Any([Any(
                {
                    Required('name'): Any(*string_types),
                    Required('date'): date(),
                    Required('collection_name'): collection_name,
                },
                {
                    Required('name'): Any(*string_types),
                    Required('version'): version(for_collection),
                    Required('collection_name'): collection_name,
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
        Schema({any_string_types: option_deprecation}),
    )
    return Schema(schemas)


def ansible_module_kwargs_schema(for_collection):
    schema = {
        'argument_spec': argument_spec_schema(for_collection),
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


def version_added(v, error_code='version-added-invalid', accept_historical=False):
    if 'version_added' in v:
        version_added = v.get('version_added')
        if isinstance(version_added, string_types):
            # If it is not a string, schema validation will have already complained
            # - or we have a float and we are in ansible/ansible, in which case we're
            # also happy.
            if v.get('version_added_collection') == 'ansible.builtin':
                if version_added == 'historical' and accept_historical:
                    return v
                try:
                    version = StrictVersion()
                    version.parse(version_added)
                except ValueError as exc:
                    raise _add_ansible_error_code(
                        Invalid('version_added (%r) is not a valid ansible-base version: '
                                '%s' % (version_added, exc)),
                        error_code=error_code)
            else:
                try:
                    version = SemanticVersion()
                    version.parse(version_added)
                except ValueError as exc:
                    raise _add_ansible_error_code(
                        Invalid('version_added (%r) is not a valid collection version '
                                '(see specification at https://semver.org/): '
                                '%s' % (version_added, exc)),
                        error_code=error_code)
    elif 'version_added_collection' in v:
        # Must have been manual intervention, since version_added_collection is only
        # added automatically when version_added is present
        raise Invalid('version_added_collection cannot be specified without version_added')
    return v


def list_dict_option_schema(for_collection):
    suboption_schema = Schema(
        {
            Required('description'): Any(list_string_types, *string_types),
            'required': bool,
            'choices': list,
            'aliases': Any(list_string_types),
            'version_added': version(for_collection),
            'version_added_collection': collection_name,
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
            'version_added': version(for_collection),
            'version_added_collection': collection_name,
            'default': json_value,
            'suboptions': Any(None, *list_dict_suboption_schema),
            # Note: Types are strings, not literal bools, such as True or False
            'type': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
            # in case of type='list' elements define type of individual item in list
            'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
        },
        extra=PREVENT_EXTRA
    )

    option_version_added = Schema(
        All({
            'suboptions': Any(None, *[{str_type: Self} for str_type in string_types]),
        }, partial(version_added, error_code='option-invalid-version-added')),
        extra=ALLOW_EXTRA
    )

    # This generates list of dicts with keys from string_types and option_schema value
    # for example in Python 3: {str: option_schema}
    return [{str_type: All(option_schema, option_version_added)} for str_type in string_types]


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
                    'version_added': version(for_collection),
                    'version_added_collection': collection_name,
                    'sample': json_value,
                    'example': json_value,
                    'contains': Any(None, *list({str_type: Self} for str_type in string_types)),
                    # in case of type='list' elements define type of individual item in list
                    'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
                }
            ),
            Schema(return_contains),
            Schema(partial(version_added, error_code='option-invalid-version-added')),
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
                        'version_added': version(for_collection),
                        'version_added_collection': collection_name,
                        'sample': json_value,
                        'example': json_value,
                        'contains': Any(None, *list_dict_return_contains_schema),
                        # in case of type='list' elements define type of individual item in list
                        'elements': Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str'),
                    }
                }
            ),
            Schema({any_string_types: return_contains}),
            Schema({any_string_types: partial(version_added, error_code='option-invalid-version-added')}),
        ),
        Schema(type(None)),
    )


def deprecation_schema(for_collection):
    main_fields = {
        Required('why'): Any(*string_types),
        Required('alternative'): Any(*string_types),
        Required('removed_from_collection'): collection_name,
        'removed': Any(True),
    }

    date_schema = {
        Required('removed_at_date'): date(),
    }
    date_schema.update(main_fields)

    if for_collection:
        version_schema = {
            Required('removed_in'): version(for_collection),
        }
    else:
        version_schema = {
            # Only list branches that are deprecated or may have docs stubs in
            # Deprecation cycle changed at 2.4 (though not retroactively)
            # 2.3 -> removed_in: "2.5" + n for docs stub
            # 2.4 -> removed_in: "2.8" + n for docs stub
            Required('removed_in'): Any(
                "2.2", "2.3", "2.4", "2.5", "2.6", "2.8", "2.9", "2.10", "2.11", "2.12", "2.13", "2.14"),
        }
    version_schema.update(main_fields)

    return Any(
        Schema(version_schema, extra=PREVENT_EXTRA),
        Schema(date_schema, extra=PREVENT_EXTRA),
    )


def author(value):
    if value is None:
        return value  # let schema checks handle

    if not is_iterable(value):
        value = [value]

    for line in value:
        if not isinstance(line, string_types):
            continue  # let schema checks handle
        m = author_line.search(line)
        if not m:
            raise Invalid("Invalid author")

    return value


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
        'extends_documentation_fragment': Any(list_string_types, *string_types),
        'version_added_collection': collection_name,
        'attributes': object,
    }

    if for_collection:
        # Optional
        doc_schema_dict['version_added'] = version(for_collection=True)
    else:
        doc_schema_dict[Required('version_added')] = version(for_collection=False)

    if deprecated_module:
        deprecation_required_scheme = {
            Required('deprecated'): Any(deprecation_schema(for_collection=for_collection)),
        }

        doc_schema_dict.update(deprecation_required_scheme)
    return Schema(
        All(
            Schema(
                doc_schema_dict,
                extra=PREVENT_EXTRA
            ),
            partial(version_added, error_code='module-invalid-version-added', accept_historical=not for_collection),
        )
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
