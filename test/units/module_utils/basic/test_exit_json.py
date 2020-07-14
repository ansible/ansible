# -*- coding: utf-8 -*-
# Copyright (c) 2015-2017 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import sys
import datetime

import pytest


EMPTY_INVOCATION = {u'module_args': {}}
DATETIME = datetime.datetime.strptime('2020-07-13 12:50:00', '%Y-%m-%d %H:%M:%S')


class TestAnsibleModuleExitJson:
    """
    Test that various means of calling exitJson and FailJson return the messages they've been given
    """
    DATA = (
        ({}, {'invocation': EMPTY_INVOCATION}),
        ({'msg': 'message'}, {'msg': 'message', 'invocation': EMPTY_INVOCATION}),
        ({'msg': 'success', 'changed': True},
         {'msg': 'success', 'changed': True, 'invocation': EMPTY_INVOCATION}),
        ({'msg': 'nochange', 'changed': False},
         {'msg': 'nochange', 'changed': False, 'invocation': EMPTY_INVOCATION}),
        ({'msg': 'message', 'date': DATETIME.date()},
         {'msg': 'message', 'date': DATETIME.date().isoformat(), 'invocation': EMPTY_INVOCATION}),
        ({'msg': 'message', 'datetime': DATETIME},
         {'msg': 'message', 'datetime': DATETIME.isoformat(), 'invocation': EMPTY_INVOCATION}),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    # pylint: disable=undefined-variable
    @pytest.mark.parametrize('args, expected, stdin', ((a, e, {}) for a, e in DATA), indirect=['stdin'])
    def test_exit_json_exits(self, am, capfd, args, expected):
        with pytest.raises(SystemExit) as ctx:
            am.exit_json(**args)
        assert ctx.value.code == 0

        out, err = capfd.readouterr()
        return_val = json.loads(out)
        assert return_val == expected

    # Fail_json is only legal if it's called with a message
    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    @pytest.mark.parametrize('args, expected, stdin',
                             ((a, e, {}) for a, e in DATA if 'msg' in a),  # pylint: disable=undefined-variable
                             indirect=['stdin'])
    def test_fail_json_exits(self, am, capfd, args, expected):
        with pytest.raises(SystemExit) as ctx:
            am.fail_json(**args)
        assert ctx.value.code == 1

        out, err = capfd.readouterr()
        return_val = json.loads(out)
        # Fail_json should add failed=True
        expected['failed'] = True
        assert return_val == expected

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_fail_json_msg_positional(self, am, capfd):
        with pytest.raises(SystemExit) as ctx:
            am.fail_json('This is the msg')
        assert ctx.value.code == 1

        out, err = capfd.readouterr()
        return_val = json.loads(out)
        # Fail_json should add failed=True
        assert return_val == {'msg': 'This is the msg', 'failed': True,
                              'invocation': EMPTY_INVOCATION}

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_fail_json_msg_as_kwarg_after(self, am, capfd):
        """Test that msg as a kwarg after other kwargs works"""
        with pytest.raises(SystemExit) as ctx:
            am.fail_json(arbitrary=42, msg='This is the msg')
        assert ctx.value.code == 1

        out, err = capfd.readouterr()
        return_val = json.loads(out)
        # Fail_json should add failed=True
        assert return_val == {'msg': 'This is the msg', 'failed': True,
                              'arbitrary': 42,
                              'invocation': EMPTY_INVOCATION}

    @pytest.mark.parametrize('stdin', [{}], indirect=['stdin'])
    def test_fail_json_no_msg(self, am):
        with pytest.raises(TypeError) as ctx:
            am.fail_json()

        if sys.version_info < (3,):
            error_msg = "fail_json() takes exactly 2 arguments (1 given)"
        else:
            error_msg = "fail_json() missing 1 required positional argument: 'msg'"

        assert ctx.value.args[0] == error_msg


class TestAnsibleModuleExitValuesRemoved:
    """
    Test that ExitJson and FailJson remove password-like values
    """
    OMIT = 'VALUE_SPECIFIED_IN_NO_LOG_PARAMETER'

    DATA = (
        (
            dict(username='person', password='$ecret k3y'),
            dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd=OMIT, url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
        (
            dict(username='person', password='password12345'),
            dict(one=1, pwd='$ecret k3y', url='https://username:password12345@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd='$ecret k3y', url='https://username:********@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
        (
            dict(username='person', password='$ecret k3y'),
            dict(one=1, pwd='$ecret k3y', url='https://username:$ecret k3y@foo.com/login/',
                 not_secret='following the leader', msg='here'),
            dict(one=1, pwd=OMIT, url='https://username:********@foo.com/login/',
                 not_secret='following the leader', msg='here',
                 invocation=dict(module_args=dict(password=OMIT, token=None, username='person'))),
        ),
    )

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    @pytest.mark.parametrize('am, stdin, return_val, expected',
                             (({'username': {}, 'password': {'no_log': True}, 'token': {'no_log': True}}, s, r, e)
                              for s, r, e in DATA),  # pylint: disable=undefined-variable
                             indirect=['am', 'stdin'])
    def test_exit_json_removes_values(self, am, capfd, return_val, expected):
        with pytest.raises(SystemExit):
            am.exit_json(**return_val)
        out, err = capfd.readouterr()

        assert json.loads(out) == expected

    # pylint bug: https://github.com/PyCQA/pylint/issues/511
    @pytest.mark.parametrize('am, stdin, return_val, expected',
                             (({'username': {}, 'password': {'no_log': True}, 'token': {'no_log': True}}, s, r, e)
                              for s, r, e in DATA),  # pylint: disable=undefined-variable
                             indirect=['am', 'stdin'])
    def test_fail_json_removes_values(self, am, capfd, return_val, expected):
        expected['failed'] = True
        with pytest.raises(SystemExit):
            am.fail_json(**return_val) == expected
        out, err = capfd.readouterr()

        assert json.loads(out) == expected
