# -*- coding: utf-8 -*-

# Copyright: (c) 2015, Matt Martz <matt@sivel.net>
# Copyright: (c) 2015, Rackspace US, Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import annotations

import re

from ansible.module_utils.compat.version import StrictVersion
from functools import partial
from urllib.parse import urlparse

from voluptuous import ALLOW_EXTRA, PREVENT_EXTRA, All, Any, Invalid, Length, MultipleInvalid, Required, Schema, Self, ValueInvalid, Exclusive
from ansible.constants import DOCUMENTABLE_PLUGINS
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.parsing.quoting import unquote
from ansible.utils.version import SemanticVersion
from ansible.release import __version__

from antsibull_docs_parser import dom
from antsibull_docs_parser.parser import parse, Context

from .utils import parse_isodate

list_string_types = [str]
tuple_string_types = (str,)

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


COLLECTION_NAME_RE = re.compile(r'^\w+(?:\.\w+)+$')
FULLY_QUALIFIED_COLLECTION_RESOURCE_RE = re.compile(r'^\w+(?:\.\w+){2,}$')


def collection_name(v, error_code=None):
    if not isinstance(v, str):
        raise _add_ansible_error_code(
            Invalid('Collection name must be a string'), error_code or 'collection-invalid-name')
    m = COLLECTION_NAME_RE.match(v)
    if not m:
        raise _add_ansible_error_code(
            Invalid('Collection name must be of format `<namespace>.<name>`'), error_code or 'collection-invalid-name')
    return v


def fqcn(v, error_code=None):
    if not isinstance(v, str):
        raise _add_ansible_error_code(
            Invalid('Module/plugin name must be a string'), error_code or 'invalid-documentation')
    m = FULLY_QUALIFIED_COLLECTION_RESOURCE_RE.match(v)
    if not m:
        raise _add_ansible_error_code(
            Invalid('Module/plugin name must be of format `<namespace>.<collection>.<name>(.<subname>)*`'), error_code or 'invalid-documentation')
    return v


def deprecation_versions():
    """Create a list of valid version for deprecation entries, current+4"""
    major, minor = [int(version) for version in __version__.split('.')[0:2]]
    return Any(*['{0}.{1}'.format(major, minor + increment) for increment in range(0, 5)])


def version(for_collection=False):
    if for_collection:
        # We do not accept floats for versions in collections
        return str
    return Any(float, str)


def date(error_code=None):
    return Any(isodate, error_code=error_code)


def require_only_one(keys):
    def f(obj):
        found = None
        for k in obj.keys():
            if k in keys:
                if found is None:
                    found = k
                else:
                    raise Invalid('Found conflicting keys, must contain only one of {}'.format(keys))
        if found is None:
            raise Invalid('Must contain one of {}'.format(keys))

        return obj
    return f


# Roles can also be referenced by semantic markup
_VALID_PLUGIN_TYPES = set(DOCUMENTABLE_PLUGINS + ('role', ))


def _check_url(directive, content):
    try:
        parsed_url = urlparse(content)
        if parsed_url.scheme not in ('', 'http', 'https'):
            raise ValueError('Schema must be HTTP, HTTPS, or not specified')
        return []
    except ValueError:
        return [_add_ansible_error_code(
            Invalid('Directive %s must contain a valid URL' % directive), 'invalid-documentation-markup')]


