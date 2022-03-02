# unit tests for ansible os_release fact collectors
# -*- coding: utf-8 -*-
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
#

# Make coding more python3-ish
from __future__ import (absolute_import, division)
__metaclass__ = type

from ansible.compat.tests import unittest
from ansible.module_utils.facts.system.os_release import parse_file

TEST_CASES = {
    'fedora atomic': {
        'content': """NAME=Fedora
VERSION="26 (Atomic Host)"
ID=fedora
VERSION_ID=26
PRETTY_NAME="Fedora 26 (Atomic Host)"
ANSI_COLOR="0;34"
CPE_NAME="cpe:/o:fedoraproject:fedora:26"
HOME_URL="https://fedoraproject.org/"
BUG_REPORT_URL="https://bugzilla.redhat.com/"
REDHAT_BUGZILLA_PRODUCT="Fedora"
REDHAT_BUGZILLA_PRODUCT_VERSION=26
REDHAT_SUPPORT_PRODUCT="Fedora"
REDHAT_SUPPORT_PRODUCT_VERSION=26
PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy
VARIANT="Atomic Host"
VARIANT_ID=atomic.host""",
        'parsed_content': {
            'VERSION': '26 (Atomic Host)',
            'VARIANT_ID': 'atomic.host',
            'CPE_NAME': 'cpe:/o:fedoraproject:fedora:26',
        },
    },
}


class TestOSReleaseParseFile(unittest.TestCase):
    def test_collect_testfile(self):
        for case in TEST_CASES.values():
            result = parse_file(case['content'])
            for k in case['parsed_content']:
                self.assertIn(k, result)
                self.assertEqual(case['parsed_content'][k], result[k])
