# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os
import re

from ast import literal_eval
from ansible.module_utils._text import to_native
from ansible.module_utils.common._json_compat import json
from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.common.text.converters import jsonify
from ansible.module_utils.common.text.formatters import human_to_bytes
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.module_utils.six import (
    binary_type,
    integer_types,
    string_types,
    text_type,
)


def count_terms(terms, parameters):
    """Count the number of occurrences of a key in a given dictionary

    :arg terms: String or iterable of values to check
    :arg parameters: Dictionary of parameters

    :returns: An integer that is the number of occurrences of the terms values
        in the provided dictionary.
    """

    if not is_iterable(terms):
        terms = [terms]

    return len(set(terms).intersection(parameters))


def safe_eval(value, locals=None, include_exceptions=False):
    # do not allow method calls to modules
    if not isinstance(value, string_types):
        # already templated to a datavaluestructure, perhaps?
        if include_exceptions:
            return (value, None)
        return value
    if re.search(r'\w\.\w+\(', value):
        if include_exceptions:
            return (value, None)
        return value
    # do not allow imports
    if re.search(r'import \w+', value):
        if include_exceptions:
            return (value, None)
        return value
    try:
        result = literal_eval(value)
        if include_exceptions:
            return (result, None)
        else:
            return result
    except Exception as e:
        if include_exceptions:
            return (value, e)
        return value


def check_mutually_exclusive(terms, parameters, options_context=None):
    """Check mutually exclusive terms against argument parameters

    Accepts a single list or list of lists that are groups of terms that should be
    mutually exclusive with one another

    :arg terms: List of mutually exclusive parameters
    :arg parameters: Dictionary of parameters

    :returns: Empty list or raises :class:`TypeError` if the check fails.
    """

    results = []
    if terms is None:
        return results

    for check in terms:
        count = count_terms(check, parameters)
        if count > 1:
            results.append(check)

    if results:
        full_list = ['|'.join(check) for check in results]
        msg = "parameters are mutually exclusive: %s" % ', '.join(full_list)
        if options_context:
            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
        raise TypeError(to_native(msg))

    return results


def check_required_one_of(terms, parameters, options_context=None):
    """Check each list of terms to ensure at least one exists in the given module
    parameters

    Accepts a list of lists or tuples

    :arg terms: List of lists of terms to check. For each list of terms, at
        least one is required.
    :arg parameters: Dictionary of parameters
    :kwarg options_context: List of strings of parent key names if ``terms`` are
        in a sub spec.

    :returns: Empty list or raises :class:`TypeError` if the check fails.
    """

    results = []
    if terms is None:
        return results

    for term in terms:
        count = count_terms(term, parameters)
        if count == 0:
            results.append(term)

    if results:
        for term in results:
            msg = "one of the following is required: %s" % ', '.join(term)
            if options_context:
                msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
            raise TypeError(to_native(msg))

    return results


def check_required_together(terms, parameters, options_context=None):
    """Check each list of terms to ensure every parameter in each list exists
    in the given parameters.

    Accepts a list of lists or tuples.

    :arg terms: List of lists of terms to check. Each list should include
        parameters that are all required when at least one is specified
        in the parameters.
    :arg parameters: Dictionary of parameters

    :returns: Empty list or raises :class:`TypeError` if the check fails.
    """

    results = []
    if terms is None:
        return results

    for term in terms:
        counts = [count_terms(field, parameters) for field in term]
        non_zero = [c for c in counts if c > 0]
        if len(non_zero) > 0:
            if 0 in counts:
                results.append(term)
    if results:
        for term in results:
            msg = "parameters are required together: %s" % ', '.join(term)
            if options_context:
                msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
            raise TypeError(to_native(msg))

    return results


def check_required_by(requirements, parameters, options_context=None):
    """For each key in requirements, check the corresponding list to see if they
    exist in parameters.

    Accepts a single string or list of values for each key.

    :arg requirements: Dictionary of requirements
    :arg parameters: Dictionary of parameters

    :returns: Empty dictionary or raises :class:`TypeError` if the
    """

    result = {}
    if requirements is None:
        return result

    for (key, value) in requirements.items():
        if key not in parameters or parameters[key] is None:
            continue
        result[key] = []
        # Support strings (single-item lists)
        if isinstance(value, string_types):
            value = [value]
        for required in value:
            if required not in parameters or parameters[required] is None:
                result[key].append(required)

    if result:
        for key, missing in result.items():
            if len(missing) > 0:
                msg = "missing parameter(s) required by '%s': %s" % (key, ', '.join(missing))
                if options_context:
                    msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
                raise TypeError(to_native(msg))

    return result