def doc_string(v):
    """Match a documentation string."""
    if not isinstance(v, str):
        raise _add_ansible_error_code(
            Invalid('Must be a string'), 'invalid-documentation')
    errors = []
    for par in parse(v, Context(), errors='message', strict=True, add_source=True):
        for part in par:
            if part.type == dom.PartType.ERROR:
                errors.append(_add_ansible_error_code(Invalid(part.message), 'invalid-documentation-markup'))
            if part.type == dom.PartType.URL:
                errors.extend(_check_url('U()', part.url))
            if part.type == dom.PartType.LINK:
                errors.extend(_check_url('L()', part.url))
            if part.type == dom.PartType.MODULE:
                if not FULLY_QUALIFIED_COLLECTION_RESOURCE_RE.match(part.fqcn):
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a FQCN; found "%s"' % (part.source, part.fqcn)),
                        'invalid-documentation-markup'))
            if part.type == dom.PartType.PLUGIN:
                if not FULLY_QUALIFIED_COLLECTION_RESOURCE_RE.match(part.plugin.fqcn):
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a FQCN; found "%s"' % (part.source, part.plugin.fqcn)),
                        'invalid-documentation-markup'))
                if part.plugin.type not in _VALID_PLUGIN_TYPES:
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a valid plugin type; found "%s"' % (part.source, part.plugin.type)),
                        'invalid-documentation-markup'))
            if part.type == dom.PartType.OPTION_NAME:
                if part.plugin is not None and not FULLY_QUALIFIED_COLLECTION_RESOURCE_RE.match(part.plugin.fqcn):
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a FQCN; found "%s"' % (part.source, part.plugin.fqcn)),
                        'invalid-documentation-markup'))
                if part.plugin is not None and part.plugin.type not in _VALID_PLUGIN_TYPES:
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a valid plugin type; found "%s"' % (part.source, part.plugin.type)),
                        'invalid-documentation-markup'))
            if part.type == dom.PartType.RETURN_VALUE:
                if part.plugin is not None and not FULLY_QUALIFIED_COLLECTION_RESOURCE_RE.match(part.plugin.fqcn):
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a FQCN; found "%s"' % (part.source, part.plugin.fqcn)),
                        'invalid-documentation-markup'))
                if part.plugin is not None and part.plugin.type not in _VALID_PLUGIN_TYPES:
                    errors.append(_add_ansible_error_code(Invalid(
                        'Directive "%s" must contain a valid plugin type; found "%s"' % (part.source, part.plugin.type)),
                        'invalid-documentation-markup'))
    if len(errors) == 1:
        raise errors[0]
    if errors:
        raise MultipleInvalid(errors)
    return v


doc_string_or_strings = Any(doc_string, [doc_string])


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
                Required('module'): fqcn,
                'description': doc_string,
            },
            {
                Required('plugin'): fqcn,
                Required('plugin_type'): Any(*DOCUMENTABLE_PLUGINS),
                'description': doc_string,
            },
            {
                Required('ref'): str,
                Required('description'): doc_string,
            },
            {
                Required('name'): str,
                Required('link'): str,
                Required('description'): doc_string,
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
    'required_by': Schema({str: Any(list_string_types, tuple_string_types, str)}),
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


def check_removal_version(v, version_field, collection_name_field, error_code='invalid-removal-version'):
    version = v.get(version_field)
    collection_name = v.get(collection_name_field)
    if not isinstance(version, str) or not isinstance(collection_name, str):
        # If they are not strings, schema validation will have already complained.
        return v
    if collection_name == 'ansible.builtin':
        try:
            parsed_version = StrictVersion()
            parsed_version.parse(version)
        except ValueError as exc:
            raise _add_ansible_error_code(
                Invalid('%s (%r) is not a valid ansible-core version: %s' % (version_field, version, exc)),
                error_code=error_code)
        return v
    try:
        parsed_version = SemanticVersion()
        parsed_version.parse(version)
        if parsed_version.major != 0 and (parsed_version.minor != 0 or parsed_version.patch != 0):
            raise _add_ansible_error_code(
                Invalid('%s (%r) must be a major release, not a minor or patch release (see specification at '
                        'https://semver.org/)' % (version_field, version)),
                error_code='removal-version-must-be-major')
    except ValueError as exc:
        raise _add_ansible_error_code(
            Invalid('%s (%r) is not a valid collection version (see specification at https://semver.org/): '
                    '%s' % (version_field, version, exc)),
            error_code=error_code)
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
        check_removal_version(v,
                              version_field='removed_in_version',
                              collection_name_field='removed_from_collection',
                              error_code='invalid-removal-version')
        return
    if v.get('removed_from_collection'):
        raise Invalid('removed_from_collection cannot be specified without either '
                      'removed_in_version or removed_at_date')


def argument_spec_schema(for_collection):
    schema = {
        str: {
            'type': Any(is_callable, *argument_spec_types),
            'elements': Any(*argument_spec_types),
            'default': object,
            'fallback': Any(
                (is_callable, list_string_types),
                [is_callable, list_string_types],
            ),
            'choices': Any([object], (object,)),
            'context': dict,
            'required': bool,
            'no_log': bool,
            'aliases': Any(list_string_types, tuple(list_string_types)),
            'apply_defaults': bool,
            'removed_in_version': version(for_collection),
            'removed_at_date': date(),
            'removed_from_collection': collection_name,
            'options': Self,
            'deprecated_aliases': Any([All(
                Any(
                    {
                        Required('name'): str,
                        Required('date'): date(),
                        Required('collection_name'): collection_name,
                    },
                    {
                        Required('name'): str,
                        Required('version'): version(for_collection),
                        Required('collection_name'): collection_name,
                    },
                ),
                partial(check_removal_version,
                        version_field='version',
                        collection_name_field='collection_name',
                        error_code='invalid-removal-version')
            )]),
        }
    }
    schema[str].update(argument_spec_modifiers)
    schemas = All(
        schema,
        Schema({str: no_required_with_default}),
        Schema({str: elements_with_list}),
        Schema({str: options_with_apply_defaults}),
        Schema({str: option_deprecation}),
    )
    return Schema(schemas)


def ansible_module_kwargs_schema(module_name, for_collection):
    schema = {
        'argument_spec': argument_spec_schema(for_collection),
        'bypass_checks': bool,
        'no_log': bool,
        'check_invalid_arguments': Any(None, bool),
        'add_file_common_args': bool,
        'supports_check_mode': bool,
    }
    if module_name.endswith(('_info', '_facts')):
        del schema['supports_check_mode']
        schema[Required('supports_check_mode')] = True
    schema.update(argument_spec_modifiers)
    return Schema(schema)


json_value = Schema(Any(
    None,
    int,
    float,
    [Self],
    {str: Self},
    str,
))


def version_added(v, error_code='version-added-invalid', accept_historical=False):
    if 'version_added' in v:
        version_added = v.get('version_added')
        if isinstance(version_added, str):
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
                        Invalid('version_added (%r) is not a valid ansible-core version: '
                                '%s' % (version_added, exc)),
                        error_code=error_code)
            else:
                try:
                    version = SemanticVersion()
                    version.parse(version_added)
                    if version.major != 0 and version.patch != 0:
                        raise _add_ansible_error_code(
                            Invalid('version_added (%r) must be a major or minor release, '
                                    'not a patch release (see specification at '
                                    'https://semver.org/)' % (version_added, )),
                            error_code='version-added-must-be-major-or-minor')
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


