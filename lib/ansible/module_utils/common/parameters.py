# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils._text import to_native
from ansible.module_utils.common._collections_compat import Mapping
from ansible.module_utils.common.collections import is_iterable

from ansible.module_utils.six import (
    binary_type,
    integer_types,
    string_types,
    text_type,
)

from ansible.module_utils.common.validation import (
    check_type_bits,
    check_type_bool,
    check_type_bytes,
    check_type_dict,
    check_type_float,
    check_type_int,
    check_type_jsonarg,
    check_type_list,
    check_type_path,
    check_type_raw,
    check_type_str,
)

# Python2 & 3 way to get NoneType
NoneType = type(None)

# if adding boolean attribute, also add to PASS_BOOL
# some of this dupes defaults from controller config
PASS_VARS = {
    'check_mode': ('check_mode', False),
    'debug': ('_debug', False),
    'diff': ('_diff', False),
    'keep_remote_files': ('_keep_remote_files', False),
    'module_name': ('_name', None),
    'no_log': ('no_log', False),
    'remote_tmp': ('_remote_tmp', None),
    'selinux_special_fs': ('_selinux_special_fs', ['fuse', 'nfs', 'vboxsf', 'ramfs', '9p', 'vfat']),
    'shell_executable': ('_shell', '/bin/sh'),
    'socket': ('_socket_path', None),
    'string_conversion_action': ('_string_conversion_action', 'warn'),
    'syslog_facility': ('_syslog_facility', 'INFO'),
    'tmpdir': ('_tmpdir', None),
    'verbosity': ('_verbosity', 0),
    'version': ('ansible_version', '0.0'),
}

PASS_BOOLS = ('check_mode', 'debug', 'diff', 'keep_remote_files', 'no_log')

DEFAULT_TYPE_VALIDATORS = {
    'str': check_type_str,
    'list': check_type_list,
    'dict': check_type_dict,
    'bool': check_type_bool,
    'int': check_type_int,
    'float': check_type_float,
    'path': check_type_path,
    'raw': check_type_raw,
    'jsonarg': check_type_jsonarg,
    'json': check_type_jsonarg,
    'bytes': check_type_bytes,
    'bits': check_type_bits,
}


def _return_datastructure_name(obj):
    """ Return native stringified values from datastructures.

    For use with removing sensitive values pre-jsonification."""
    if isinstance(obj, (text_type, binary_type)):
        if obj:
            yield to_native(obj, errors='surrogate_or_strict')
        return
    elif isinstance(obj, Mapping):
        for element in obj.items():
            for subelement in _return_datastructure_name(element[1]):
                yield subelement
    elif is_iterable(obj):
        for element in obj:
            for subelement in _return_datastructure_name(element):
                yield subelement
    elif isinstance(obj, (bool, NoneType)):
        # This must come before int because bools are also ints
        return
    elif isinstance(obj, tuple(list(integer_types) + [float])):
        yield to_native(obj, nonstring='simplerepr')
    else:
        raise TypeError('Unknown parameter type: %s' % (type(obj)))


def list_no_log_values(argument_spec, params):
    """Return set of no log values

    :arg argument_spec: An argument spec dictionary from a module
    :arg params: Dictionary of all module parameters

    :returns: Set of strings that should be hidden from output::

        {'secret_dict_value', 'secret_list_item_one', 'secret_list_item_two', 'secret_string'}
    """

    no_log_values = set()
    for arg_name, arg_opts in argument_spec.items():
        if arg_opts.get('no_log', False):
            # Find the value for the no_log'd param
            no_log_object = params.get(arg_name, None)

            if no_log_object:
                try:
                    no_log_values.update(_return_datastructure_name(no_log_object))
                except TypeError as e:
                    raise TypeError('Failed to convert "%s": %s' % (arg_name, to_native(e)))

        # Get no_log values from suboptions
        sub_argument_spec = arg_opts.get('options')
        if sub_argument_spec is not None:
            wanted_type = arg_opts.get('type')
            sub_parameters = params.get(arg_name)

            if sub_parameters is not None:
                if wanted_type == 'dict' or (wanted_type == 'list' and arg_opts.get('elements', '') == 'dict'):
                    # Sub parameters can be a dict or list of dicts. Ensure parameters are always a list.
                    if not isinstance(sub_parameters, list):
                        sub_parameters = [sub_parameters]

                    for sub_param in sub_parameters:
                        # Validate dict fields in case they came in as strings

                        if isinstance(sub_param, string_types):
                            sub_param = check_type_dict(sub_param)

                        if not isinstance(sub_param, Mapping):
                            raise TypeError("Value '{1}' in the sub parameter field '{0}' must by a {2}, "
                                            "not '{1.__class__.__name__}'".format(arg_name, sub_param, wanted_type))

                        no_log_values.update(list_no_log_values(sub_argument_spec, sub_param))

    return no_log_values


