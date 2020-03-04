# (c) 2017 Red Hat Inc.
#
# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

from ansible.module_utils.ec2 import map_complex_type, compare_policies


class Ec2Utils(unittest.TestCase):

    def setUp(self):
        # A pair of simple IAM Trust relationships using bools, the first a
        # native bool the second a quoted string
        self.bool_policy_bool = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": True}
                    },
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::XXXXXXXXXXXX:root"},
                    "Sid": "AssumeRoleWithBoolean"
                }
            ]
        }

        self.bool_policy_string = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "Bool": {"aws:MultiFactorAuthPresent": "true"}
                    },
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::XXXXXXXXXXXX:root"},
                    "Sid": "AssumeRoleWithBoolean"
                }
            ]
        }

        # A pair of simple bucket policies using numbers, the first a
        # native int the second a quoted string
        self.numeric_policy_number = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "s3:ListBucket",
                    "Condition": {
                        "NumericLessThanEquals": {"s3:max-keys": 15}
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::examplebucket",
                    "Sid": "s3ListBucketWithNumericLimit"
                }
            ]
        }

        self.numeric_policy_string = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    "Action": "s3:ListBucket",
                    "Condition": {
                        "NumericLessThanEquals": {"s3:max-keys": "15"}
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::examplebucket",
                    "Sid": "s3ListBucketWithNumericLimit"
                }
            ]
        }

        self.small_policy_one = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 's3:PutObjectAcl',
                    'Sid': 'AddCannedAcl2',
                    'Resource': 'arn:aws:s3:::test_policy/*',
                    'Effect': 'Allow',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']}
                }
            ]
        }

        # The same as small_policy_one, except the single resource is in a list and the contents of Statement are jumbled
        self.small_policy_two = {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Effect': 'Allow',
                    'Action': 's3:PutObjectAcl',
                    'Principal': {'AWS': ['arn:aws:iam::XXXXXXXXXXXX:user/username1', 'arn:aws:iam::XXXXXXXXXXXX:user/username2']},
                    'Resource': ['arn:aws:s3:::test_policy/*'],
                    'Sid': 'AddCannedAcl2'
                }
            ]
        }

        self.larger_policy_one = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Test",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                        ]
                    },
                    "Action": "s3:PutObjectAcl",
                    "Resource": "arn:aws:s3:::test_policy/*"
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                    },
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ],
                    "Resource": "arn:aws:s3:::test_policy/*"
                }
            ]
        }

        # The same as larger_policy_one, except having a list of length 1 and jumbled contents
        self.larger_policy_two = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": {
                       "AWS": ["arn:aws:iam::XXXXXXXXXXXX:user/testuser2"]
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"
                    ]
                },
                {
                    "Action": "s3:PutObjectAcl",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser2"
                        ]
                    },
                    "Sid": "Test",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Effect": "Allow"
                }
            ]
        }

        # Different than larger_policy_two: a different principal is given
        self.larger_policy_three = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Principal": {
                        "AWS": ["arn:aws:iam::XXXXXXXXXXXX:user/testuser2"]
                    },
                    "Effect": "Allow",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Action": [
                        "s3:PutObject",
                        "s3:PutObjectAcl"]
                },
                {
                    "Action": "s3:PutObjectAcl",
                    "Principal": {
                        "AWS": [
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser1",
                            "arn:aws:iam::XXXXXXXXXXXX:user/testuser3"
                        ]
                    },
                    "Sid": "Test",
                    "Resource": "arn:aws:s3:::test_policy/*",
                    "Effect": "Allow"
                }
            ]
        }

    def test_map_complex_type_over_dict(self):
        complex_type = {'minimum_healthy_percent': "75", 'maximum_percent': "150"}
        type_map = {'minimum_healthy_percent': 'int', 'maximum_percent': 'int'}
        complex_type_mapped = map_complex_type(complex_type, type_map)
        complex_type_expected = {'minimum_healthy_percent': 75, 'maximum_percent': 150}
        self.assertEqual(complex_type_mapped, complex_type_expected)

    def test_compare_small_policies_without_differences(self):
        """ Testing two small policies which are identical except for:
                * The contents of the statement are in different orders
                * The second policy contains a list of length one whereas in the first it is a string
        """
        self.assertFalse(compare_policies(self.small_policy_one, self.small_policy_two))

    def test_compare_large_policies_without_differences(self):
        """ Testing two larger policies which are identical except for:
                * The statements are in different orders
                * The contents of the statements are also in different orders
                * The second contains a list of length one for the Principal whereas in the first it is a string
        """
        self.assertFalse(compare_policies(self.larger_policy_one, self.larger_policy_two))

    def test_compare_larger_policies_with_difference(self):
        """ Testing two larger policies which are identical except for:
                * one different principal
        """
        self.assertTrue(compare_policies(self.larger_policy_two, self.larger_policy_three))

    def test_compare_smaller_policy_with_larger(self):
        """ Testing two policies of different sizes """
        self.assertTrue(compare_policies(self.larger_policy_one, self.small_policy_one))

    def test_compare_boolean_policy_bool_and_string_are_equal(self):
        """ Testing two policies one using a quoted boolean, the other a bool """
        self.assertFalse(compare_policies(self.bool_policy_string, self.bool_policy_bool))

    def test_compare_numeric_policy_number_and_string_are_equal(self):
        """ Testing two policies one using a quoted number, the other an int """
        self.assertFalse(compare_policies(self.numeric_policy_string, self.numeric_policy_number))