def check_option_elements(v):
    # Check whether elements is there iff type == 'list'
    v_type = v.get('type')
    v_elements = v.get('elements')
    if v_type == 'list' and v_elements is None:
        raise _add_ansible_error_code(
            Invalid('Argument defines type as list but elements is not defined'),
            error_code='parameter-list-no-elements')  # FIXME: adjust error code?
    if v_type != 'list' and v_elements is not None:
        raise _add_ansible_error_code(
            Invalid('Argument defines parameter elements as %s but it is valid only when value of parameter type is list' % (v_elements, )),
            error_code='doc-elements-invalid')
    return v


def get_type_checker(v):
    v_type = v.get('type')
    if v_type == 'list':
        elt_checker, elt_name = get_type_checker({'type': v.get('elements')})

        def list_checker(value):
            if isinstance(value, str):
                value = [unquote(x.strip()) for x in value.split(',')]
            if not isinstance(value, list):
                raise ValueError('Value must be a list')
            if elt_checker:
                for elt in value:
                    try:
                        elt_checker(elt)
                    except Exception as exc:
                        raise ValueError('Entry %r is not of type %s: %s' % (elt, elt_name, exc))

        return list_checker, ('list of %s' % elt_name) if elt_checker else 'list'

    if v_type in ('boolean', 'bool'):
        return partial(boolean, strict=False), v_type

    if v_type in ('integer', 'int'):
        return int, v_type

    if v_type == 'float':
        return float, v_type

    if v_type == 'none':
        def none_checker(value):
            if value not in ('None', None):
                raise ValueError('Value must be "None" or none')

        return none_checker, v_type

    if v_type in ('str', 'string', 'path', 'tmp', 'temppath', 'tmppath'):
        def str_checker(value):
            if not isinstance(value, str):
                raise ValueError('Value must be string')

        return str_checker, v_type

    if v_type in ('pathspec', 'pathlist'):
        def path_list_checker(value):
            if not isinstance(value, str) and not is_iterable(value):
                raise ValueError('Value must be string or list of strings')

        return path_list_checker, v_type

    if v_type in ('dict', 'dictionary'):
        def dict_checker(value):
            if not isinstance(value, dict):
                raise ValueError('Value must be dictionary')

        return dict_checker, v_type

    return None, 'unknown'


