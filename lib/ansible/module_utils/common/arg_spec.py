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
    _validate_argument_types,
    _validate_argument_values,
    _validate_sub_spec,
    get_unsupported_parameters,
    handle_aliases,
    list_no_log_values,
    remove_values,
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

from ansible.module_utils.six import string_types


class ArgumentSpecValidator():
    """Argument spec validation class

    This will evaluate the given parameters against a provide argument spec, coerce
    provided arguments to the specified type, and return a boolean for overall
    pass/fail of the validation and coercion. Any errors with the validation are
    stored in the ``error_messages`` property.

    A copy of the original parameters is stored in the ``validated_parameters``
    property. This will be mutated in order to ensure the parameters match
    the specified type. The original parameters and argument_spec are unaltered.

    :param argument_spec: Specification of valid parameters and their type. May
        include nested argument specs.
    :type argument_spec: dict

    :param parameters: Terms to be validated and coerced to the correct type.
    :type parameters: dict

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

    def __init__(self, argument_spec, parameters,
                 mutually_exclusive=None,
                 required_together=None,
                 required_one_of=None,
                 required_if=None,
                 required_by=None,
                 ):

        self._error_messages = []
        self._no_log_values = set()
        self._validated_parameters = deepcopy(parameters)  # Make a copy of the original parameters to avoid changing them
        self._valid_parameter_names = []
        self._unsupported_parameters = set()
        self._mutually_exclusive = mutually_exclusive
        self._required_together = required_together
        self._required_one_of = required_one_of
        self._required_if = required_if
        self._required_by = required_by
        self.argument_spec = argument_spec

    @property
    def error_messages(self):
        return self._error_messages

    @property
    def validated_parameters(self):
        return self._validated_parameters

    @property
    def valid_parameter_names(self):
        if self._valid_parameter_names:
            return self._validated_parameter_names
        valid_parameter_names = []
        for key in sorted(self.argument_spec.keys()):
            aliases = self.argument_spec[key].get('aliases')
            if aliases:
                valid_parameter_names.append("{key} ({aliases})".format(key=key, aliases=", ".join(sorted(aliases))))
            else:
                valid_parameter_names.append(key)

        self._valid_parameter_names = valid_parameter_names
        return valid_parameter_names

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
        """Validate module parameters against argument spec. Returns True/False
        for overall pass/fail of validation and coercion.

        For unsupported parameters, a format string is added to ``self.error_messages``
        with ``name`` and ``kind`` fields. These should be replaced with the name
        of the plugin and the plugin kind so the message is useful to the reader.

        :Example:

        validator = ArgumentSpecValidator(argument_spec, parameters)
        passed = validator.validate()
        if not passed:
            sys.exit("Validation failed: {0}".format(", ".join(validator.error_messages).format(name='name', kind='module'))

        valid_params = validator.validated_parameters

        :param argument_spec: Specification of parameters, type, and valid values
        :type argument_spec: dict

        :param parameters: Parameters provided to the role
        :type parameters: dict

        :returns: True if no errors were encountered, False if any errors were encountered.
        :rtype: bool
        """

        self._no_log_values.update(set_fallbacks(self.argument_spec, self._validated_parameters))

        alias_warnings = []
        alias_deprecations = []
        try:
            alias_results, legal_inputs = handle_aliases(self.argument_spec, self._validated_parameters, alias_warnings, alias_deprecations)
        except (TypeError, ValueError) as e:
            alias_results = {}
            legal_inputs = None
            self._add_error(to_native(e))

        for option, alias in alias_warnings:
            warn('Both option %s and its alias %s are set.' % (option, alias))

        for deprecation in alias_deprecations:
            deprecate("Alias '%s' is deprecated. See the module docs for more information" % deprecation['name'],
                      version=deprecation.get('version'), date=deprecation.get('date'),
                      collection_name=deprecation.get('collection_name'))

        self._no_log_values.update(list_no_log_values(self.argument_spec, self._validated_parameters))

        if legal_inputs is None:
            legal_inputs = list(alias_results.keys()) + list(self.argument_spec.keys())
        self._unsupported_parameters.update(get_unsupported_parameters(self.argument_spec, self._validated_parameters, legal_inputs))

        try:
            check_mutually_exclusive(self._mutually_exclusive, self._validated_parameters)
        except TypeError as te:
            self._add_error(to_native(te))

        self._no_log_values.update(set_defaults(self.argument_spec, self._validated_parameters, False))

        try:
            check_required_arguments(self.argument_spec, self._validated_parameters)
        except TypeError as e:
            self._add_error(to_native(e))

        _validate_argument_types(self.argument_spec, self._validated_parameters, errors=self._error_messages)
        _validate_argument_values(self.argument_spec, self._validated_parameters, errors=self._error_messages)

        checks = (
            {'func': check_required_together, 'attr': getattr(self, '_required_together')},
            {'func': check_required_one_of, 'attr': getattr(self, '_required_one_of')},
            {'func': check_required_if, 'attr': getattr(self, '_required_if')},
            {'func': check_required_by, 'attr': getattr(self, '_required_by')},
        )

        for check in checks:
            if check['attr'] is not None:
                try:
                    check['func'](check['attr'], self._validated_parameters)
                except TypeError as te:
                    self._add_error(to_native(te))

        self._no_log_values.update(set_defaults(self.argument_spec, self._validated_parameters))

        _validate_sub_spec(self.argument_spec, self._validated_parameters,
                           errors=self._error_messages,
                           no_log_values=self._no_log_values,
                           unsupported_parameters=self._unsupported_parameters)

        if self._unsupported_parameters:
            flattened_names = []
            for item in self._unsupported_parameters:
                if isinstance(item, tuple):
                    flattened_names.append(".".join(item))
                else:
                    flattened_names.append(item)

            unsupported_string = ", ".join(sorted(list(flattened_names)))
            supported_string = ", ".join(self.valid_parameter_names)
            self._add_error("Unsupported parameters for ({{name}}) {{kind}}: {0}. "
                            "Supported parameters include: {1}.".format(unsupported_string, supported_string))

        self._sanitize_error_messages()

        if self.error_messages:
            return False
        else:
            return True
