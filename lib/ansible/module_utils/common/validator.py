# -*- coding: utf-8 -*-
# Copyright (c) 2020 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common._collections_compat import (
    KeysView,
    Sequence,
)

from ansible.module_utils.common.parameters import (
    get_unsupported_parameters,
    get_type_validator,
)

from ansible.module_utils.parsing.convert_bool import BOOLEANS_FALSE, BOOLEANS_TRUE
from ansible.module_utils.common.text.converters import to_native

from ansible.module_utils.common.text.formatters import (
    lenient_lowercase,
)

from ansible.module_utils.common.validation import (
    check_required_arguments,
    check_required_by,
    check_required_if,
    check_required_one_of,
    check_required_together,
)

from ansible.module_utils.six import (
    binary_type,
    text_type,
)


class Validator():
    """Argument spec validator class"""

    def __init__(self, arg_spec, module_params):
        self._options_context = None

        self.arg_spec = arg_spec
        self.module_params = module_params
        self.error_messages = []
        self.validated_params = {}

    def _validate_argument_types(self):
        """Validate module parameters and store them in self.validated_params"""

        # TODO: Move to standalone function
        # FIXME: Need to handle subelements

        for k, v in self.arg_spec.items():
            type = v.get('type')
            if k not in self.module_params:
                continue

            value = self.module_params[k]
            if value is None:
                continue

            type_checker, wanted_name = get_type_validator(type)

            self.validated_params[k] = type_checker(value)

    def _validate_argument_values(self):
        """Docs"""

        # TODO: Move to standalone function

        for k, v in self.arg_spec.items():
            choices = v.get('choices')
            if choices is None:
                continue

            if isinstance(choices, (frozenset, KeysView, Sequence)) and not isinstance(choices, (binary_type, text_type)):
                if k in self.module_params:
                    # Allow one or more when type='list' param with choices
                    if isinstance(self.module_params[k], list):
                        diff_list = ", ".join([item for item in self.module_params[k] if item not in choices])
                        if diff_list:
                            choices_str = ", ".join([to_native(c) for c in choices])
                            msg = "value of %s must be one or more of: %s. Got no match for: %s" % (k, choices_str, diff_list)
                            if self._options_context:
                                msg += " found in %s" % " -> ".join(self._options_context)
                            raise ValueError(msg)

                        # PyYaml converts certain strings to bools. If we can unambiguously convert back, do so before checking
                        # the value. If we can't figure this out, module author is responsible.
                        lowered_choices = None
                        if self.module_params[k] == 'False':
                            lowered_choices = lenient_lowercase(choices)
                            overlap = BOOLEANS_FALSE.intersection(choices)
                            if len(overlap) == 1:
                                # Extract from a set
                                (self.module_params[k],) = overlap

                        if self.module_params[k] == 'True':
                            if lowered_choices is None:
                                lowered_choices = lenient_lowercase(choices)
                            overlap = BOOLEANS_TRUE.intersection(choices)
                            if len(overlap) == 1:
                                (self.module_params[k],) = overlap

                        if self.module_params[k] not in choices:
                            choices_str = ", ".join([to_native(c) for c in choices])
                            msg = "value of %s must be one of: %s, got: %s" % (k, choices_str, self.module_params[k])
                            if self._options_context:
                                msg += " found in %s" % " -> ".join(self._options_context)
                            raise ValueError(msg)
            else:
                msg = "internal error: choices for argument %s are not iterable: %s" % (k, choices)
                if self._options_context:
                    msg += " found in %s" % " -> ".join(self._options_context)
                raise ValueError(msg)

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
            self._validate_argument_types()
        except TypeError as te:
            self.error_messages.append(to_native(te))

        try:
            self._validate_argument_values()
        except TypeError as te:
            self.error_messages.append(to_native(te))

        # TODO: Since these need explicit input outside the argument_spec,
        #       how are we handling them?
        #
        # check_required_arguments()
        # check_required_together()
        # check_required_one_of()
        # check_required_if()
        # check_required_by()

        try:
            check_required_arguments(self.arg_spec, self.module_params)
        except TypeError as te:
            self.error_messages.append(to_native(te))

        # try:
        #     check_required_together(required_together, self.module_params)
        # except TypeError as te:
        #     self.error_messages.append(to_native(te))

        return {
            'error_messages': self.error_messages,
            'validated': self.validated_params,
        }