def check_option_choices(v):
    # Check whether choices have the correct type
    v_choices = v.get('choices')
    if not is_iterable(v_choices):
        return v

    if v.get('type') == 'list':
        # choices for a list type means that every list element must be one of these choices
        type_checker, type_name = get_type_checker({'type': v.get('elements')})
    else:
        type_checker, type_name = get_type_checker(v)

    if type_checker is None:
        return v

    if isinstance(v_choices, dict):
        # choices are still a list (the keys) but dict form serves to document each choice.
        iterate = v_choices.keys()
    else:
        iterate = v_choices

    for value in iterate:
        try:
            type_checker(value)
        except Exception as exc:
            raise _add_ansible_error_code(
                Invalid(
                    'Argument defines choices as (%r) but this is incompatible with argument type %s: %s' % (value, type_name, exc)),
                error_code='doc-choices-incompatible-type')

    return v


def check_option_default(v):
    # Check whether default is only present if required=False, and whether default has correct type
    v_default = v.get('default')
    if v.get('required') and v_default is not None:
        raise _add_ansible_error_code(
            Invalid(
                'Argument is marked as required but specifies a default.'
                ' Arguments with a default should not be marked as required'),
            error_code='no-default-for-required-parameter')  # FIXME: adjust error code?

    if v_default is None:
        return v

    type_checker, type_name = get_type_checker(v)
    if type_checker is None:
        return v

    try:
        type_checker(v_default)
    except Exception as exc:
        raise _add_ansible_error_code(
            Invalid(
                'Argument defines default as (%r) but this is incompatible with parameter type %s: %s' % (v_default, type_name, exc)),
            error_code='incompatible-default-type')

    return v


