# -*- coding: utf-8 -*-
# Copyright (c) 2018 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.collections import is_iterable
from ansible.module_utils.six import string_types


def count_terms(terms, module_parameters):
    """Count the number of occurrences of a key in a given dictionary

    :arg terms: String or iterable of values to check
    :arg module_parameters: Dictionary of module parameters

    :returns: An integer that is the number of occurrences of the terms values
        in the provided dictionary.
    """

    if not is_iterable(terms):
        terms = [terms]

    return len(set(terms).intersection(module_parameters))


def check_mutually_exclusive(terms, module_parameters):
    """Check mutually exclusive terms against argument parameters. Accepts
    a single list or list of lists that are groups of terms that should be
    mutually exclusive with one another

    :arg terms: List of mutually exclusive module parameters
    :arg module_parameters: Dictionary of module parameters

    :returns: A list of terms that are mutually exclusive.
    """

    result = []
    if terms is None:
        return result

    for check in terms:
        count = count_terms(check, module_parameters)
        if count > 1:
            result.append(check)

    return result


def check_required_one_of(terms, module_parameters):
    """Check each list of terms to ensure at least one exists in the given module
    parameters. Accepts a list of lists or tuples.

    :arg terms: List of lists of terms to check. For each list of terms, at
        least is required.
    :arg module_parameters: Dictionary of module parameters

    :returns: list of terms that should be present in module parameters but
              are missing
    """

    result = []
    for term in terms:

        count = count_terms(term, module_parameters)
        if count == 0:
            result.append(term)

    return result


def check_required_together(terms, module_parameters):
    """Check each list of terms to ensure every parameter in each list exists
    in the given module parameters. Accepts a list of lists or tuples.

    :arg terms: List of lists of terms to check. Each list should include
        parameters that are all required when at least one is specified
        in the module_parameters.
    :arg module_parameters: Dictionary of module parameters

    :returns: List of lists of terms that exist in module_parametcs but are
        missing other required terms.
    """

    result = []
    if terms is None:
        return result

    for term in terms:
        counts = [count_terms(field, module_parameters) for field in term]
        non_zero = [c for c in counts if c > 0]
        if len(non_zero) > 0:
            if 0 in counts:
                result.append(term)

    return result


def check_required_by(requirements, module_parameters):
    """For each key in requirements, check the corresponding list to see if they
    exist in module_parameters. Accepts a single string or list of values for
    each key.

    :arg requirements: Dictionary of requirements
    :arg module_parameters: Dictionary of module parameters

    :returns: Dictionary of required terms with a list of missing terms for
        each key
    """

    result = {}
    if requirements is None:
        return result

    for (key, value) in requirements.items():
        if key not in module_parameters or module_parameters[key] is None:
            continue
        result[key] = []
        # Support strings (single-item lists)
        if isinstance(value, string_types):
            value = [value]
        for required in value:
            if required not in module_parameters or module_parameters[required] is None:
                result[key].append(required)

    return result


def check_required_arguments(argument_spec, module_parameters):
    """Check all paramaters in argument_spec and return a list of parameters
    that are required by not present in module_parameters.

    :arg argument_spec: Argument spec dicitionary containing all parameters
        and their specification
    :arg module_paramaters: Dictionary of module parameters

    :returns: List of parameters that are required but missing.

    """

    missing = []
    for (k, v) in argument_spec.items():
        required = v.get('required', False)
        if required and k not in module_parameters:
            missing.append(k)

    return missing


def check_required_if(requirements, module_parameters):
    """Check parameters that are conditionally required.

    :arg requirements: List of lists specifying a parameter, value, parameters
        required when the given parameter is the specified value, and optionally
        a boolean indicating any or all parameters are required.

        Example:
            required_if=[
                ['state', 'present', ('path',), True],
                ['someint', 99, ('bool_param', 'string_param')],
            ]

    :arg module_paramaters: Dictionary of module parameters

    :returns: List of dictionaries. Each dictionary is the result of evaluting
        each item in requirements. Each return dictionary contains the following
        keys:

            :key missing: List of parameters that are required but missing
            :key requires: 'any' or 'all'
            :key paramater: Parameter name that has the requirement
            :key value: Original value of the paramater
            :key requirements: Original required parameters

        Example:
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
    result = []
    if requirements is None:
        return result

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

        if key in module_parameters and module_parameters[key] == val:
            for check in requirements:
                count = count_terms(check, module_parameters)
                if count == 0:
                    missing['missing'].append(check)
        if len(missing['missing']) and len(missing['missing']) >= max_missing_count:
            missing['parameter'] = key
            missing['value'] = val
            missing['requirements'] = requirements
            result.append(missing)

    return result
