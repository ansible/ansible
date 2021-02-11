# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from copy import deepcopy

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
    validate_argument_types,
    validate_argument_values,
    validate_sub_spec,
)

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.warnings import warn
from ansible.module_utils.common.validation import (
    check_required_arguments,
)

from ansible.module_utils.six import string_types


class ArgumentSpecValidator():
    """Argument spec validation class"""

    def __init__(self, argument_spec, parameters):
        self._error_messages = []
        self._no_log_values = set()
        self.argument_spec = argument_spec
        # Make a copy of the original parameters to avoid changing them
        self._validated_parameters = deepcopy(parameters)
        self._unsupported_parameters = set()

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

    def validate(self, *args, **kwargs):
        """Validate module parameters against argument spec.

        :Example:

        validator = ArgumentSpecValidator(argument_spec, parameters)
        passeded = validator.validate()

        :param argument_spec: Specification of parameters, type, and valid values
        :type argument_spec: dict

        :param parameters: Parameters provided to the role
        :type parameters: dict

        :returns: True if no errors were encountered, False if any errors were encountered.
        :rtype: bool
        """

        self._no_log_values.update(set_fallbacks(self.argument_spec, self._validated_parameters))

        alias_warnings = []
        try:
            alias_results, legal_inputs = handle_aliases(self.argument_spec, self._validated_parameters, alias_warnings)
        except (TypeError, ValueError) as e:
            alias_results = {}
            legal_inputs = None
            self._add_error(to_native(e))

        for option, alias in alias_warnings:
            warn('Both option %s and its alias %s are set.' % (option, alias))

        self._no_log_values.update(list_no_log_values(self.argument_spec, self._validated_parameters))

        if legal_inputs is None:
            legal_inputs = list(alias_results.keys()) + list(self.argument_spec.keys())
        self._unsupported_parameters.update(get_unsupported_parameters(self.argument_spec, self._validated_parameters, legal_inputs))

        try:
            check_required_arguments(self.argument_spec, self._validated_parameters)
        except TypeError as e:
            self._add_error(to_native(e))

        # Just get no_log values without setting defaults. This adds the default values
        # to the values we have set to no_log. This seems odd.
        self._no_log_values.update(set_defaults(self.argument_spec, self._validated_parameters, False))

        validate_argument_types(self.argument_spec, self._validated_parameters, errors=self._error_messages)
        validate_argument_values(self.argument_spec, self._validated_parameters, errors=self._error_messages)

        # Actually set default values
        self._no_log_values.update(set_defaults(self.argument_spec, self._validated_parameters))

        validate_sub_spec(self.argument_spec, self._validated_parameters,
                          errors=self._error_messages,
                          no_log_values=self._no_log_values,
                          unsupported_parameters=self._unsupported_parameters)

        if self._unsupported_parameters:
            self._add_error('Unsupported parameters: %s' % ', '.join(sorted(list(self._unsupported_parameters))))

        self._sanitize_error_messages()

        if self.error_messages:
            return False
        else:
            return True
