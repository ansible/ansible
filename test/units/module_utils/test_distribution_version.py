# -*- coding: utf-8 -*-
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
from __future__ import (absolute_import, division)
__metaclass__ = type

import sys

# to work around basic.py reading stdin
import json
from io import BytesIO, StringIO
from ansible.compat.six import PY3
from ansible.utils.unicode import to_bytes

# for testing
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

import ansible.module_utils.facts


@unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
class TestModuleUtilsFactsDistribution(unittest.TestCase):

    def setUp(self):
        self.real_stdin = sys.stdin
        from ansible.module_utils import basic

        args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}, ANSIBLE_MODULE_CONSTANTS={}))
        if PY3:
            sys.stdin = StringIO(args)
            sys.stdin.buffer = BytesIO(to_bytes(args))
        else:
            sys.stdin = BytesIO(to_bytes(args))
        self.module = basic.AnsibleModule(argument_spec=dict())

    def tearDown(self):
        sys.stdin = self.real_stdin

    def clear_modules(self, mods):
        for mod in mods:
            if mod in sys.modules:
                del sys.modules[mod]

    def test_distribution_from_files(self):
        """tests the distribution parsing code of the Facts class

        testsets have
        * a name (for output/debugging only)
        * input files that are faked
          * those should be complete and also include "irrelevant" files that might be mistaken as coming from other distributions
          * all files that are not listed here are assumed to not exist at all
        * the output of pythons platform.dist()
        * results for the ansible variables distribution*
        """

        testsets = [
            {
                "name" : "openSUSE Leap 42.1",
                "input": {
                    "/etc/os-release":
                    """NAME="openSUSE Leap"
                    VERSION="42.1"
                    VERSION_ID="42.1"
                    PRETTY_NAME="openSUSE Leap 42.1 (x86_64)"
                    ID=opensuse
                    ANSI_COLOR="0;32"
                    CPE_NAME="cpe:/o:opensuse:opensuse:42.1"
                    BUG_REPORT_URL="https://bugs.opensuse.org"
                    HOME_URL="https://opensuse.org/"
                    ID_LIKE="suse"
                    """,
                    "/etc/SuSE-release":"""
                    openSUSE 42.1 (x86_64)
                    VERSION = 42.1
                    CODENAME = Malachite
                    # /etc/SuSE-release is deprecated and will be removed in the future, use /etc/os-release instead
                    """
                },
                "platform.dist": ['SuSE', '42.1', 'x86_64'],
                "result":{
                    "distribution": "openSUSE Leap",
                    "distribution_major_version": "42",
                    "distribution_release": "x86_64",
                    "distribution_version": "42.1",
                }
            },
			{
                'name': 'openSUSE 13.2',
                'input': {'/etc/SuSE-release': 'openSUSE 13.2 (x86_64)\nVERSION = 13.2\nCODENAME = Harlequin\n# /etc/SuSE-release is deprecated and will be removed in the future, use /etc/os-release instead\n',
                          '/etc/os-release': 'NAME=openSUSE\nVERSION="13.2 (Harlequin)"\nVERSION_ID="13.2"\nPRETTY_NAME="openSUSE 13.2 (Harlequin) (x86_64)"\nID=opensuse\nANSI_COLOR="0;32"\nCPE_NAME="cpe:/o:opensuse:opensuse:13.2"\nBUG_REPORT_URL="https://bugs.opensuse.org"\nHOME_URL="https://opensuse.org/"\nID_LIKE="suse"\n'},
                'platform.dist': ('SuSE', '13.2', 'x86_64'),
                'result': {'distribution': u'openSUSE',
                           'distribution_major_version': u'13',
                           'distribution_release': u'Harlequin',
                           'distribution_version': u'13.2'}
            },
            { # see https://github.com/ansible/ansible/issues/14837
                "name": "SLES 11.3",
                "input": {
                    "/etc/SuSE-release":"""
SUSE Linux Enterprise Server 11 (x86_64)
VERSION = 11
PATCHLEVEL = 3
                    """
                },
                "platform.dist": ['SuSE', '11', 'x86_64'],
                "result":{
                    "distribution": "SLES",
                    "distribution_major_version": "11",
                    "distribution_release": "3",
                    "distribution_version": "11.3",
                }
            },
            { # see https://github.com/ansible/ansible/issues/14837
                "name": "SLES 11.4",
                "input": {
                    "/etc/SuSE-release":"""
SUSE Linux Enterprise Server 11 (x86_64)
VERSION = 11
PATCHLEVEL = 4
                    """,
                    "/etc/os-release":"""
NAME="SLES"
VERSION="11.4"
VERSION_ID="11.4"
PRETTY_NAME="SUSE Linux Enterprise Server 11 SP4"
ID="sles"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:suse:sles:11:4"
                    """,
                },
                "platform.dist": ['SuSE', '11', 'x86_64'],
                "result":{
                    "distribution": "SLES",
                    "distribution_major_version": "11",
                    "distribution_release": "4",
                    "distribution_version": "11.4",
                }
            },
            { # see https://github.com/ansible/ansible/issues/14837
                "name": "SLES 12 SP0",
                "input": {
                    "/etc/SuSE-release":"""
SUSE Linux Enterprise Server 12 (x86_64)
VERSION = 12
PATCHLEVEL = 0
# This file is deprecated and will be removed in a future service pack or release.
# Please check /etc/os-release for details about this release.
                    """,
                    "/etc/os-release":"""
NAME="SLES"
VERSION="12"
VERSION_ID="12"
PRETTY_NAME="SUSE Linux Enterprise Server 12"
ID="sles"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:suse:sles:12"
                    """,
                },
                "platform.dist": ['SuSE', '12', 'x86_64'],
                "result":{
                    "distribution": "SLES",
                    "distribution_major_version": "12",
                    "distribution_release": "0",
                    "distribution_version": "12",
                }
            },

            { # see https://github.com/ansible/ansible/issues/14837
                "name": "SLES 12 SP1",
                "input": {
                    "/etc/SuSE-release":"""
SUSE Linux Enterprise Server 12 (x86_64)
VERSION = 12
PATCHLEVEL = 0
# This file is deprecated and will be removed in a future service pack or release.
# Please check /etc/os-release for details about this release.
                    """,
                    "/etc/os-release":"""
NAME="SLES"
VERSION="12-SP1"
VERSION_ID="12.1"
PRETTY_NAME="SUSE Linux Enterprise Server 12 SP1"
ID="sles"
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:suse:sles:12:sp1"
                    """,
                },
                "platform.dist": ['SuSE', '12', 'x86_64'],
                "result":{
                    "distribution": "SLES",
                    "distribution_major_version": "12",
                    "distribution_release": "1",
                    "distribution_version": "12.1",
                }
            },

            {
                "name": "Debian stretch/sid",
                "input": {
                    "/etc/os-release":"""
PRETTY_NAME="Debian GNU/Linux stretch/sid"
NAME="Debian GNU/Linux"
ID=debian
HOME_URL="https://www.debian.org/"
SUPPORT_URL="https://www.debian.org/support"
BUG_REPORT_URL="https://bugs.debian.org/"
                    """,
                    "/etc/debian_version":"""
                    stretch/sid
                    """,
                },
                "platform.dist": ('debian', 'stretch/sid', ''),
                "result":{
                    "distribution": "Debian",
                    "distribution_major_version": "stretch/sid",
                    "distribution_release": "NA",
                    "distribution_version": "stretch/sid",
                }
            },
            {
                'name': "Debian 7.9",
                'input': {'/etc/os-release': 'PRETTY_NAME="Debian GNU/Linux 7 (wheezy)"\nNAME="Debian GNU/Linux"'
                                             '\nVERSION_ID="7"\nVERSION="7 (wheezy)"\nID=debian\nANSI_COLOR="1;31"\n'
                                             'HOME_URL="http://www.debian.org/"\nSUPPORT_URL="http://www.debian.org/support/'
                                             '"\nBUG_REPORT_URL="http://bugs.debian.org/"\n'},
                'platform.dist': ('debian', '7.9', ''),
                'result': {'distribution': u'Debian',
                           'distribution_major_version': u'7',
                           'distribution_release': u'wheezy',
                           'distribution_version': u'7.9'}
            },
            {
                'name': "Ubuntu 14.04",
                'input': {'/etc/lsb-release': 'DISTRIB_ID=Ubuntu\nDISTRIB_RELEASE=14.04\nDISTRIB_CODENAME=trusty\nDISTRIB_DESCRIPTION="Ubuntu 14.04.4 LTS"\n',
                          '/etc/os-release': 'NAME="Ubuntu"\nVERSION="14.04.4 LTS, Trusty Tahr"\nID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu 14.04.4 LTS"\nVERSION_ID="14.04"\nHOME_URL="http://www.ubuntu.com/"\nSUPPORT_URL="http://help.ubuntu.com/"\nBUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"\n'},
                'platform.dist': ('Ubuntu', '14.04', 'trusty'),
                'result': {'distribution': u'Ubuntu',
                           'distribution_major_version': u'14',
                           'distribution_release': u'trusty',
                           'distribution_version': u'14.04'}
            },
            {
                'name': "Ubuntu 12.04",
                'input': {'/etc/lsb-release': 'DISTRIB_ID=Ubuntu\nDISTRIB_RELEASE=12.04\nDISTRIB_CODENAME=precise\nDISTRIB_DESCRIPTION="Ubuntu 12.04.5 LTS"\n',
                          '/etc/os-release': 'NAME="Ubuntu"\nVERSION="12.04.5 LTS, Precise Pangolin"\nID=ubuntu\nID_LIKE=debian\nPRETTY_NAME="Ubuntu precise (12.04.5 LTS)"\nVERSION_ID="12.04"\n'},
                'platform.dist': ('Ubuntu', '12.04', 'precise'),
                'result': {'distribution': u'Ubuntu',
                           'distribution_major_version': u'12',
                           'distribution_release': u'precise',
                           'distribution_version': u'12.04'}
            },
            {
                'name': 'Core OS',
                'input': {
                    '/etc/os-release':"""
NAME=CoreOS
ID=coreos
VERSION=976.0.0
VERSION_ID=976.0.0
BUILD_ID=2016-03-03-2324
PRETTY_NAME="CoreOS 976.0.0 (Coeur Rouge)"
ANSI_COLOR="1;32"
HOME_URL="https://coreos.com/"
BUG_REPORT_URL="https://github.com/coreos/bugs/issues"
                    """,
                    '/etc/lsb-release':'DISTRIB_ID=CoreOS\nDISTRIB_RELEASE=976.0.0\nDISTRIB_CODENAME="Coeur Rouge"\nDISTRIB_DESCRIPTION="CoreOS 976.0.0 (Coeur Rouge)"\n',
                },
                'platform.dist': ('', '', ''),
                'result' : {
                    "distribution": "CoreOS",
                    "distribution_major_version": "NA",
                    "distribution_release": "NA",
                    "distribution_version": "976.0.0",
                }
            }


        ]

        for t in testsets:

            def mock_get_file_content(fname, default=None, strip=True):
                data = default
                if fname in t['input']:
                    # for debugging
                    print('faked '+fname+' for '+t['name'])
                    data = t['input'][fname].strip()
                if strip and data is not None:
                    data = data.strip()
                return data

            def mock_path_exists(fname):
                return fname in t['input']

            def mock_path_getsize(fname):
                if fname in t['input']:
                    return len(t['input'][fname])
                else:
                    return 0


            with patch('ansible.module_utils.facts.get_file_content', side_effect=mock_get_file_content):
                with patch('os.path.exists', side_effect=mock_path_exists):
                    with patch('os.path.getsize', side_effect=mock_path_getsize):
                        with patch('platform.dist', return_value=t['platform.dist']):
                            with patch('platform.system', return_value='Linux'):
                                generated_facts = ansible.module_utils.facts.Facts(self.module).populate()
                                for key, val in t['result'].items():
                                    self.assertIn(key, generated_facts)
                                    msg = 'Comparing value of %s on %s, should: %s, is: %s' %\
                                        (key, t['name'], val, generated_facts[key])
                                    self.assertEqual(generated_facts[key], val, msg)
