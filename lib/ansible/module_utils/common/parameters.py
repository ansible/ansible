# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import datetime
import os

from collections import deque
from itertools import chain

from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.common.text.formatters import lenient_lowercase
from ansible.module_utils.common.warnings import warn
from ansible.module_utils.errors import (
    AliasError,
    AnsibleFallbackNotFound,
    AnsibleValidationErrorMultiple,
    ArgumentTypeError,
    ArgumentValueError,
    ElementError,
    MutuallyExclusiveError,
    NoLogError,
    RequiredByError,
    RequiredError,
    RequiredIfError,
    RequiredOneOfError,
    RequiredTogetherError,
    SubParameterTypeError,
)
from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE, BOOLEANS_TRUE

from ansible.module_utils.common._collections_compat import (
    KeysView,
    Set,
    Sequence,
    Mapping,
    MutableMapping,
    MutableSet,
    MutableSequence,
)

from ansible.module_utils.six import (
    binary_type,
    integer_types,
    string_types,
    text_type,
    PY2,
    PY3,
)

from ansible.module_utils.common.validation import (
    check_mutually_exclusive,
    check_required_arguments,
    check_required_together,
    check_required_one_of,
    check_required_if,
    check_required_by,
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

_ADDITIONAL_CHECKS = (
    {'func': check_required_together, 'attr': 'required_together', 'err': RequiredTogetherError},
    {'func': check_required_one_of, 'attr': 'required_one_of', 'err': RequiredOneOfError},
    {'func': check_required_if, 'attr': 'required_if', 'err': RequiredIfError},
    {'func': check_required_by, 'attr': 'required_by', 'err': RequiredByError},
)

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


def _get_type_validator(wanted):
    """Returns the callable used to validate a wanted type and the type name.

    :arg wanted: String or callable. If a string, get the corresponding
        validation function from DEFAULT_TYPE_VALIDATORS. If callable,
        get the name of the custom callable and return that for the type_checker.

    :returns: Tuple of callable function or None, and a string that is the name
        of the wanted type.
    """

    # Use one of our builtin validators.
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


def _get_legal_inputs(argument_spec, parameters, aliases=None):
    if aliases is None:
        aliases = _handle_aliases(argument_spec, parameters)

    return list(aliases.keys()) + list(argument_spec.keys())


def _get_unsupported_parameters(argument_spec, parameters, legal_inputs=None, options_context=None):
    """Check keys in parameters against those provided in legal_inputs
    to ensure they contain legal values. If legal_inputs are not supplied,
    they will be generated using the argument_spec.

    :arg argument_spec: Dictionary of parameters, their type, and valid values.
    :arg parameters: Dictionary of parameters.
    :arg legal_inputs: List of valid key names property names. Overrides values
        in argument_spec.
    :arg options_context: List of parent keys for tracking the context of where
        a parameter is defined.

    :returns: Set of unsupported parameters. Empty set if no unsupported parameters
        are found.
    """

    if legal_inputs is None:
        legal_inputs = _get_legal_inputs(argument_spec, parameters)

    unsupported_parameters = set()
    for k in parameters.keys():
        if k not in legal_inputs:
            context = k
            if options_context:
                context = tuple(options_context + [k])

            unsupported_parameters.add(context)

    return unsupported_parameters


def _handle_aliases(argument_spec, parameters, alias_warnings=None, alias_deprecations=None):
    """Process aliases from an argument_spec including warnings and deprecations.

    Modify ``parameters`` by adding a new key for each alias with the supplied
    value from ``parameters``.

    If a list is provided to the alias_warnings parameter, it will be filled with tuples
    (option, alias) in every case where both an option and its alias are specified.

    If a list is provided to alias_deprecations, it will be populated with dictionaries,
    each containing deprecation information for each alias found in argument_spec.

    :param argument_spec: Dictionary of parameters, their type, and valid values.
    :type argument_spec: dict

    :param parameters: Dictionary of parameters.
    :type parameters: dict

    :param alias_warnings:
    :type alias_warnings: list

    :param alias_deprecations:
    :type alias_deprecations: list
    """

    aliases_results = {}  # alias:canon

    for (k, v) in argument_spec.items():
        aliases = v.get('aliases', None)
        default = v.get('default', None)
        required = v.get('required', False)

        if alias_deprecations is not None:
            for alias in argument_spec[k].get('deprecated_aliases', []):
                if alias.get('name') in parameters:
                    alias_deprecations.append(alias)

        if default is not None and required:
            # not alias specific but this is a good place to check this
            raise ValueError("internal error: required and default are mutually exclusive for %s" % k)

        if aliases is None:
            continue

        if not is_iterable(aliases) or isinstance(aliases, (binary_type, text_type)):
            raise TypeError('internal error: aliases must be a list or tuple')

        for alias in aliases:
            aliases_results[alias] = k
            if alias in parameters:
                if k in parameters and alias_warnings is not None:
                    alias_warnings.append((k, alias))
                parameters[k] = parameters[alias]

    return aliases_results


def _list_deprecations(argument_spec, parameters, prefix=''):
    """Return a list of deprecations

    :arg argument_spec: An argument spec dictionary
    :arg parameters: Dictionary of parameters

    :returns: List of dictionaries containing a message and version in which
        the deprecated parameter will be removed, or an empty list.

    :Example return:

    .. code-block:: python

        [
            {
                'msg': "Param 'deptest' is deprecated. See the module docs for more information",
                'version': '2.9'
            }
        ]
    """

    deprecations = []
    for arg_name, arg_opts in argument_spec.items():
        if arg_name in parameters:
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
                sub_arguments = parameters[arg_name]
                if isinstance(sub_arguments, Mapping):
                    sub_arguments = [sub_arguments]
                if isinstance(sub_arguments, list):
                    for sub_params in sub_arguments:
                        if isinstance(sub_params, Mapping):
                            deprecations.extend(_list_deprecations(sub_argument_spec, sub_params, prefix=sub_prefix))

    return deprecations


def _list_no_log_values(argument_spec, params):
    """Return set of no log values

    :arg argument_spec: An argument spec dictionary
    :arg params: Dictionary of all parameters

    :returns: :class:`set` of strings that should be hidden from output:
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

                        no_log_values.update(_list_no_log_values(sub_argument_spec, sub_param))

    return no_log_values


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


def _remove_values_conditions(value, no_log_strings, deferred_removals):
    """
    Helper function for :meth:`remove_values`.

    :arg value: The value to check for strings that need to be stripped
    :arg no_log_strings: set of strings which must be stripped out of any values
    :arg deferred_removals: List which holds information about nested
        containers that have to be iterated for removals.  It is passed into
        this function so that more entries can be added to it if value is
        a container type.  The format of each entry is a 2-tuple where the first
        element is the ``value`` parameter and the second value is a new
        container to copy the elements of ``value`` into once iterated.

    :returns: if ``value`` is a scalar, returns ``value`` with two exceptions:

        1. :class:`~datetime.datetime` objects which are changed into a string representation.
        2. objects which are in ``no_log_strings`` are replaced with a placeholder
           so that no sensitive data is leaked.

        If ``value`` is a container type, returns a new empty container.

    ``deferred_removals`` is added to as a side-effect of this function.

    .. warning:: It is up to the caller to make sure the order in which value
        is passed in is correct.  For instance, higher level containers need
        to be passed in before lower level containers. For example, given
        ``{'level1': {'level2': 'level3': [True]} }`` first pass in the
        dictionary for ``level1``, then the dict for ``level2``, and finally
        the list for ``level3``.
    """
    if isinstance(value, (text_type, binary_type)):
        # Need native str type
        native_str_value = value
        if isinstance(value, text_type):
            value_is_text = True
            if PY2:
                native_str_value = to_bytes(value, errors='surrogate_or_strict')
        elif isinstance(value, binary_type):
            value_is_text = False
            if PY3:
                native_str_value = to_text(value, errors='surrogate_or_strict')

        if native_str_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            native_str_value = native_str_value.replace(omit_me, '*' * 8)

        if value_is_text and isinstance(native_str_value, binary_type):
            value = to_text(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        elif not value_is_text and isinstance(native_str_value, text_type):
            value = to_bytes(native_str_value, encoding='utf-8', errors='surrogate_then_replace')
        else:
            value = native_str_value

    elif isinstance(value, Sequence):
        if isinstance(value, MutableSequence):
            new_value = type(value)()
        else:
            new_value = []  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, Set):
        if isinstance(value, MutableSet):
            new_value = type(value)()
        else:
            new_value = set()  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, Mapping):
        if isinstance(value, MutableMapping):
            new_value = type(value)()
        else:
            new_value = {}  # Need a mutable value
        deferred_removals.append((value, new_value))
        value = new_value

    elif isinstance(value, tuple(chain(integer_types, (float, bool, NoneType)))):
        stringy_value = to_native(value, encoding='utf-8', errors='surrogate_or_strict')
        if stringy_value in no_log_strings:
            return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'
        for omit_me in no_log_strings:
            if omit_me in stringy_value:
                return 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

    elif isinstance(value, (datetime.datetime, datetime.date)):
        value = value.isoformat()
    else:
        raise TypeError('Value of unknown type: %s, %s' % (type(value), value))

    return value


def _set_defaults(argument_spec, parameters, set_default=True):
    """Set default values for parameters when no value is supplied.

    Modifies parameters directly.

    :arg argument_spec: Argument spec
    :type argument_spec: dict

    :arg parameters: Parameters to evaluate
    :type parameters: dict

    :kwarg set_default: Whether or not to set the default values
    :type set_default: bool

    :returns: Set of strings that should not be logged.
    :rtype: set
    """

    no_log_values = set()
    for param, value in argument_spec.items():

        # TODO: Change the default value from None to Sentinel to differentiate between
        #       user supplied None and a default value set by this function.
        default = value.get('default', None)

        # This prevents setting defaults on required items on the 1st run,
        # otherwise will set things without a default to None on the 2nd.
        if param not in parameters and (default is not None or set_default):
            # Make sure any default value for no_log fields are masked.
            if value.get('no_log', False) and default:
                no_log_values.add(default)

            parameters[param] = default

    return no_log_values


def _sanitize_keys_conditions(value, no_log_strings, ignore_keys, deferred_removals):
    """ Helper method to :func:`sanitize_keys` to build ``deferred_removals`` and avoid deep recursion. """
    if isinstance(value, (text_type, binary_type)):
        return value

    if isinstance(value, Sequence):
        if isinstance(value, MutableSequence):
            new_value = type(value)()
        else:
            new_value = []  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, Set):
        if isinstance(value, MutableSet):
            new_value = type(value)()
        else:
            new_value = set()  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, Mapping):
        if isinstance(value, MutableMapping):
            new_value = type(value)()
        else:
            new_value = {}  # Need a mutable value
        deferred_removals.append((value, new_value))
        return new_value

    if isinstance(value, tuple(chain(integer_types, (float, bool, NoneType)))):
        return value

    if isinstance(value, (datetime.datetime, datetime.date)):
        return value

    raise TypeError('Value of unknown type: %s, %s' % (type(value), value))


def _validate_elements(wanted_type, parameter, values, options_context=None, errors=None):

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    type_checker, wanted_element_type = _get_type_validator(wanted_type)
    validated_parameters = []
    # Get param name for strings so we can later display this value in a useful error message if needed
    # Only pass 'kwargs' to our checkers and ignore custom callable checkers
    kwargs = {}
    if wanted_element_type == 'str' and isinstance(wanted_type, string_types):
        if isinstance(parameter, string_types):
            kwargs['param'] = parameter
        elif isinstance(parameter, dict):
            kwargs['param'] = list(parameter.keys())[0]

    for value in values:
        try:
            validated_parameters.append(type_checker(value, **kwargs))
        except (TypeError, ValueError) as e:
            msg = "Elements value for option '%s'" % parameter
            if options_context:
                msg += " found in '%s'" % " -> ".join(options_context)
            msg += " is of type %s and we were unable to convert to %s: %s" % (type(value), wanted_element_type, to_native(e))
            errors.append(ElementError(msg))
    return validated_parameters


def _validate_argument_types(argument_spec, parameters, prefix='', options_context=None, errors=None):
    """Validate that parameter types match the type in the argument spec.

    Determine the appropriate type checker function and run each
    parameter value through that function. All error messages from type checker
    functions are returned. If any parameter fails to validate, it will not
    be in the returned parameters.

    :arg argument_spec: Argument spec
    :type argument_spec: dict

    :arg parameters: Parameters
    :type parameters: dict

    :kwarg prefix: Name of the parent key that contains the spec. Used in the error message
    :type prefix: str

    :kwarg options_context: List of contexts?
    :type options_context: list

    :returns: Two item tuple containing validated and coerced parameters
              and a list of any errors that were encountered.
    :rtype: tuple

    """

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    for param, spec in argument_spec.items():
        if param not in parameters:
            continue

        value = parameters[param]
        if value is None:
            continue

        wanted_type = spec.get('type')
        type_checker, wanted_name = _get_type_validator(wanted_type)
        # Get param name for strings so we can later display this value in a useful error message if needed
        # Only pass 'kwargs' to our checkers and ignore custom callable checkers
        kwargs = {}
        if wanted_name == 'str' and isinstance(wanted_type, string_types):
            kwargs['param'] = list(parameters.keys())[0]

            # Get the name of the parent key if this is a nested option
            if prefix:
                kwargs['prefix'] = prefix

        try:
            parameters[param] = type_checker(value, **kwargs)
            elements_wanted_type = spec.get('elements', None)
            if elements_wanted_type:
                elements = parameters[param]
                if wanted_type != 'list' or not isinstance(elements, list):
                    msg = "Invalid type %s for option '%s'" % (wanted_name, elements)
                    if options_context:
                        msg += " found in '%s'." % " -> ".join(options_context)
                    msg += ", elements value check is supported only with 'list' type"
                    errors.append(ArgumentTypeError(msg))
                parameters[param] = _validate_elements(elements_wanted_type, param, elements, options_context, errors)

        except (TypeError, ValueError) as e:
            msg = "argument '%s' is of type %s" % (param, type(value))
            if options_context:
                msg += " found in '%s'." % " -> ".join(options_context)
            msg += " and we were unable to convert to %s: %s" % (wanted_name, to_native(e))
            errors.append(ArgumentTypeError(msg))


def _validate_argument_values(argument_spec, parameters, options_context=None, errors=None):
    """Ensure all arguments have the requested values, and there are no stray arguments"""

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    for param, spec in argument_spec.items():
        choices = spec.get('choices')
        if choices is None:
            continue

        if isinstance(choices, (frozenset, KeysView, Sequence)) and not isinstance(choices, (binary_type, text_type)):
            if param in parameters:
                # Allow one or more when type='list' param with choices
                if isinstance(parameters[param], list):
                    diff_list = ", ".join([item for item in parameters[param] if item not in choices])
                    if diff_list:
                        choices_str = ", ".join([to_native(c) for c in choices])
                        msg = "value of %s must be one or more of: %s. Got no match for: %s" % (param, choices_str, diff_list)
                        if options_context:
                            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
                        errors.append(ArgumentValueError(msg))
                elif parameters[param] not in choices:
                    # PyYaml converts certain strings to bools. If we can unambiguously convert back, do so before checking
                    # the value. If we can't figure this out, module author is responsible.
                    lowered_choices = None
                    if parameters[param] == 'False':
                        lowered_choices = lenient_lowercase(choices)
                        overlap = BOOLEANS_FALSE.intersection(choices)
                        if len(overlap) == 1:
                            # Extract from a set
                            (parameters[param],) = overlap

                    if parameters[param] == 'True':
                        if lowered_choices is None:
                            lowered_choices = lenient_lowercase(choices)
                        overlap = BOOLEANS_TRUE.intersection(choices)
                        if len(overlap) == 1:
                            (parameters[param],) = overlap

                    if parameters[param] not in choices:
                        choices_str = ", ".join([to_native(c) for c in choices])
                        msg = "value of %s must be one of: %s, got: %s" % (param, choices_str, parameters[param])
                        if options_context:
                            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
                        errors.append(ArgumentValueError(msg))
        else:
            msg = "internal error: choices for argument %s are not iterable: %s" % (param, choices)
            if options_context:
                msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
            errors.append(ArgumentTypeError(msg))


def _validate_sub_spec(argument_spec, parameters, prefix='', options_context=None, errors=None, no_log_values=None, unsupported_parameters=None):
    """Validate sub argument spec.

    This function is recursive.
    """

    if options_context is None:
        options_context = []

    if errors is None:
        errors = AnsibleValidationErrorMultiple()

    if no_log_values is None:
        no_log_values = set()

    if unsupported_parameters is None:
        unsupported_parameters = set()

    for param, value in argument_spec.items():
        wanted = value.get('type')
        if wanted == 'dict' or (wanted == 'list' and value.get('elements', '') == 'dict'):
            sub_spec = value.get('options')
            if value.get('apply_defaults', False):
                if sub_spec is not None:
                    if parameters.get(param) is None:
                        parameters[param] = {}
                else:
                    continue
            elif sub_spec is None or param not in parameters or parameters[param] is None:
                continue

            # Keep track of context for warning messages
            options_context.append(param)

            # Make sure we can iterate over the elements
            if isinstance(parameters[param], dict):
                elements = [parameters[param]]
            else:
                elements = parameters[param]

            for idx, sub_parameters in enumerate(elements):
                if not isinstance(sub_parameters, dict):
                    errors.append(SubParameterTypeError("value of '%s' must be of type dict or list of dicts" % param))

                # Set prefix for warning messages
                new_prefix = prefix + param
                if wanted == 'list':
                    new_prefix += '[%d]' % idx
                new_prefix += '.'

                no_log_values.update(set_fallbacks(sub_spec, sub_parameters))

                alias_warnings = []
                alias_deprecations = []
                try:
                    options_aliases = _handle_aliases(sub_spec, sub_parameters, alias_warnings, alias_deprecations)
                except (TypeError, ValueError) as e:
                    options_aliases = {}
                    errors.append(AliasError(to_native(e)))

                for option, alias in alias_warnings:
                    warn('Both option %s and its alias %s are set.' % (option, alias))

                try:
                    no_log_values.update(_list_no_log_values(sub_spec, sub_parameters))
                except TypeError as te:
                    errors.append(NoLogError(to_native(te)))

                legal_inputs = _get_legal_inputs(sub_spec, sub_parameters, options_aliases)
                unsupported_parameters.update(_get_unsupported_parameters(sub_spec, sub_parameters, legal_inputs, options_context))

                try:
                    check_mutually_exclusive(value.get('mutually_exclusive'), sub_parameters, options_context)
                except TypeError as e:
                    errors.append(MutuallyExclusiveError(to_native(e)))

                no_log_values.update(_set_defaults(sub_spec, sub_parameters, False))

                try:
                    check_required_arguments(sub_spec, sub_parameters, options_context)
                except TypeError as e:
                    errors.append(RequiredError(to_native(e)))

                _validate_argument_types(sub_spec, sub_parameters, new_prefix, options_context, errors=errors)
                _validate_argument_values(sub_spec, sub_parameters, options_context, errors=errors)

                for check in _ADDITIONAL_CHECKS:
                    try:
                        check['func'](value.get(check['attr']), sub_parameters, options_context)
                    except TypeError as e:
                        errors.append(check['err'](to_native(e)))

                no_log_values.update(_set_defaults(sub_spec, sub_parameters))

                # Handle nested specs
                _validate_sub_spec(sub_spec, sub_parameters, new_prefix, options_context, errors, no_log_values, unsupported_parameters)

            options_context.pop()


def env_fallback(*args, **kwargs):
    """Load value from environment variable"""

    for arg in args:
        if arg in os.environ:
            return os.environ[arg]
    raise AnsibleFallbackNotFound


def set_fallbacks(argument_spec, parameters):
    no_log_values = set()
    for param, value in argument_spec.items():
        fallback = value.get('fallback', (None,))
        fallback_strategy = fallback[0]
        fallback_args = []
        fallback_kwargs = {}
        if param not in parameters and fallback_strategy is not None:
            for item in fallback[1:]:
                if isinstance(item, dict):
                    fallback_kwargs = item
                else:
                    fallback_args = item
            try:
                fallback_value = fallback_strategy(*fallback_args, **fallback_kwargs)
            except AnsibleFallbackNotFound:
                continue
            else:
                if value.get('no_log', False) and fallback_value:
                    no_log_values.add(fallback_value)
                parameters[param] = fallback_value

    return no_log_values


def sanitize_keys(obj, no_log_strings, ignore_keys=frozenset()):
    """Sanitize the keys in a container object by removing ``no_log`` values from key names.

    This is a companion function to the :func:`remove_values` function. Similar to that function,
    we make use of ``deferred_removals`` to avoid hitting maximum recursion depth in cases of
    large data structures.

    :arg obj: The container object to sanitize. Non-container objects are returned unmodified.
    :arg no_log_strings: A set of string values we do not want logged.
    :kwarg ignore_keys: A set of string values of keys to not sanitize.

    :returns: An object with sanitized keys.
    """

    deferred_removals = deque()

    no_log_strings = [to_native(s, errors='surrogate_or_strict') for s in no_log_strings]
    new_value = _sanitize_keys_conditions(obj, no_log_strings, ignore_keys, deferred_removals)

    while deferred_removals:
        old_data, new_data = deferred_removals.popleft()

        if isinstance(new_data, Mapping):
            for old_key, old_elem in old_data.items():
                if old_key in ignore_keys or old_key.startswith('_ansible'):
                    new_data[old_key] = _sanitize_keys_conditions(old_elem, no_log_strings, ignore_keys, deferred_removals)
                else:
                    # Sanitize the old key. We take advantage of the sanitizing code in
                    # _remove_values_conditions() rather than recreating it here.
                    new_key = _remove_values_conditions(old_key, no_log_strings, None)
                    new_data[new_key] = _sanitize_keys_conditions(old_elem, no_log_strings, ignore_keys, deferred_removals)
        else:
            for elem in old_data:
                new_elem = _sanitize_keys_conditions(elem, no_log_strings, ignore_keys, deferred_removals)
                if isinstance(new_data, MutableSequence):
                    new_data.append(new_elem)
                elif isinstance(new_data, MutableSet):
                    new_data.add(new_elem)
                else:
                    raise TypeError('Unknown container type encountered when removing private values from keys')

    return new_value


def remove_values(value, no_log_strings):
    """Remove strings in ``no_log_strings`` from value.

    If value is a container type, then remove a lot more.

    Use of ``deferred_removals`` exists, rather than a pure recursive solution,
    because of the potential to hit the maximum recursion depth when dealing with
    large amounts of data (see `issue #24560 <https://github.com/ansible/ansible/issues/24560>`_).
    """

    deferred_removals = deque()

    no_log_strings = [to_native(s, errors='surrogate_or_strict') for s in no_log_strings]
    new_value = _remove_values_conditions(value, no_log_strings, deferred_removals)

    while deferred_removals:
        old_data, new_data = deferred_removals.popleft()
        if isinstance(new_data, Mapping):
            for old_key, old_elem in old_data.items():
                new_elem = _remove_values_conditions(old_elem, no_log_strings, deferred_removals)
                new_data[old_key] = new_elem
        else:
            for elem in old_data:
                new_elem = _remove_values_conditions(elem, no_log_strings, deferred_removals)
                if isinstance(new_data, MutableSequence):
                    new_data.append(new_elem)
                elif isinstance(new_data, MutableSet):
                    new_data.add(new_elem)
                else:
                    raise TypeError('Unknown container type encountered when removing private values from output')

    return new_value
