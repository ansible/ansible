# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class AnsibleFallbackNotFound(Exception):
    """Fallback validator was not found"""


class AnsibleValidationError(Exception):
    """Single argument spec validation error"""

    def __init__(self, message):
        super(AnsibleValidationError, self).__init__(message)
        self.error_message = message
        """The error message passed in when the exception was raised."""

    @property
    def msg(self):
        """The error message passed in when the exception was raised."""
        return self.args[0]


class AnsibleValidationErrorMultiple(AnsibleValidationError):
    """Multiple argument spec validation errors"""

    def __init__(self, errors=None):
        self.errors = errors[:] if errors else []
        """:class:`list` of :class:`AnsibleValidationError` objects"""

    def __getitem__(self, key):
        return self.errors[key]

    def __setitem__(self, key, value):
        self.errors[key] = value

    def __delitem__(self, key):
        del self.errors[key]

    @property
    def msg(self):
        """The first message from the first error in ``errors``."""
        return self.errors[0].args[0]

    @property
    def messages(self):
        """:class:`list` of each error message in ``errors``."""
        return [err.msg for err in self.errors]

    def append(self, error):
        """Append a new error to ``self.errors``.

        Only :class:`AnsibleValidationError` should be added.
        """

        self.errors.append(error)

    def extend(self, errors):
        """Append each item in ``errors`` to ``self.errors``. Only :class:`AnsibleValidationError` should be added."""
        self.errors.extend(errors)


class AliasError(AnsibleValidationError):
    """Error handling aliases"""


class ArgumentTypeError(AnsibleValidationError):
    """Error with parameter type"""


class ArgumentValueError(AnsibleValidationError):
    """Error with parameter value"""


class ElementError(AnsibleValidationError):
    """Error when validating elements"""


class MutuallyExclusiveError(AnsibleValidationError):
    """Mutually exclusive parameters were supplied"""


class NoLogError(AnsibleValidationError):
    """Error converting no_log values"""


class RequiredByError(AnsibleValidationError):
    """Error with parameters that are required by other parameters"""


class RequiredDefaultError(AnsibleValidationError):
    """A required parameter was assigned a default value"""


class RequiredError(AnsibleValidationError):
    """Missing a required parameter"""


class RequiredIfError(AnsibleValidationError):
    """Error with conditionally required parameters"""


class RequiredOneOfError(AnsibleValidationError):
    """Error with parameters where at least one is required"""


class RequiredTogetherError(AnsibleValidationError):
    """Error with parameters that are required together"""


class SubParameterTypeError(AnsibleValidationError):
    """Incorrect type for subparameter"""


class UnsupportedError(AnsibleValidationError):
    """Unsupported parameters were supplied"""
