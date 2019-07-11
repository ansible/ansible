# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# Simplified BSD License (see licenses/simplified_bsd.txt or https://opensource.org/licenses/BSD-2-Clause)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


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
