# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.common.parameters import (
    _validate_argument_types,
    _validate_argument_values,
    _validate_sub_spec,
    get_unsupported_parameters,
    handle_aliases,
    list_no_log_values,
    set_defaults,
    set_fallbacks,
)

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.common.warnings import deprecate, warn

from ansible.module_utils.common.validation import (
    check_mutually_exclusive,
    check_required_arguments,
    check_required_by,
    check_required_if,
    check_required_one_of,
    check_required_together,
)

from ansible.module_utils.errors import (
    AliasError,
    AnsibleValidationErrorMultiple,
    MutuallyExclusiveError,
    NoLogError,
    RequiredByError,
    RequiredDefaultError,
    RequiredError,
    RequiredIfError,
    RequiredOneOfError,
    RequiredTogetherError,
    UnsupportedError,
)


class ValidationResult:
    """Result of argument spec validation.

    :param parameters: Terms to be validated and coerced to the correct type.
    :type parameters: dict

    """

    def __init__(self, parameters):
        self._no_log_values = set()
        self._unsupported_parameters = set()
        self._validated_parameters = deepcopy(parameters)
        self.errors = AnsibleValidationErrorMultiple()

    @property
    def validated_parameters(self):
        return self._validated_parameters

    @property
    def unsupported_parameters(self):
        return self._unsupported_parameters

    @property
    def error_messages(self):
        return self.errors.messages


class ArgumentSpecValidator:
    """Argument spec validation class

    Creates a validator based on the ``argument_spec`` that can be used to
    validate a number of parameters using the ``validate()`` method.

    :param argument_spec: Specification of valid parameters and their type. May
        include nested argument specs.
    :type argument_spec: dict

    :param mutually_exclusive: List or list of lists of terms that should not
        be provided together.
    :type: list, optional

    :param required_together: List of lists of terms that are required together.
    :type: list, optional

    :param required_one_of: List of lists of terms, one of which in each list
        is required.
    :type: list, optional

    :param required_if: List of lists of ``[parameter, value, [parameters]]`` where
        one of [parameters] is required if ``parameter`` == ``value``.
    :type: list, optional

    :param required_by: Dictionary of parameter names that contain a list of
        parameters required by each key in the dictionary.
    :type: dict, optional
    """

    def __init__(self, argument_spec,
                 mutually_exclusive=None,
                 required_together=None,
                 required_one_of=None,
                 required_if=None,
                 required_by=None,
                 ):

        self._valid_parameter_names = set()
        self._mutually_exclusive = mutually_exclusive
        self._required_together = required_together
        self._required_one_of = required_one_of
        self._required_if = required_if
        self._required_by = required_by
        self.argument_spec = argument_spec

    @property
    def valid_parameter_names(self):
        if self._valid_parameter_names:
            return self._validated_parameter_names
        valid_parameter_names = set()
        for key in sorted(self.argument_spec.keys()):
            aliases = self.argument_spec[key].get('aliases')
            if aliases:
                valid_parameter_names.update(["{key} ({aliases})".format(key=key, aliases=", ".join(sorted(aliases)))])
            else:
                valid_parameter_names.update([key])

        self._valid_parameter_names = valid_parameter_names
        return valid_parameter_names

    def validate(self, parameters, *args, **kwargs):
        """Validate module parameters against argument spec. Returns a
        ValidationResult object.

        Error messages in the ValidationResult may contain
        no_log values and should be sanitized before logging or displaying.

        :Example:

        validator = ArgumentSpecValidator(argument_spec)
        result = validator.validate(parameters)

        if result.error_messages:
            sys.exit("Validation failed: {0}".format(", ".join(result.error_messages))

        valid_params = result.validated_parameters

        :param argument_spec: Specification of parameters, type, and valid values
        :type argument_spec: dict

        :param parameters: Parameters provided to the role
        :type parameters: dict

        :return: Object containing validated parameters.
        :rtype: ValidationResult
        """

        result = ValidationResult(parameters)

        result._no_log_values.update(set_fallbacks(self.argument_spec, result._validated_parameters))

        alias_warnings = []
        alias_deprecations = []
        try:
            alias_results, legal_inputs = handle_aliases(self.argument_spec, result._validated_parameters, alias_warnings, alias_deprecations)
        except (TypeError, ValueError) as e:
            alias_results = {}
            legal_inputs = None
            result.errors.append(AliasError(to_native(e)))

        for option, alias in alias_warnings:
            warn('Both option %s and its alias %s are set.' % (option, alias))

        for deprecation in alias_deprecations:
            deprecate("Alias '%s' is deprecated. See the module docs for more information" % deprecation['name'],
                      version=deprecation.get('version'), date=deprecation.get('date'),
                      collection_name=deprecation.get('collection_name'))

        try:
            result._no_log_values.update(list_no_log_values(self.argument_spec, result._validated_parameters))
        except TypeError as te:
            result.errors.append(NoLogError(to_native(te)))

        if legal_inputs is None:
            legal_inputs = list(alias_results.keys()) + list(self.argument_spec.keys())
        try:
            result._unsupported_parameters.update(get_unsupported_parameters(self.argument_spec, result._validated_parameters, legal_inputs))
        except TypeError as te:
            result.errors.append(RequiredDefaultError(to_native(te)))
        except ValueError as ve:
            result.errors.append(AliasError(to_native(ve)))

        try:
            check_mutually_exclusive(self._mutually_exclusive, result._validated_parameters)
        except TypeError as te:
            result.errors.append(MutuallyExclusiveError(to_native(te)))

        result._no_log_values.update(set_defaults(self.argument_spec, result._validated_parameters, False))

        try:
            check_required_arguments(self.argument_spec, result._validated_parameters)
        except TypeError as e:
            result.errors.append(RequiredError(to_native(e)))

        _validate_argument_types(self.argument_spec, result._validated_parameters, errors=result.errors)
        _validate_argument_values(self.argument_spec, result._validated_parameters, errors=result.errors)

        checks = (
            {'func': check_required_together, 'attr': '_required_together', 'err': RequiredTogetherError},
            {'func': check_required_one_of, 'attr': '_required_one_of', 'err': RequiredOneOfError},
            {'func': check_required_if, 'attr': '_required_if', 'err': RequiredIfError},
            {'func': check_required_by, 'attr': '_required_by', 'err': RequiredByError},
        )

        for check in checks:
            if check['attr'] is not None:
                try:
                    check['func'](getattr(self, check['attr']), result._validated_parameters)
                except TypeError as te:
                    result.errors.append(check['err'](to_native(te)))

        result._no_log_values.update(set_defaults(self.argument_spec, result._validated_parameters))

        _validate_sub_spec(self.argument_spec, result._validated_parameters,
                           errors=result.errors,
                           no_log_values=result._no_log_values,
                           unsupported_parameters=result._unsupported_parameters)

        if result._unsupported_parameters:
            flattened_names = []
            for item in result._unsupported_parameters:
                if isinstance(item, tuple):
                    flattened_names.append(".".join(item))
                else:
                    flattened_names.append(item)

            unsupported_string = ", ".join(sorted(list(flattened_names)))
            supported_string = ", ".join(self.valid_parameter_names)
            result.errors.append(
                UnsupportedError("{0}. Supported parameters include: {1}.".format(unsupported_string, supported_string)))

        return result
