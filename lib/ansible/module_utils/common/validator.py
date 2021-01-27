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

    def __init__(self):
        self._options_context = None

        self.argument_spec = {}
        self.module_parameters = {}
        self.error_messages = []
        self.validated_parameters = {}

    def validate(self, arg_spec, module_parameters):
        """Validate module parameters against argument spec.

        :Example:

        validator = Validator()
        validator.validate()
        validated_parameters = validator.validated_parameters
        errors = validator.error_messages

        :param arg_spec: Specification of parameters, type, and valid values
        :type arg_spec: dict

        :param module_parameters: Parameters provided to the module
        :type module_parameters: dict

        :returns: Validated spec (is there some transformation done? aliases, etc.?)
        :rtype: list

        :raises TypeError: When validation fails.
        :raises ValueError: When parameter choices do not match spec choices
        """

        self.argument_spec = arg_spec
        self.module_parameters = module_parameters

        unsupported_parameters = get_unsupported_parameters(self.argument_spec, self.module_parameters)
        if unsupported_parameters:
            self.error_messages.append('Unsupported parameters: %s' % ', '.join(sorted(list(unsupported_parameters))))

        try:
            check_required_arguments(self.argument_spec, self.module_parameters)
        except TypeError as e:
            self.error_messages.append(to_native(e))

        self.validated_parameters, errors = validate_argument_types(self.argument_spec, self.module_parameters)
        self.error_messages.extend(errors)

        errors = validate_argument_values(self.argument_spec, self.module_parameters)
        self.error_messages.extend(errors)

        return self.validated_parameters