def list_dict_option_schema(for_collection, plugin_type):
    if plugin_type == 'module':
        option_types = Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str')
        element_types = option_types
    else:
        option_types = Any(None, 'boolean', 'bool', 'integer', 'int', 'float', 'list', 'dict', 'dictionary', 'none',
                           'path', 'tmp', 'temppath', 'tmppath', 'pathspec', 'pathlist', 'str', 'string', 'raw')
        element_types = Any(None, 'boolean', 'bool', 'integer', 'int', 'float', 'list', 'dict', 'dictionary', 'path', 'str', 'string', 'raw')

    basic_option_schema = {
        Required('description'): doc_string_or_strings,
        'required': bool,
        'choices': Any(list, {object: doc_string_or_strings}),
        'aliases': Any(list_string_types),
        'version_added': version(for_collection),
        'version_added_collection': collection_name,
        'default': json_value,
        # Note: Types are strings, not literal bools, such as True or False
        'type': option_types,
        # in case of type='list' elements define type of individual item in list
        'elements': element_types,
    }
    if plugin_type != 'module':
        basic_option_schema['name'] = str
        deprecated_schema = All(
            Schema(
                All(
                    {
                        # This definition makes sure everything has the correct types/values
                        'why': doc_string,
                        # TODO: phase out either plural or singular, 'alt' is exclusive group
                        Exclusive('alternative', 'alt'): doc_string,
                        Exclusive('alternatives', 'alt'): doc_string,
                        # vod stands for 'version or date'; this is the name of the exclusive group
                        Exclusive('removed_at_date', 'vod'): date(),
                        Exclusive('version', 'vod'): version(for_collection),
                        'collection_name': collection_name,
                    },
                    {
                        # This definition makes sure that everything we require is there
                        Required('why'): str,
                        Required(Any('alternatives', 'alternative')): str,
                        Required(Any('removed_at_date', 'version')): str,
                        Required('collection_name'): str,
                    },
                ),
                extra=PREVENT_EXTRA
            ),
            partial(check_removal_version,
                    version_field='version',
                    collection_name_field='collection_name',
                    error_code='invalid-removal-version'),
        )
        env_schema = All(
            Schema({
                Required('name'): str,
                'deprecated': deprecated_schema,
                'version_added': version(for_collection),
                'version_added_collection': collection_name,
            }, extra=PREVENT_EXTRA),
            partial(version_added, error_code='option-invalid-version-added')
        )
        ini_schema = All(
            Schema({
                Required('key'): str,
                Required('section'): str,
                'deprecated': deprecated_schema,
                'version_added': version(for_collection),
                'version_added_collection': collection_name,
            }, extra=PREVENT_EXTRA),
            partial(version_added, error_code='option-invalid-version-added')
        )
        vars_schema = All(
            Schema({
                Required('name'): str,
                'deprecated': deprecated_schema,
                'version_added': version(for_collection),
                'version_added_collection': collection_name,
            }, extra=PREVENT_EXTRA),
            partial(version_added, error_code='option-invalid-version-added')
        )
        cli_schema = All(
            Schema({
                Required('name'): str,
                'option': str,
                'deprecated': deprecated_schema,
                'version_added': version(for_collection),
                'version_added_collection': collection_name,
            }, extra=PREVENT_EXTRA),
            partial(version_added, error_code='option-invalid-version-added')
        )
        keyword_schema = All(
            Schema({
                Required('name'): str,
                'deprecated': deprecated_schema,
                'version_added': version(for_collection),
                'version_added_collection': collection_name,
            }, extra=PREVENT_EXTRA),
            partial(version_added, error_code='option-invalid-version-added')
        )
        basic_option_schema.update({
            'env': [env_schema],
            'ini': [ini_schema],
            'vars': [vars_schema],
            'cli': [cli_schema],
            'keyword': [keyword_schema],
            'deprecated': deprecated_schema,
        })

    suboption_schema = dict(basic_option_schema)
    suboption_schema.update({
        # Recursive suboptions
        'suboptions': Any(None, {str: Self}),
    })
    suboption_schema = Schema(All(
        suboption_schema,
        check_option_elements,
        check_option_choices,
        check_option_default,
    ), extra=PREVENT_EXTRA)

    option_schema = dict(basic_option_schema)
    option_schema.update({
        'suboptions': Any(None, {str: suboption_schema}),
    })
    option_schema = Schema(All(
        option_schema,
        check_option_elements,
        check_option_choices,
        check_option_default,
    ), extra=PREVENT_EXTRA)

    option_version_added = Schema(
        All({
            'suboptions': Any(None, {str: Self}),
        }, partial(version_added, error_code='option-invalid-version-added')),
        extra=ALLOW_EXTRA
    )

    return [{str: All(option_schema, option_version_added)}]


def return_contains(v):
    schema = Schema(
        {
            Required('contains'): Any(dict, list, str)
        },
        extra=ALLOW_EXTRA
    )
    if v.get('type') == 'complex':
        return schema(v)
    return v


def return_schema(for_collection, plugin_type='module'):
    if plugin_type == 'module':
        return_types = Any('bool', 'complex', 'dict', 'float', 'int', 'list', 'raw', 'str')
        element_types = Any(None, 'bits', 'bool', 'bytes', 'dict', 'float', 'int', 'json', 'jsonarg', 'list', 'path', 'raw', 'sid', 'str')
    else:
        return_types = Any(None, 'boolean', 'bool', 'integer', 'int', 'float', 'list', 'dict', 'dictionary', 'path', 'str', 'string', 'raw')
        element_types = return_types

    basic_return_option_schema = {
        Required('description'): doc_string_or_strings,
        'returned': doc_string,
        'version_added': version(for_collection),
        'version_added_collection': collection_name,
        'sample': json_value,
        'example': json_value,
        # in case of type='list' elements define type of individual item in list
        'elements': element_types,
        'choices': Any([object], (object,)),
    }
    if plugin_type == 'module':
        # type is only required for modules right now
        basic_return_option_schema[Required('type')] = return_types
    else:
        basic_return_option_schema['type'] = return_types

    inner_return_option_schema = dict(basic_return_option_schema)
    inner_return_option_schema.update({
        'contains': Any(None, {str: Self}),
    })
    return_contains_schema = Any(
        All(
            Schema(inner_return_option_schema),
            Schema(return_contains),
            Schema(partial(version_added, error_code='option-invalid-version-added')),
        ),
        Schema(type(None)),
    )

    return_option_schema = dict(basic_return_option_schema)
    return_option_schema.update({
        'contains': Any(None, {str: return_contains_schema}),
    })
    if plugin_type == 'module':
        # 'returned' is required on top-level
        del return_option_schema['returned']
        return_option_schema[Required('returned')] = str
    return Any(
        All(
            Schema(
                {
                    str: return_option_schema
                }
            ),
            Schema({str: return_contains}),
            Schema({str: partial(version_added, error_code='option-invalid-version-added')}),
        ),
        Schema(type(None)),
    )


