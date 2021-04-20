# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from copy import deepcopy

from ansible.module_utils.common.parameters import (
    _ADDITIONAL_CHECKS,
    _get_legal_inputs,
    _get_unsupported_parameters,
    _handle_aliases,
    _list_no_log_values,
    _set_defaults,
    _validate_argument_types,
    _validate_argument_values,
    _validate_sub_spec,
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

    This is the object returned by :func:`ArgumentSpecValidator.validate()
    <ansible.module_utils.common.arg_spec.ArgumentSpecValidator.validate()>`
    containing the validated parameters and any errors.
    """

    def __init__(self, parameters):
        """
        :arg parameters: Terms to be validated and coerced to the correct type.
        :type parameters: dict
        """
        self._no_log_values = set()
        """:class:`set` of values marked as ``no_log`` in the argument spec. This
        is a temporary holding place for these values and may move in the future.
        """

        self._unsupported_parameters = set()
        self._validated_parameters = deepcopy(parameters)
        self._deprecations = []
        self._warnings = []
        self.errors = AnsibleValidationErrorMultiple()
        """
        :class:`~ansible.module_utils.errors.AnsibleValidationErrorMultiple` containing all
        :class:`~ansible.module_utils.errors.AnsibleValidationError` objects if there were
        any failures during validation.
        """

    @property
    def validated_parameters(self):
        """Validated and coerced parameters."""
        return self._validated_parameters

    @property
    def unsupported_parameters(self):
        """:class:`set` of unsupported parameter names."""
        return self._unsupported_parameters

    @property
    def error_messages(self):
        """:class:`list` of all error messages from each exception in :attr:`errors`."""
        return self.errors.messages


class ArgumentSpecValidator:
    """Argument spec validation class

    Creates a validator based on the ``argument_spec`` that can be used to
    validate a number of parameters using the :meth:`validate` method.
    """

    def __init__(self, argument_spec,
                 mutually_exclusive=None,
                 required_together=None,
                 required_one_of=None,
                 required_if=None,
                 required_by=None,
                 ):

        """
        :arg argument_spec: Specification of valid parameters and their type. May
            include nested argument specs.
        :type argument_spec: dict[str, dict]

        :kwarg mutually_exclusive: List or list of lists of terms that should not
            be provided together.
        :type mutually_exclusive: list[str] or list[list[str]]

        :kwarg required_together: List of lists of terms that are required together.
        :type required_together: list[list[str]]

        :kwarg required_one_of: List of lists of terms, one of which in each list
            is required.
        :type required_one_of: list[list[str]]

        :kwarg required_if: List of lists of ``[parameter, value, [parameters]]`` where
            one of ``[parameters]`` is required if ``parameter == value``.
        :type required_if: list

        :kwarg required_by: Dictionary of parameter names that contain a list of
            parameters required by each key in the dictionary.
        :type required_by: dict[str, list[str]]
        """

        self._mutually_exclusive = mutually_exclusive
        self._required_together = required_together
        self._required_one_of = required_one_of
        self._required_if = required_if
        self._required_by = required_by
        self._valid_parameter_names = set()
        self.argument_spec = argument_spec

        for key in sorted(self.argument_spec.keys()):
            aliases = self.argument_spec[key].get('aliases')
            if aliases:
                self._valid_parameter_names.update(["{key} ({aliases})".format(key=key, aliases=", ".join(sorted(aliases)))])
            else:
                self._valid_parameter_names.update([key])

    def validate(self, parameters, *args, **kwargs):
        """Validate ``parameters`` against argument spec.

        Error messages in the :class:`ValidationResult` may contain no_log values and should be
        sanitized with :func:`~ansible.module_utils.common.parameters.sanitize_keys` before logging or displaying.

        :arg parameters: Parameters to validate against the argument spec
        :type parameters: dict[str, dict]

        :return: :class:`ValidationResult` containing validated parameters.

        :Simple Example:

            .. code-block:: text

                argument_spec = {
                    'name': {'type': 'str'},
                    'age': {'type': 'int'},
                }

                parameters = {
                    'name': 'bo',
                    'age': '42',
                }

                validator = ArgumentSpecValidator(argument_spec)
                result = validator.validate(parameters)

                if result.error_messages:
                    sys.exit("Validation failed: {0}".format(", ".join(result.error_messages))

                valid_params = result.validated_parameters
        """

        result = ValidationResult(parameters)

        result._no_log_values.update(set_fallbacks(self.argument_spec, result._validated_parameters))

        alias_warnings = []
        alias_deprecations = []
        try:
            aliases = _handle_aliases(self.argument_spec, result._validated_parameters, alias_warnings, alias_deprecations)
        except (TypeError, ValueError) as e:
            aliases = {}
            result.errors.append(AliasError(to_native(e)))

        legal_inputs = _get_legal_inputs(self.argument_spec, result._validated_parameters, aliases)

        for option, alias in alias_warnings:
            result._warnings.append({'option': option, 'alias': alias})

        for deprecation in alias_deprecations:
            result._deprecations.append({
                'name': deprecation['name'],
                'version': deprecation.get('version'),
                'date': deprecation.get('date'),
                'collection_name': deprecation.get('collection_name'),
            })

        try:
            result._no_log_values.update(_list_no_log_values(self.argument_spec, result._validated_parameters))
        except TypeError as te:
            result.errors.append(NoLogError(to_native(te)))

        try:
            result._unsupported_parameters.update(_get_unsupported_parameters(self.argument_spec, result._validated_parameters, legal_inputs))
        except TypeError as te:
            result.errors.append(RequiredDefaultError(to_native(te)))
        except ValueError as ve:
            result.errors.append(AliasError(to_native(ve)))

        try:
            check_mutually_exclusive(self._mutually_exclusive, result._validated_parameters)
        except TypeError as te:
            result.errors.append(MutuallyExclusiveError(to_native(te)))

        result._no_log_values.update(_set_defaults(self.argument_spec, result._validated_parameters, False))

        try:
            check_required_arguments(self.argument_spec, result._validated_parameters)
        except TypeError as e:
            result.errors.append(RequiredError(to_native(e)))

        _validate_argument_types(self.argument_spec, result._validated_parameters, errors=result.errors)
        _validate_argument_values(self.argument_spec, result._validated_parameters, errors=result.errors)

        for check in _ADDITIONAL_CHECKS:
            try:
                check['func'](getattr(self, "_{attr}".format(attr=check['attr'])), result._validated_parameters)
            except TypeError as te:
                result.errors.append(check['err'](to_native(te)))

        result._no_log_values.update(_set_defaults(self.argument_spec, result._validated_parameters))

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
            supported_string = ", ".join(self._valid_parameter_names)
            result.errors.append(
                UnsupportedError("{0}. Supported parameters include: {1}.".format(unsupported_string, supported_string)))

        return result


class ModuleArgumentSpecValidator(ArgumentSpecValidator):
    """Argument spec validation class used by :class:`AnsibleModule`.

    This is not meant to be used outside of :class:`AnsibleModule`. Use
    :class:`ArgumentSpecValidator` instead.
    """

    def __init__(self, *args, **kwargs):
        super(ModuleArgumentSpecValidator, self).__init__(*args, **kwargs)

    def validate(self, parameters):
        result = super(ModuleArgumentSpecValidator, self).validate(parameters)

        for d in result._deprecations:
            deprecate("Alias '{name}' is deprecated. See the module docs for more information".format(name=d['name']),
                      version=d.get('version'), date=d.get('date'),
                      collection_name=d.get('collection_name'))

        for w in result._warnings:
            warn('Both option {option} and its alias {alias} are set.'.format(option=w['option'], alias=w['alias']))

        return result
