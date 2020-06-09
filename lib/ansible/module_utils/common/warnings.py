# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import string_types

_global_warnings = []
_global_deprecations = []


def warn(warning):
    if isinstance(warning, string_types):
        _global_warnings.append(warning)
    else:
        raise TypeError("warn requires a string not a %s" % type(warning))


def deprecate(msg, version=None, date=None, collection_name=None):
    if isinstance(msg, string_types):
        # For compatibility, we accept that neither version nor date is set,
        # and treat that the same as if version would haven been set
        if date is not None:
            _global_deprecations.append({'msg': msg, 'date': date, 'collection_name': collection_name})
        else:
            _global_deprecations.append({'msg': msg, 'version': version, 'collection_name': collection_name})
    else:
        raise TypeError("deprecate requires a string not a %s" % type(msg))


def get_warning_messages():
    """Return a tuple of warning messages accumulated over this run"""
    return tuple(_global_warnings)


def get_deprecation_messages():
    """Return a tuple of deprecations accumulated over this run"""
    return tuple(_global_deprecations)
