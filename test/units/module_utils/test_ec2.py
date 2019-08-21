# (c) 2017 Red Hat Inc.
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

# (c) 2017 Red Hat Inc.
import unittest

from ansible.module_utils.ec2 import map_complex_type, compare_policies

class Ec2Utils(unittest.TestCase):

    def setUp(self):
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