def check_required_arguments(argument_spec, parameters, options_context=None):
    """Check all parameters in argument_spec and return a list of parameters
    that are required but not present in parameters.

    Raises :class:`TypeError` if the check fails

    :arg argument_spec: Argument spec dictionary containing all parameters
        and their specification
    :arg parameters: Dictionary of parameters

    :returns: Empty list or raises :class:`TypeError` if the check fails.
    """

    missing = []
    if argument_spec is None:
        return missing

    for (k, v) in argument_spec.items():
        required = v.get('required', False)
        if required and k not in parameters:
            missing.append(k)

    if missing:
        msg = "missing required arguments: %s" % ", ".join(sorted(missing))
        if options_context:
            msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
        raise TypeError(to_native(msg))

    return missing


def check_required_if(requirements, parameters, options_context=None):
    """Check parameters that are conditionally required

    Raises :class:`TypeError` if the check fails

    :arg requirements: List of lists specifying a parameter, value, parameters
        required when the given parameter is the specified value, and optionally
        a boolean indicating any or all parameters are required.

    :Example:

    .. code-block:: python

        required_if=[
            ['state', 'present', ('path',), True],
            ['someint', 99, ('bool_param', 'string_param')],
        ]

    :arg parameters: Dictionary of parameters

    :returns: Empty list or raises :class:`TypeError` if the check fails.
        The results attribute of the exception contains a list of dictionaries.
        Each dictionary is the result of evaluating each item in requirements.
        Each return dictionary contains the following keys:

            :key missing: List of parameters that are required but missing
            :key requires: 'any' or 'all'
            :key parameter: Parameter name that has the requirement
            :key value: Original value of the parameter
            :key requirements: Original required parameters

        :Example:

        .. code-block:: python

            [
                {
                    'parameter': 'someint',
                    'value': 99
                    'requirements': ('bool_param', 'string_param'),
                    'missing': ['string_param'],
                    'requires': 'all',
                }
            ]

    """
    results = []
    if requirements is None:
        return results

    for req in requirements:
        missing = {}
        missing['missing'] = []
        max_missing_count = 0
        is_one_of = False
        if len(req) == 4:
            key, val, requirements, is_one_of = req
        else:
            key, val, requirements = req

        # is_one_of is True at least one requirement should be
        # present, else all requirements should be present.
        if is_one_of:
            max_missing_count = len(requirements)
            missing['requires'] = 'any'
        else:
            missing['requires'] = 'all'

        if key in parameters and parameters[key] == val:
            for check in requirements:
                count = count_terms(check, parameters)
                if count == 0:
                    missing['missing'].append(check)
        if len(missing['missing']) and len(missing['missing']) >= max_missing_count:
            missing['parameter'] = key
            missing['value'] = val
            missing['requirements'] = requirements
            results.append(missing)

    if results:
        for missing in results:
            msg = "%s is %s but %s of the following are missing: %s" % (
                missing['parameter'], missing['value'], missing['requires'], ', '.join(missing['missing']))
            if options_context:
                msg = "{0} found in {1}".format(msg, " -> ".join(options_context))
            raise TypeError(to_native(msg))

    return results


def check_missing_parameters(parameters, required_parameters=None):
    """This is for checking for required params when we can not check via
    argspec because we need more information than is simply given in the argspec.

    Raises :class:`TypeError` if any required parameters are missing

    :arg parameters: Dictionary of parameters
    :arg required_parameters: List of parameters to look for in the given parameters.

    :returns: Empty list or raises :class:`TypeError` if the check fails.
    """
    missing_params = []
    if required_parameters is None:
        return missing_params

    for param in required_parameters:
        if not parameters.get(param):
            missing_params.append(param)

    if missing_params:
        msg = "missing required arguments: %s" % ', '.join(missing_params)
        raise TypeError(to_native(msg))

    return missing_params


# FIXME: The param and prefix parameters here are coming from AnsibleModule._check_type_string()
#        which is using those for the warning messaged based on string conversion warning settings.
#        Not sure how to deal with that here since we don't have config state to query.
def check_type_str(value, allow_conversion=True, param=None, prefix=''):
    """Verify that the value is a string or convert to a string.

    Since unexpected changes can sometimes happen when converting to a string,
    ``allow_conversion`` controls whether or not the value will be converted or a
    TypeError will be raised if the value is not a string and would be converted

    :arg value: Value to validate or convert to a string
    :arg allow_conversion: Whether to convert the string and return it or raise
        a TypeError

    :returns: Original value if it is a string, the value converted to a string
        if allow_conversion=True, or raises a TypeError if allow_conversion=False.
    """
    if isinstance(value, string_types):
        return value

    if allow_conversion:
        return to_native(value, errors='surrogate_or_strict')

    msg = "'{0!r}' is not a string and conversion is not allowed".format(value)
    raise TypeError(to_native(msg))


