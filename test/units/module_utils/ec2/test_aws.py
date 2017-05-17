# -*- coding: utf-8 -*-
# (c) 2015, Allen Sanabria <asanabria@linuxdynasty.org>
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

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except:
    HAS_BOTO3 = False

from nose.plugins.skip import SkipTest
from ansible.compat.tests.mock import MagicMock, Mock, patch
from ansible.module_utils import basic
from ansible.compat.tests import unittest
from ansible.module_utils.ec2 import AWSRetry
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes
import botocore.exceptions
import json

#from ansible.module_utils.basic import fail_json

if not HAS_BOTO3:
    raise SkipTest("test_aws.py requires the python modules 'boto3' and 'botocore'")


class RetryTestCase(unittest.TestCase):

    def test_no_failures(self):
        self.counter = 0

        @AWSRetry.backoff(tries=2, delay=0.1)
        def no_failures():
            self.counter += 1

        r = no_failures()
        self.assertEqual(self.counter, 1)

    def test_retry_once(self):
        self.counter = 0
        err_msg = {'Error': {'Code': 'InstanceId.NotFound'}}

        @AWSRetry.backoff(tries=2, delay=0.1)
        def retry_once():
            self.counter += 1
            if self.counter < 2:
                raise botocore.exceptions.ClientError(err_msg, 'Could not find you')
            else:
                return 'success'

        r = retry_once()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)

    def test_reached_limit(self):
        self.counter = 0
        err_msg = {'Error': {'Code': 'RequestLimitExceeded'}}

        @AWSRetry.backoff(tries=4, delay=0.1)
        def fail():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_msg, 'toooo fast!!')

        #with self.assertRaises(botocore.exceptions.ClientError):
        try:
            fail()
        except Exception as e:
            self.assertEqual(e.response['Error']['Code'], 'RequestLimitExceeded')
        self.assertEqual(self.counter, 4)

    def test_unexpected_exception_does_not_retry(self):
        self.counter = 0
        err_msg = {'Error': {'Code': 'AuthFailure'}}

        @AWSRetry.backoff(tries=4, delay=0.1)
        def raise_unexpected_error():
            self.counter += 1
            raise botocore.exceptions.ClientError(err_msg, 'unexpected error')

        #with self.assertRaises(botocore.exceptions.ClientError):
        try:
            raise_unexpected_error()
        except Exception as e:
            self.assertEqual(e.response['Error']['Code'], 'AuthFailure')

        self.assertEqual(self.counter, 1)


class ErrorReportingTestcase(unittest.TestCase):

    def test_botocore_exception_reports_nicely_via_fail_json_aws(self):

        basic._ANSIBLE_ARGS=to_bytes(json.dumps({'ANSIBLE_MODULE_ARGS': {}}))
        module = AnsibleModule(argument_spec = dict(
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
               in fail_json_double.mock_calls[0][2]["traceback"]), \
               "traceback doesn't include correct function, fail call was actually: " \
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
        module = AnsibleModule(argument_spec = dict(
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
               in fail_json_double.mock_calls[0][2]["traceback"]), \
               "traceback doesn't include correct function, fail call was actually: " \
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