def list_deprecations(argument_spec, params, prefix=''):
    """Return a list of deprecations

    :arg argument_spec: An argument spec dictionary from a module
    :arg params: Dictionary of all module parameters

    :returns: List of dictionaries containing a message and version in which
        the deprecated parameter will be removed, or an empty list::

            [{'msg': "Param 'deptest' is deprecated. See the module docs for more information", 'version': '2.9'}]
    """

    deprecations = []
    for arg_name, arg_opts in argument_spec.items():
        if arg_name in params:
            if prefix:
                sub_prefix = '%s["%s"]' % (prefix, arg_name)
            else:
                sub_prefix = arg_name
            if arg_opts.get('removed_at_date') is not None:
                deprecations.append({
                    'msg': "Param '%s' is deprecated. See the module docs for more information" % sub_prefix,
                    'date': arg_opts.get('removed_at_date'),
                    'collection_name': arg_opts.get('removed_from_collection'),
                })
            elif arg_opts.get('removed_in_version') is not None:
                deprecations.append({
                    'msg': "Param '%s' is deprecated. See the module docs for more information" % sub_prefix,
                    'version': arg_opts.get('removed_in_version'),
                    'collection_name': arg_opts.get('removed_from_collection'),
                })
            # Check sub-argument spec
            sub_argument_spec = arg_opts.get('options')
            if sub_argument_spec is not None:
                sub_arguments = params[arg_name]
                if isinstance(sub_arguments, Mapping):
                    sub_arguments = [sub_arguments]
                if isinstance(sub_arguments, list):
                    for sub_params in sub_arguments:
                        if isinstance(sub_params, Mapping):
                            deprecations.extend(list_deprecations(sub_argument_spec, sub_params, prefix=sub_prefix))

    return deprecations


def handle_aliases(argument_spec, params, alias_warnings=None):
    """Return a two item tuple. The first is a dictionary of aliases, the second is
    a list of legal inputs.

    If a list is provided to the alias_warnings parameter, it will be filled with tuples
    (option, alias) in every case where both an option and its alias are specified.
    """

    legal_inputs = ['_ansible_%s' % k for k in PASS_VARS]
    aliases_results = {}  # alias:canon

    for (k, v) in argument_spec.items():
        legal_inputs.append(k)
        aliases = v.get('aliases', None)
        default = v.get('default', None)
        required = v.get('required', False)
        if default is not None and required:
            # not alias specific but this is a good place to check this
            raise ValueError("internal error: required and default are mutually exclusive for %s" % k)
        if aliases is None:
            continue
        if not is_iterable(aliases) or isinstance(aliases, (binary_type, text_type)):
            raise TypeError('internal error: aliases must be a list or tuple')
        for alias in aliases:
            legal_inputs.append(alias)
            aliases_results[alias] = k
            if alias in params:
                if k in params and alias_warnings is not None:
                    alias_warnings.append((k, alias))
                params[k] = params[alias]

    return aliases_results, legal_inputs


def get_unsupported_parameters(argument_spec, module_parameters, legal_inputs=None):
    """Check keys in module_parameters against those provided in legal_inputs
    to ensure they contain legal values. If legal_inputs are not supplied,
    they will be generated using the argument_spec.

    :arg argument_spec: Dictionary of parameters, their type, and valid values.
    :arg module_parameters: Dictionary of module parameters.
    :arg legal_inputs: List of valid key names property names. Overrides values
        in argument_spec.

    :returns: Set of unsupported parameters. Empty set if no unsupported parameters
        are found.
    """

    if legal_inputs is None:
        aliases, legal_inputs = handle_aliases(argument_spec, module_parameters)

    unsupported_parameters = set()
    for k in module_parameters.keys():
        if k not in legal_inputs:
            unsupported_parameters.add(k)

    return unsupported_parameters


def get_type_validator(wanted):
    """Returns the callable used to validate a wanted type and the type name.

    :arg wanted: String or callable. If a string, get the corresponding
        validation function from DEFAULT_TYPE_VALIDATORS. If callable,
        get the name of the custom callable and return that for the type_checker.

    :returns: Tuple of callable function or None, and a string that is the name
        of the wanted type.
    """

    # Use one our our builtin validators.
    if not callable(wanted):
        if wanted is None:
            # Default type for parameters
            wanted = 'str'

        type_checker = DEFAULT_TYPE_VALIDATORS.get(wanted)

    # Use the custom callable for validation.
    else:
        type_checker = wanted
        wanted = getattr(wanted, '__name__', to_native(type(wanted)))

    return type_checker, wanted
