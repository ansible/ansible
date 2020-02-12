# -*- coding: utf-8 -*-
# (c) 2015, Allen Sanabria <asanabria@linuxdynasty.org>
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import boto3
    import botocore
    HAS_BOTO3 = True
except Exception:
    HAS_BOTO3 = False

import pytest

from units.compat import unittest
from ansible.module_utils.ec2 import AWSRetry

if not HAS_BOTO3:
    pytestmark = pytest.mark.skip("test_aws.py requires the python modules 'boto3' and 'botocore'")


class RetryTestCase(unittest.TestCase):

    def test_no_failures(self):
        self.counter = 0

        @AWSRetry.backoff(tries=2, delay=0.1)
        def no_failures():
            self.counter += 1

        r = no_failures()
        self.assertEqual(self.counter, 1)

    def test_extend_boto3_failures(self):
        self.counter = 0
        err_msg = {'Error': {'Code': 'MalformedPolicyDocument'}}

        @AWSRetry.backoff(tries=2, delay=0.1, catch_extra_error_codes=['MalformedPolicyDocument'])
        def extend_failures():
            self.counter += 1
            if self.counter < 2:
                raise botocore.exceptions.ClientError(err_msg, 'You did something wrong.')
            else:
                return 'success'

        r = extend_failures()
        self.assertEqual(r, 'success')
        self.assertEqual(self.counter, 2)

    def test_retry_once(self):
        self.counter = 0
        err_msg = {'Error': {'Code': 'InternalFailure'}}

        @AWSRetry.backoff(tries=2, delay=0.1)
        def retry_once():
            self.counter += 1
            if self.counter < 2:
                raise botocore.exceptions.ClientError(err_msg, 'Something went wrong!')
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

        # with self.assertRaises(botocore.exceptions.ClientError):
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

        # with self.assertRaises(botocore.exceptions.ClientError):
        try:
            raise_unexpected_error()
        except Exception as e:
            self.assertEqual(e.response['Error']['Code'], 'AuthFailure')

        self.assertEqual(self.counter, 1)
