# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.common.arg_spec import Validator


def test_required_and_default():
    arg_spec = {
        'param_req': {'required': True, 'default': 'DEFAULT'},
    }

    v = Validator()
    passed = v.validate(arg_spec, {})

    assert passed is False
    assert v.error_messages == ['internal error: required and default are mutually exclusive for param_req']
