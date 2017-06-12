# -*- coding: utf-8 -*-
# (c) 2017, Michael De La Rue
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
import unittest
from ansible.module_utils import basic
from ansible.module_utils.aws import AnsibleAWSModule
from ansible.module_utils._text import to_bytes
from ansible.compat.tests.mock import MagicMock, Mock, patch
import json

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

if not HAS_BOTO3:
    raise SkipTest("test_aws_module.py requires the python modules 'boto3' and 'botocore'")

class AWSModuleTestCase(unittest.TestCase):

    basic._ANSIBLE_ARGS=to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': {}}))
    def test_create_aws_module(self):
        m=AnsibleAWSModule(argument_spec = dict(
            fail_mode = dict(type='list', default=['success'])
        ))
        m_noretry_no_customargs=AnsibleAWSModule(
            autoretry=False , default_args=False,
            argument_spec = dict(
                fail_mode = dict(type='list', default=['success'])
            )
        )

class ErrorReportingTestcase(unittest.TestCase):

    def test_botocore_exception_reports_nicely_via_fail_json_aws(self):

        basic._ANSIBLE_ARGS=to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': {}}))
        module = AnsibleAWSModule(argument_spec = dict(
            fail_mode = dict(type='list', default=['success'])
        ))

        fail_json_double=Mock()
        err_msg = {'Error': {'Code': 'FakeClass.FakeError'}}
        with patch.object(basic.AnsibleModule, 'fail_json', fail_json_double):
            try:
                raise botocore.exceptions.ClientError(err_msg, 'Could not find you')
            except Exception as e:
                print("exception is " + str(e))
                module.fail_json_aws(e, msg="Fake failure for testing boto exception messages")

        assert(len(fail_json_double.mock_calls) > 0), "failed to call fail_json when should have"
        assert(len(fail_json_double.mock_calls) < 2), "called fail_json multiple times when once would do"
        assert("test_botocore_exception_reports_nicely"
               in fail_json_double.mock_calls[0][2]["exception"]), \
               "exception traceback doesn't include correct function, fail call was actually: " \
                + str(fail_json_double.mock_calls[0])

        assert("Fake failure for testing boto exception messages:" in fail_json_double.mock_calls[0][2]["msg"]), \
            "error message doesn't include the local message; was: " \
            + str(fail_json_double.mock_calls[0])
        assert("Could not find you" in fail_json_double.mock_calls[0][2]["msg"]), \
            "error message doesn't include the botocore exception message; was: " \
            + str(fail_json_double.mock_calls[0])
        try:
            fail_json_double.mock_calls[0][2]["error"]
        except KeyError:
            raise Exception("error was missing; call was: " + str(fail_json_double.mock_calls[0]))
        assert("FakeClass.FakeError" == fail_json_double.mock_calls[0][2]["error"]["code"]), \
            "Failed to find error/code; was: " + str(fail_json_double.mock_calls[0])



    def test_botocore_exception_without_response_reports_nicely_via_fail_json_aws(self):

        basic._ANSIBLE_ARGS=to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': {}}))
        module = AnsibleAWSModule(argument_spec = dict(
            fail_mode = dict(type='list', default=['success'])
        ))

        fail_json_double=Mock()
        err_msg = None
        with patch.object(basic.AnsibleModule, 'fail_json', fail_json_double):
            try:
                raise botocore.exceptions.ClientError(err_msg, 'Could not find you')
            except Exception as e:
                print("exception is " + str(e))
                module.fail_json_aws(e, msg="Fake failure for testing boto exception messages again")

        assert(len(fail_json_double.mock_calls) > 0), "failed to call fail_json when should have"
        assert(len(fail_json_double.mock_calls) < 2), \
            "called fail_json multiple times when once would do"

        assert("test_botocore_exception_without_response_reports_nicely_via_fail_json_aws"
               in fail_json_double.mock_calls[0][2]["exception"]), \
               "exception traceback doesn't include correct function, fail call was actually: " \
               + str(fail_json_double.mock_calls[0])

        assert("Fake failure for testing boto exception messages again:" in fail_json_double.mock_calls[0][2]["msg"]), \
            "error message doesn't include the local message; was: " \
            + str(fail_json_double.mock_calls[0])

        # I would have thought this should work, however the botocore exception comes back with
        # "argument of type 'NoneType' is not iterable" so it's probably not really designed
        # to handle "None" as an error response.
        #
        # assert("Could not find you" in fail_json_double.mock_calls[0][2]["msg"]), \
        #    "error message doesn't include the botocore exception message; was: " \
        #    + str(fail_json_double.mock_calls[0])


# TODO:
#  - an exception without a message
#  - plain boto exception
#  - socket errors and other standard things.
