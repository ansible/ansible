# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class AnsibleFallbackNotFound(Exception):
    """Fallback validator was not found"""


class AnsibleValidationError(Exception):
    """Single argument spec validation error"""

    def __init__(self, message, error_type=None):
        super(AnsibleValidationError, self).__init__(message)
        self.error_message = message
        self.error_type = error_type

    @property
    def msg(self):
        return self.args[0]


class AnsibleValidationErrorMultiple(AnsibleValidationError):
    """Multiple argument spec validation errors"""

    def __init__(self, errors=None):
        self.errors = errors[:] if errors else []

    def __getitem__(self, key):
        return self.errors[key]

    def __setitem__(self, key, value):
        self.errors[key] = value

    def __delitem__(self, key):
        del self.errors[key]

    @property
    def msg(self):
        return self.errors[0].args[0]

    @property
    def messages(self):
        return [err.msg for err in self.errors]

    def append(self, error):
        self.errors.append(error)

    def extend(self, errors):
        self.errors.extend(errors)