def deprecation_schema(for_collection):

    main_fields = {
        Required('why'): doc_string,
        'alternative': doc_string,
        'alternatives': doc_string,
    }

    if for_collection:
        main_fields.update({Required('removed_from_collection'): collection_name, 'removed': Any(True)})

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
            Required('removed_in'): deprecation_versions(),
        }
    version_schema.update(main_fields)

    result = Any(
        Schema(version_schema, extra=PREVENT_EXTRA),
        Schema(date_schema, extra=PREVENT_EXTRA),
    )

    if for_collection:
        result = All(
            result,
            require_only_one(['alternative', 'alternatives']),
            partial(check_removal_version,
                    version_field='removed_in',
                    collection_name_field='removed_from_collection',
                    error_code='invalid-removal-version'))

    return result


def author(value):
    if value is None:
        return value  # let schema checks handle

    if not is_iterable(value):
        value = [value]

    for line in value:
        if not isinstance(line, str):
            continue  # let schema checks handle
        m = author_line.search(line)
        if not m:
            raise Invalid("Invalid author")

    return value


def doc_schema(module_name, for_collection=False, deprecated_module=False, plugin_type='module'):

    if module_name.startswith('_') and not for_collection:
        module_name = module_name[1:]
        deprecated_module = True
    if for_collection is False and plugin_type == 'connection' and module_name == 'paramiko_ssh':
        # The plugin loader has a hard-coded exception: when the builtin connection 'paramiko' is
        # referenced, it loads 'paramiko_ssh' instead. That's why in this plugin, the name must be
        # 'paramiko' and not 'paramiko_ssh'.
        module_name = 'paramiko'
    doc_schema_dict = {
        Required('module' if plugin_type == 'module' else 'name'): module_name,
        Required('short_description'): doc_string,
        Required('description'): doc_string_or_strings,
        'notes': Any(None, [doc_string]),
        'seealso': Any(None, seealso_schema),
        'requirements': [doc_string],
        'todo': Any(None, doc_string_or_strings),
        'options': Any(None, *list_dict_option_schema(for_collection, plugin_type)),
        'extends_documentation_fragment': Any(list_string_types, str),
        'version_added_collection': collection_name,
    }
    if plugin_type == 'module':
        doc_schema_dict[Required('author')] = All(Any(None, list_string_types, str), author)
    else:
        # author is optional for plugins (for now)
        doc_schema_dict['author'] = All(Any(None, list_string_types, str), author)
    if plugin_type == 'callback':
        doc_schema_dict[Required('type')] = Any('aggregate', 'notification', 'stdout')

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

    def add_default_attributes(more=None):
        schema = {
            'description': doc_string_or_strings,
            'details': doc_string_or_strings,
            'support': str,
            'version_added_collection': str,
            'version_added': str,
        }
        if more:
            schema.update(more)
        return schema

    doc_schema_dict['attributes'] = Schema(
        All(
            Schema({
                str: {
                    Required('description'): doc_string_or_strings,
                    Required('support'): Any('full', 'partial', 'none', 'N/A'),
                    'details': doc_string_or_strings,
                    'version_added_collection': collection_name,
                    'version_added': version(for_collection=for_collection),
                },
            }, extra=ALLOW_EXTRA),
            partial(version_added, error_code='attribute-invalid-version-added', accept_historical=False),
            Schema({
                str: add_default_attributes(),
                'action_group': add_default_attributes({
                    Required('membership'): list_string_types,
                }),
                'platform': add_default_attributes({
                    Required('platforms'): Any(list_string_types, str)
                }),
            }, extra=PREVENT_EXTRA),
        )
    )
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
