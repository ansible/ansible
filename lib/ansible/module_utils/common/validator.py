# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.common._collections_compat import (
    Sequence,
)

from ansible.module_utils.common.parameters import (
    get_unsupported_parameters,
    validate_argument_types,  # Rename this because it actually does coercion?
    validate_argument_values,
)

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.validation import (
    check_required_arguments,
)

from ansible.module_utils.six import string_types


class Validator():
    """Argument spec validator class"""

    def __init__(self):
        self._options_context = None

        self._error_messages = []
        self._validated_parameters = {}

    @property
    def error_messages(self):
        return self._error_messages

    @property
    def validated_parameters(self):
        return self._validated_parameters

    def add_error(self, error):
        if isinstance(error, string_types):
            self._error_messages.append(error)
        elif isinstance(error, Sequence):
            self._error_messages.extend(error)
        else:
            raise ValueError('Error messages must be a string or sequence not a %s' % type(error))

    def validate_role(self, argument_spec, parameters):
        """Validate module parameters against argument spec.

        :Example:

        [good example goes here]

        :param argument_spec: Specification of parameters, type, and valid values
        :type argument_spec: dict

        :param parameters: Parameters provided to the role
        :type parameters: dict

        :returns: Validated spec (is there some transformation done? aliases, etc.?)
        :rtype: list

        :raises TypeError: When validation fails.
        :raises ValueError: When parameter choices do not match spec choices
        """

        unsupported_parameters = get_unsupported_parameters(argument_spec, parameters)
        if unsupported_parameters:
            self.add_error('Unsupported parameters: %s' % ', '.join(sorted(list(unsupported_parameters))))

        try:
            check_required_arguments(argument_spec, parameters)
        except TypeError as e:
            self.add_error(to_native(e))

        self._validated_parameters, errors = validate_argument_types(argument_spec, parameters)
        self.add_error(errors)

        errors = validate_argument_values(argument_spec, parameters)
        self.add_error(errors)


    def validate_module(self, arg_spec, parameters):
        """Future method that can be used to module arg spec validation"""
        pass
