# -*- coding: utf-8 -*-
# Copyright (c) 2021 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.arg_spec import ArgumentSpecValidator


def test_add_sequence():
    v = ArgumentSpecValidator({}, {})
    errors = [
        'one error',
        'another error',
    ]
    v._add_error(errors)

    assert v.error_messages == errors


def test_invalid_error_message():
    v = ArgumentSpecValidator({}, {})

    with pytest.raises(ValueError, match="Error messages must be a string or sequence not a"):
        v._add_error(None)