def check_type_list(value):
    """Verify that the value is a list or convert to a list

    A comma separated string will be split into a list. Raises a :class:`TypeError`
    if unable to convert to a list.

    :arg value: Value to validate or convert to a list

    :returns: Original value if it is already a list, single item list if a
        float, int, or string without commas, or a multi-item list if a
        comma-delimited string.
    """
    if isinstance(value, list):
        return value

    if isinstance(value, string_types):
        return value.split(",")
    elif isinstance(value, int) or isinstance(value, float):
        return [str(value)]

    raise TypeError('%s cannot be converted to a list' % type(value))


def check_type_dict(value):
    """Verify that value is a dict or convert it to a dict and return it.

    Raises :class:`TypeError` if unable to convert to a dict

    :arg value: Dict or string to convert to a dict. Accepts ``k1=v2, k2=v2``.

    :returns: value converted to a dictionary
    """
    if isinstance(value, dict):
        return value

    if isinstance(value, string_types):
        if value.startswith("{"):
            try:
                return json.loads(value)
            except Exception:
                (result, exc) = safe_eval(value, dict(), include_exceptions=True)
                if exc is not None:
                    raise TypeError('unable to evaluate string as dictionary')
                return result
        elif '=' in value:
            fields = []
            field_buffer = []
            in_quote = False
            in_escape = False
            for c in value.strip():
                if in_escape:
                    field_buffer.append(c)
                    in_escape = False
                elif c == '\\':
                    in_escape = True
                elif not in_quote and c in ('\'', '"'):
                    in_quote = c
                elif in_quote and in_quote == c:
                    in_quote = False
                elif not in_quote and c in (',', ' '):
                    field = ''.join(field_buffer)
                    if field:
                        fields.append(field)
                    field_buffer = []
                else:
                    field_buffer.append(c)

            field = ''.join(field_buffer)
            if field:
                fields.append(field)
            return dict(x.split("=", 1) for x in fields)
        else:
            raise TypeError("dictionary requested, could not parse JSON or key=value")

    raise TypeError('%s cannot be converted to a dict' % type(value))


def check_type_bool(value):
    """Verify that the value is a bool or convert it to a bool and return it.

    Raises :class:`TypeError` if unable to convert to a bool

    :arg value: String, int, or float to convert to bool. Valid booleans include:
         '1', 'on', 1, '0', 0, 'n', 'f', 'false', 'true', 'y', 't', 'yes', 'no', 'off'

    :returns: Boolean True or False
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, string_types) or isinstance(value, (int, float)):
        return boolean(value)

    raise TypeError('%s cannot be converted to a bool' % type(value))


def check_type_int(value):
    """Verify that the value is an integer and return it or convert the value
    to an integer and return it

    Raises :class:`TypeError` if unable to convert to an int

    :arg value: String or int to convert of verify

    :return: int of given value
    """
    if isinstance(value, integer_types):
        return value

    if isinstance(value, string_types):
        try:
            return int(value)
        except ValueError:
            pass

    raise TypeError('%s cannot be converted to an int' % type(value))


def check_type_float(value):
    """Verify that value is a float or convert it to a float and return it

    Raises :class:`TypeError` if unable to convert to a float

    :arg value: float, int, str, or bytes to verify or convert and return.

    :returns: float of given value.
    """
    if isinstance(value, float):
        return value

    if isinstance(value, (binary_type, text_type, int)):
        try:
            return float(value)
        except ValueError:
            pass

    raise TypeError('%s cannot be converted to a float' % type(value))


def check_type_path(value,):
    """Verify the provided value is a string or convert it to a string,
    then return the expanded path
    """
    value = check_type_str(value)
    return os.path.expanduser(os.path.expandvars(value))


def check_type_raw(value):
    """Returns the raw value"""
    return value


def check_type_bytes(value):
    """Convert a human-readable string value to bytes

    Raises :class:`TypeError` if unable to covert the value
    """
    try:
        return human_to_bytes(value)
    except ValueError:
        raise TypeError('%s cannot be converted to a Byte value' % type(value))


def check_type_bits(value):
    """Convert a human-readable string bits value to bits in integer.

    Example: ``check_type_bits('1Mb')`` returns integer 1048576.

    Raises :class:`TypeError` if unable to covert the value.
    """
    try:
        return human_to_bytes(value, isbits=True)
    except ValueError:
        raise TypeError('%s cannot be converted to a Bit value' % type(value))


def check_type_jsonarg(value):
    """Return a jsonified string. Sometimes the controller turns a json string
    into a dict/list so transform it back into json here

    Raises :class:`TypeError` if unable to covert the value

    """
    if isinstance(value, (text_type, binary_type)):
        return value.strip()
    elif isinstance(value, (list, tuple, dict)):
        return jsonify(value)
    raise TypeError('%s cannot be converted to a json string' % type(value))
