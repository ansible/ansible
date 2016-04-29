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

from units.mock.procenv import swap_stdin_and_argv

# for testing
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

# the module we are actually testing


# to generate the testcase data, you can use the script gen_distribution_version_testcase.py in hacking/tests
TESTSETS = [
    {
    "platform.dist": [
        "centos",
        "7.2.1511",
        "Core"
    ],
    "input": {
        "/etc/redhat-release": "CentOS Linux release 7.2.1511 (Core) \n",
        "/etc/os-release": "NAME=\"CentOS Linux\"\nVERSION=\"7 (Core)\"\nID=\"centos\"\nID_LIKE=\"rhel fedora\"\nVERSION_ID=\"7\"\nPRETTY_NAME=\"CentOS Linux 7 (Core)\"\nANSI_COLOR=\"0;31\"\nCPE_NAME=\"cpe:/o:centos:centos:7\"\nHOME_URL=\"https://www.centos.org/\"\nBUG_REPORT_URL=\"https://bugs.centos.org/\"\n\nCENTOS_MANTISBT_PROJECT=\"CentOS-7\"\nCENTOS_MANTISBT_PROJECT_VERSION=\"7\"\nREDHAT_SUPPORT_PRODUCT=\"centos\"\nREDHAT_SUPPORT_PRODUCT_VERSION=\"7\"\n\n",
        "/etc/system-release": "CentOS Linux release 7.2.1511 (Core) \n"
    },
    "name": "CentOS 7.2.1511",
    "result": {
        "distribution_release": "Core",
        "distribution": "CentOS",
        "distribution_major_version": "7",
        "distribution_version": "7.2.1511"
    }
},
    {
    "name": "CentOS 6.7",
    "platform.dist": [
        "centos",
        "6.7",
        "Final"
    ],
    "input": {
        "/etc/redhat-release": "CentOS release 6.7 (Final)\n",
        "/etc/lsb-release": "LSB_VERSION=base-4.0-amd64:base-4.0-noarch:core-4.0-amd64:core-4.0-noarch:graphics-4.0-amd64:graphics-4.0-noarch:printing-4.0-amd64:printing-4.0-noarch\n",
        "/etc/system-release": "CentOS release 6.7 (Final)\n"
    },
    "result": {
        "distribution_release": "Final",
        "distribution": "CentOS",
        "distribution_major_version": "6",
        "distribution_version": "6.7"
    }
},
    {
    "name": "RedHat 7.2",
    "platform.dist": [
        "redhat",
        "7.2",
        "Maipo"
    ],
    "input": {
        "/etc/redhat-release": "Red Hat Enterprise Linux Server release 7.2 (Maipo)\n",
        "/etc/os-release": "NAME=\"Red Hat Enterprise Linux Server\"\nVERSION=\"7.2 (Maipo)\"\nID=\"rhel\"\nID_LIKE=\"fedora\"\nVERSION_ID=\"7.2\"\nPRETTY_NAME=\"Red Hat Enterprise Linux Server 7.2 (Maipo)\"\nANSI_COLOR=\"0;31\"\nCPE_NAME=\"cpe:/o:redhat:enterprise_linux:7.2:GA:server\"\nHOME_URL=\"https://www.redhat.com/\"\nBUG_REPORT_URL=\"https://bugzilla.redhat.com/\"\n\nREDHAT_BUGZILLA_PRODUCT=\"Red Hat Enterprise Linux 7\"\nREDHAT_BUGZILLA_PRODUCT_VERSION=7.2\nREDHAT_SUPPORT_PRODUCT=\"Red Hat Enterprise Linux\"\nREDHAT_SUPPORT_PRODUCT_VERSION=\"7.2\"\n",
        "/etc/system-release": "Red Hat Enterprise Linux Server release 7.2 (Maipo)\n"
    },
    "result": {
        "distribution_release": "Maipo",
        "distribution": "RedHat",
        "distribution_major_version": "7",
        "distribution_version": "7.2"
    }
},
{
    "name": "RedHat 6.7",
    "platform.dist": [
        "redhat",
        "6.7",
        "Santiago"
    ],
    "input": {
        "/etc/redhat-release": "Red Hat Enterprise Linux Server release 6.7 (Santiago)\n",
        "/etc/lsb-release": "LSB_VERSION=base-4.0-amd64:base-4.0-noarch:core-4.0-amd64:core-4.0-noarch:graphics-4.0-amd64:graphics-4.0-noarch:printing-4.0-amd64:printing-4.0-noarch\n",
        "/etc/system-release": "Red Hat Enterprise Linux Server release 6.7 (Santiago)\n"
    },
    "result": {
        "distribution_release": "Santiago",
        "distribution": "RedHat",
        "distribution_major_version": "6",
        "distribution_version": "6.7"
    }
},
{
        "name" : "openSUSE Leap 42.1",
        "input": {
            "/etc/os-release":
            """
NAME="openSUSE Leap"
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
        'input': {'/etc/SuSE-release': """openSUSE 13.2 (x86_64)
VERSION = 13.2
CODENAME = Harlequin
# /etc/SuSE-release is deprecated and will be removed in the future, use /etc/os-release instead
""",
                  '/etc/os-release': """NAME=openSUSE
VERSION="13.2 (Harlequin)"
VERSION_ID="13.2"
PRETTY_NAME="openSUSE 13.2 (Harlequin) (x86_64)"
ID=opensuse
ANSI_COLOR="0;32"
CPE_NAME="cpe:/o:opensuse:opensuse:13.2"
BUG_REPORT_URL="https://bugs.opensuse.org"
HOME_URL="https://opensuse.org/"
ID_LIKE="suse"
"""},
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
        'input': {'/etc/os-release': """PRETTY_NAME="Debian GNU/Linux 7 (wheezy)"
NAME="Debian GNU/Linux"
VERSION_ID="7"
VERSION="7 (wheezy)"
ID=debian
ANSI_COLOR="1;31"
HOME_URL="http://www.debian.org/"
SUPPORT_URL="http://www.debian.org/support/"
BUG_REPORT_URL="http://bugs.debian.org/"
"""},
        'platform.dist': ('debian', '7.9', ''),
        'result': {'distribution': u'Debian',
                   'distribution_major_version': u'7',
                   'distribution_release': u'wheezy',
                   'distribution_version': u'7.9'}
    },
    {
        'name': "Ubuntu 14.04",
        'input': {'/etc/lsb-release': """DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=14.04
DISTRIB_CODENAME=trusty
DISTRIB_DESCRIPTION="Ubuntu 14.04.4 LTS"
""",
                  '/etc/os-release': """NAME="Ubuntu"
VERSION="14.04.4 LTS, Trusty Tahr"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 14.04.4 LTS"
VERSION_ID="14.04"
HOME_URL="http://www.ubuntu.com/"
SUPPORT_URL="http://help.ubuntu.com/"
BUG_REPORT_URL="http://bugs.launchpad.net/ubuntu/"
"""},
        'platform.dist': ('Ubuntu', '14.04', 'trusty'),
        'result': {'distribution': u'Ubuntu',
                   'distribution_major_version': u'14',
                   'distribution_release': u'trusty',
                   'distribution_version': u'14.04'}
    },
    {
        'name': "Ubuntu 12.04",
        'input': {'/etc/lsb-release': """DISTRIB_ID=Ubuntu
DISTRIB_RELEASE=12.04
DISTRIB_CODENAME=precise
DISTRIB_DESCRIPTION="Ubuntu 12.04.5 LTS"
""",
                  '/etc/os-release': """NAME="Ubuntu"
VERSION="12.04.5 LTS, Precise Pangolin"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu precise (12.04.5 LTS)"
VERSION_ID="12.04"
"""},
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
            '/etc/lsb-release':"""DISTRIB_ID=CoreOS
DISTRIB_RELEASE=976.0.0
DISTRIB_CODENAME="Coeur Rouge"
DISTRIB_DESCRIPTION="CoreOS 976.0.0 (Coeur Rouge)"
""",
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

@unittest.skipIf(sys.version_info[0] >= 3, "Python 3 is not supported on targets (yet)")
def test_distribution_version():
    """tests the distribution parsing code of the Facts class

    testsets have
    * a name (for output/debugging only)
    * input files that are faked
      * those should be complete and also include "irrelevant" files that might be mistaken as coming from other distributions
      * all files that are not listed here are assumed to not exist at all
    * the output of pythons platform.dist()
    * results for the ansible variables distribution*
    """

    # needs to be in here, because the import fails with python3 still
    import ansible.module_utils.facts as facts

    from ansible.module_utils import basic

    args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}, ANSIBLE_MODULE_CONSTANTS={}))
    with swap_stdin_and_argv(stdin_data=args):
        module = basic.AnsibleModule(argument_spec=dict())

        for t in TESTSETS:
            # run individual tests via generator
            # set nicer stdout output for nosetest
            _test_one_distribution.description = "check distribution_version for %s" % t['name']
            yield _test_one_distribution, facts, module, t

def _test_one_distribution(facts, module, testcase):
    """run the test on one distribution testcase

    * prepare some mock functions to get the testdata in
    * run Facts()
    * compare with the expected output
    """

    def mock_get_file_content(fname, default=None, strip=True):
        """give fake content if it exists, otherwise pretend the file is empty"""
        data = default
        if fname in testcase['input']:
            # for debugging
            print('faked '+fname+' for '+testcase['name'])
            data = testcase['input'][fname].strip()
        if strip and data is not None:
            data = data.strip()
        return data

    def mock_path_exists(fname):
        return fname in testcase['input']

    def mock_path_getsize(fname):
        if fname in testcase['input']:
            # the len is not used, but why not be honest if you can be?
            return len(testcase['input'][fname])
        else:
            return 0

    @patch('ansible.module_utils.facts.get_file_content', mock_get_file_content)
    @patch('os.path.exists', mock_path_exists)
    @patch('os.path.getsize', mock_path_getsize)
    @patch('platform.dist', lambda: testcase['platform.dist'])
    @patch('platform.system', lambda: 'Linux')
    def get_facts(testcase):
        return facts.Facts(module).populate()

    generated_facts = get_facts(testcase)

    # testcase['result'] has a list of variables and values it expects Facts() to set
    for key, val in testcase['result'].items():
        assert key in generated_facts
        msg = 'Comparing value of %s on %s, should: %s, is: %s' %\
            (key, testcase['name'], val, generated_facts[key])
        assert generated_facts[key] == val, msg
