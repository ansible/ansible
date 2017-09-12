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

from ansible.modules.cloud.amazon.s3_bucket import compare_policies

small_policy_one = {
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
small_policy_two = {
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

larger_policy_one = {
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
larger_policy_two = {
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
larger_policy_three = {
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


def test_compare_small_policies_without_differences():
    """ Testing two small policies which are identical except for:
            * The contents of the statement are in different orders
            * The second policy contains a list of length one whereas in the first it is a string
    """
    assert compare_policies(small_policy_one, small_policy_two) is False


def test_compare_large_policies_without_differences():
    """ Testing two larger policies which are identical except for:
            * The statements are in different orders
            * The contents of the statements are also in different orders
            * The second contains a list of length one for the Principal whereas in the first it is a string
    """
    assert compare_policies(larger_policy_one, larger_policy_two) is False


def test_compare_larger_policies_with_difference():
    """ Testing two larger policies which are identical except for:
            * one different principal
    """
    assert compare_policies(larger_policy_two, larger_policy_three)


def test_compare_smaller_policy_with_larger():
    """ Testing two policies of different sizes """
    assert compare_policies(larger_policy_one, small_policy_one)
