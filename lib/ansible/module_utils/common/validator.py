# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from ansible.module_utils.common.parameters import (
    get_unsupported_parameters,
    validate_argument_types,  # Rename this because it actually does coercion?
    validate_argument_values,
)

from ansible.module_utils.common.text.converters import to_native


from ansible.module_utils.common.validation import (
    check_required_arguments,
)


class Validator():
    """Argument spec validator class"""

    def __init__(self, arg_spec, module_params):
        self._options_context = None

        self.arg_spec = arg_spec
        self.module_params = module_params
        self.error_messages = []
        self.validated_params = {}

    def validate(self):
        """Validate module parameters against argument spec.

        :Example:

        validator = Validator(argument_spec, module parameters)
        validated_params = validator.validate()

        :param arg_spec: Specification of parameters, type, and valid values
        :type arg_spec: dict

        :param module_params: Parameters provided to the module
        :type module_params: dict

        :returns: Validated spec (is there some transformation done? aliases, etc.?)
        :rtype: list

        :raises TypeError: When validation fails.
        :raises ValueError: When parameter choices do not match spec choices
        """

        unsupported_parameters = get_unsupported_parameters(self.arg_spec, self.module_params)
        if unsupported_parameters:
            self.error_messages.append('Unsupported parameters: %s' % ', '.join(sorted(list(unsupported_parameters))))

        try:
            check_required_arguments(self.arg_spec, self.module_params)
        except TypeError as e:
            self.error_messages.append(to_native(e))

        result = validate_argument_types(self.arg_spec, self.module_params)
        self.validated_params = result['validated_params']

        self.error_messages.append([to_native(e) for e in result['errors']])
        self.error_messages.append(validate_argument_values(self.arg_spec, self.module_params))

        return {
            'error_messages': self.error_messages,
            'validated': self.validated_params,
        }
