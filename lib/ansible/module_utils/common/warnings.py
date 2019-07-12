# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.six import string_types

global_warnings = []


class AnsibleWarning(Warning):
    def __init__(self, msg):
        self.msg = msg
        super(AnsibleWarning, self).__init__(msg)


class AnsibleDeprecationWarning(DeprecationWarning):
    def __init__(self, msg, version=None):
        self.msg = msg
        self.version = version
        super(AnsibleDeprecationWarning, self).__init__(msg)


def warn(warning):
    if isinstance(warning, string_types):
        global_warnings.append(AnsibleWarning(warning))
    else:
        raise TypeError("warn requires a string not a %s" % type(warning))


def deprecate(msg, version=None):
    if isinstance(msg, string_types):
        global_warnings.append(AnsibleDeprecationWarning(msg,version))
    else:
        raise TypeError("deprecate requires a string not a %s" % type(msg))
