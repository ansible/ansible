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
    handle_aliases,
    list_no_log_values,
    remove_values,
    set_defaults,
    set_fallbacks,
    validate_argument_types,  # Rename this because it actually does coercion?
    validate_argument_values,
    validate_sub_spec,
)

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.warnings import warn
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
        self._no_log_values = set()

    @property
    def error_messages(self):
        return self._error_messages

    @property
    def validated_parameters(self):
        return self._validated_parameters

    def _add_error(self, error):
        if isinstance(error, string_types):
            self._error_messages.append(error)
        elif isinstance(error, Sequence):
            self._error_messages.extend(error)
        else:
            raise ValueError('Error messages must be a string or sequence not a %s' % type(error))

    def _sanitize_error_messages(self):
        self._error_messages = remove_values(self._error_messages, self._no_log_values)

    def validate(self, argument_spec, parameters):
        """Validate module parameters against argument spec.

        :Example:

        [good example goes here]

        :param argument_spec: Specification of parameters, type, and valid values
        :type argument_spec: dict

        :param parameters: Parameters provided to the role
        :type parameters: dict

        :returns: True if no errors were encountered, False if any errors were encountered.
        :rtype: bool
        """

        self._no_log_values.update(set_fallbacks(argument_spec, parameters))

        alias_warnings = []
        try:
            alias_results, legal_inputs = handle_aliases(argument_spec, parameters, alias_warnings=alias_warnings)
        except (TypeError, ValueError) as e:
            alias_results = {}
            legal_inputs = None
            self._add_error(to_native(e))

        for option, alias in alias_warnings:
            warn('Both option %s and its alias %s are set.' % (option, alias))

        self._no_log_values.update(list_no_log_values(argument_spec, parameters))

        if legal_inputs is None:
            legal_inputs = list(alias_results.keys()) + list(argument_spec.keys())
        unsupported_parameters = get_unsupported_parameters(argument_spec, parameters, legal_inputs)

        try:
            check_required_arguments(argument_spec, parameters)
        except TypeError as e:
            self._add_error(to_native(e))

        self._no_log_values.update(set_defaults(argument_spec, parameters, False))

        self._validated_parameters, errors = validate_argument_types(argument_spec, parameters)
        self._add_error(errors)

        errors = validate_argument_values(argument_spec, parameters)
        self._add_error(errors)

        # Sub Spec
        # _validated_parameters, errors, _unsupported = validate_sub_spec(argument_spec, self._validated_parameters)
        # self._validated_parameters.update(_validated_parameters)
        # self._add_error(errors)
        # unsupported_parameters.extend(_unsupported)
        # if unsupported_parameters:
        #     self._add_error('Unsupported parameters %s' % ', '.join((p for p in unsupported_parameters)))

        if unsupported_parameters:
            self._add_error('Unsupported parameters: %s' % ', '.join(sorted(list(unsupported_parameters))))

        self._sanitize_error_messages()

        if self.error_messages:
            return False
        else:
            return True
