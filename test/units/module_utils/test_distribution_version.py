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
import pytest

from units.mock.procenv import swap_stdin_and_argv

# for testing
from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

# the module we are actually testing
import ansible.module_utils.facts as facts


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
            "/etc/os-release": ("NAME=\"CentOS Linux\"\nVERSION=\"7 (Core)\"\nID=\"centos\"\nID_LIKE=\"rhel fedora\"\nVERSION_ID=\"7\"\n"
                                "PRETTY_NAME=\"CentOS Linux 7 (Core)\"\nANSI_COLOR=\"0;31\"\nCPE_NAME=\"cpe:/o:centos:centos:7\"\n"
                                "HOME_URL=\"https://www.centos.org/\"\nBUG_REPORT_URL=\"https://bugs.centos.org/\"\n\nCENTOS_MANTISBT_PROJECT=\"CentOS-7\"\n"
                                "CENTOS_MANTISBT_PROJECT_VERSION=\"7\"\nREDHAT_SUPPORT_PRODUCT=\"centos\"\nREDHAT_SUPPORT_PRODUCT_VERSION=\"7\"\n\n"),
            "/etc/system-release": "CentOS Linux release 7.2.1511 (Core) \n"
            },
        "name": "CentOS 7.2.1511",
        "result": {
            "distribution_release": "Core",
            "distribution": "CentOS",
            "distribution_major_version": "7",
            "os_family": "RedHat",
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
            "/etc/lsb-release": ("LSB_VERSION=base-4.0-amd64:base-4.0-noarch:core-4.0-amd64:core-4.0-noarch:graphics-4.0-amd64:graphics-4.0-noarch:"
                                 "printing-4.0-amd64:printing-4.0-noarch\n"),
            "/etc/system-release": "CentOS release 6.7 (Final)\n"
            },
        "result": {
            "distribution_release": "Final",
            "distribution": "CentOS",
            "distribution_major_version": "6",
            "os_family": "RedHat",
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
            "/etc/os-release": ("NAME=\"Red Hat Enterprise Linux Server\"\nVERSION=\"7.2 (Maipo)\"\nID=\"rhel\"\nID_LIKE=\"fedora\"\nVERSION_ID=\"7.2\"\n"
                                "PRETTY_NAME=\"Red Hat Enterprise Linux Server 7.2 (Maipo)\"\nANSI_COLOR=\"0;31\"\n"
                                "CPE_NAME=\"cpe:/o:redhat:enterprise_linux:7.2:GA:server\"\nHOME_URL=\"https://www.redhat.com/\"\n"
                                "BUG_REPORT_URL=\"https://bugzilla.redhat.com/\"\n\nREDHAT_BUGZILLA_PRODUCT=\"Red Hat Enterprise Linux 7\"\n"
                                "REDHAT_BUGZILLA_PRODUCT_VERSION=7.2\nREDHAT_SUPPORT_PRODUCT=\"Red Hat Enterprise Linux\"\n"
                                "REDHAT_SUPPORT_PRODUCT_VERSION=\"7.2\"\n"),
            "/etc/system-release": "Red Hat Enterprise Linux Server release 7.2 (Maipo)\n"
            },
        "result": {
            "distribution_release": "Maipo",
            "distribution": "RedHat",
            "distribution_major_version": "7",
            "os_family": "RedHat",
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
            "/etc/lsb-release": ("LSB_VERSION=base-4.0-amd64:base-4.0-noarch:core-4.0-amd64:core-4.0-noarch:graphics-4.0-amd64:graphics-4.0-noarch:"
                                 "printing-4.0-amd64:printing-4.0-noarch\n"),
            "/etc/system-release": "Red Hat Enterprise Linux Server release 6.7 (Santiago)\n"
            },
        "result": {
            "distribution_release": "Santiago",
            "distribution": "RedHat",
            "distribution_major_version": "6",
            "os_family": "RedHat",
            "distribution_version": "6.7"
            }
        },
    {
        "name": "Virtuozzo 7.3",
        "platform.dist": [
            "redhat",
            "7.3",
            ""
            ],
        "input": {
            "/etc/redhat-release": "Virtuozzo Linux release 7.3\n",
            "/etc/os-release": ("NAME=\"Virtuozzo\"\n"
                                "VERSION=\"7.0.3\"\n"
                                "ID=\"virtuozzo\"\n"
                                "ID_LIKE=\"rhel fedora\"\n"
                                "VERSION_ID=\"7\"\n"
                                "PRETTY_NAME=\"Virtuozzo release 7.0.3\"\n"
                                "ANSI_COLOR=\"0;31\"\n"
                                "CPE_NAME=\"cpe:/o:virtuozzoproject:vz:7\"\n"
                                "HOME_URL=\"http://www.virtuozzo.com\"\n"
                                "BUG_REPORT_URL=\"https://bugs.openvz.org/\"\n"),
            "/etc/system-release": "Virtuozzo release 7.0.3 (640)\n"
            },
        "result": {
            "distribution_release": "NA",
            "distribution": "Virtuozzo",
            "distribution_major_version": "7",
            "os_family": "RedHat",
            "distribution_version": "7.3"
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
            "distribution_release": "1",
            "os_family": "Suse",
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
                   'distribution_release': u'2',
                   'os_family': u'Suse',
                   'distribution_version': u'13.2'}
    },
    {
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/os-release": ("NAME=\"openSUSE Tumbleweed\"\n# VERSION=\"20160917\"\nID=opensuse\nID_LIKE=\"suse\"\nVERSION_ID=\"20160917\"\n"
                                "PRETTY_NAME=\"openSUSE Tumbleweed\"\nANSI_COLOR=\"0;32\"\nCPE_NAME=\"cpe:/o:opensuse:tumbleweed:20160917\"\n"
                                "BUG_REPORT_URL=\"https://bugs.opensuse.org\"\nHOME_URL=\"https://www.opensuse.org/\"\n")
        },
        "name": "openSUSE Tumbleweed 20160917",
        "result": {
            "distribution_release": "",
            "distribution": "openSUSE Tumbleweed",
            "distribution_major_version": "NA",
            "os_family": "Suse",
            "distribution_version": "20160917"
        }
    },
    {  # see https://github.com/ansible/ansible/issues/14837
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
            "os_family": "Suse",
            "distribution_version": "11.3",
        }
    },
    {  # see https://github.com/ansible/ansible/issues/14837
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
            "os_family": "Suse",
            "distribution_version": "11.4",
        }
    },
    {  # see https://github.com/ansible/ansible/issues/14837
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
            "os_family": "Suse",
            "distribution_version": "12",
        }
    },

    {  # see https://github.com/ansible/ansible/issues/14837
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
            "os_family": "Suse",
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
            "os_family": "Debian",
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
                   "os_family": "Debian",
                   'distribution_version': u'7.9'}
    },
    {
        "platform.dist": [
            "Ubuntu",
            "16.04",
            "xenial"
        ],
        "input": {
            "/etc/os-release": ("NAME=\"Ubuntu\"\nVERSION=\"16.04 LTS (Xenial Xerus)\"\nID=ubuntu\nID_LIKE=debian\nPRETTY_NAME=\"Ubuntu 16.04 LTS\"\n"
                                "VERSION_ID=\"16.04\"\nHOME_URL=\"http://www.ubuntu.com/\"\nSUPPORT_URL=\"http://help.ubuntu.com/\"\n"
                                "BUG_REPORT_URL=\"http://bugs.launchpad.net/ubuntu/\"\nUBUNTU_CODENAME=xenial\n"),
            "/etc/lsb-release": "DISTRIB_ID=Ubuntu\nDISTRIB_RELEASE=16.04\nDISTRIB_CODENAME=xenial\nDISTRIB_DESCRIPTION=\"Ubuntu 16.04 LTS\"\n"
        },
        "name": "Ubuntu 16.04",
        "result": {
            "distribution_release": "xenial",
            "distribution": "Ubuntu",
            "distribution_major_version": "16",
            "os_family": "Debian",
            "distribution_version": "16.04"
        }
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
                   "os_family": "Debian",
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
                   "os_family": "Debian",
                   'distribution_version': u'12.04'}
    },
    {
        "platform.dist": [
            "neon",
            "16.04",
            "xenial"
        ],
        "input": {
            "/etc/os-release": ("NAME=\"KDE neon\"\nVERSION=\"5.8\"\nID=neon\nID_LIKE=\"ubuntu debian\"\nPRETTY_NAME=\"KDE neon User Edition 5.8\"\n"
                                "VERSION_ID=\"16.04\"\nHOME_URL=\"http://neon.kde.org/\"\nSUPPORT_URL=\"http://neon.kde.org/\"\n"
                                "BUG_REPORT_URL=\"http://bugs.kde.org/\"\nVERSION_CODENAME=xenial\nUBUNTU_CODENAME=xenial\n"),
            "/etc/lsb-release": "DISTRIB_ID=neon\nDISTRIB_RELEASE=16.04\nDISTRIB_CODENAME=xenial\nDISTRIB_DESCRIPTION=\"KDE neon User Edition 5.8\"\n"
        },
        "name": "KDE neon 16.04",
        "result": {
            "distribution_release": "xenial",
            "distribution": "Neon",
            "distribution_major_version": "16",
            "os_family": "Debian",
            "distribution_version": "16.04"
        }
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
    },
    # Solaris and derivatives: https://gist.github.com/natefoo/7af6f3d47bb008669467
    {
        "name": "SmartOS Global Zone",
        "uname_v": "joyent_20160330T234717Z",
        "result": {
            "distribution_release": "SmartOS 20160330T234717Z x86_64",
            "distribution": "SmartOS",
            "os_family": "Solaris",
            "distribution_version": "joyent_20160330T234717Z"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                       SmartOS 20160330T234717Z x86_64\n"
                             "              Copyright 2010 Sun Microsystems, Inc.  All Rights Reserved.\n"
                             "              Copyright 2010-2012 Joyent, Inc.  All Rights Reserved.\n"
                             "                        Use is subject to license terms.\n\n"
                             "   Built with the following components:\n\n[\n"
                             "        { \"repo\": \"smartos-live\", \"branch\": \"release-20160331\", \"rev\": \"a77c410f2afe6dc9853a915733caec3609cc50f1\", "
                             "\"commit_date\": \"1459340323\", \"url\": \"git@github.com:joyent/smartos-live.git\" }\n        , "
                             "{ \"repo\": \"illumos-joyent\", \"branch\": \"release-20160331\", \"rev\": \"ab664c06caf06e9ce7586bff956e7709df1e702e\", "
                             "\"commit_date\": \"1459362533\", \"url\": \"/root/data/jenkins/workspace/smartos/MG/build/illumos-joyent\" }\n"
                             "        , { \"repo\": \"illumos-extra\", \"branch\": \"release-20160331\", "
                             "\"rev\": \"cc723855bceace3df7860b607c9e3827d47e0ff4\", \"commit_date\": \"1458153188\", "
                             "\"url\": \"/root/data/jenkins/workspace/smartos/MG/build/illumos-extra\" }\n        , "
                             "{ \"repo\": \"kvm\", \"branch\": \"release-20160331\", \"rev\": \"a8befd521c7e673749c64f118585814009fe4b73\", "
                             "\"commit_date\": \"1450081968\", \"url\": \"/root/data/jenkins/workspace/smartos/MG/build/illumos-kvm\" }\n        , "
                             "{ \"repo\": \"kvm-cmd\", \"branch\": \"release-20160331\", \"rev\": \"c1a197c8e4582c68739ab08f7e3198b2392c9820\", "
                             "\"commit_date\": \"1454723558\", \"url\": \"/root/data/jenkins/workspace/smartos/MG/build/illumos-kvm-cmd\" }\n        , "
                             "{ \"repo\": \"mdata-client\", \"branch\": \"release-20160331\", \"rev\": \"58158c44603a3316928975deccc5d10864832770\", "
                             "\"commit_date\": \"1429917227\", \"url\": \"/root/data/jenkins/workspace/smartos/MG/build/mdata-client\" }\n]\n")
        },
        "platform.system": "SunOS"
    },
    {
        "name": "SmartOS Zone",
        "uname_v": "joyent_20160330T234717Z",
        "result": {
            "distribution_release": "SmartOS x86_64",
            "distribution": "SmartOS",
            "os_family": "Solaris",
            "distribution_version": "14.3.0"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                                SmartOS x86_64\n              Copyright 2010 Sun Microsystems, Inc.  All Rights Reserved.\n"
                             "              Copyright 2010-2013 Joyent, Inc.  All Rights Reserved.\n                        Use is subject to license terms.\n"
                             "                   See joyent_20141002T182809Z for assembly date and time.\n"),
            "/etc/product": "Name: Joyent Instance\nImage: base64 14.3.0\nDocumentation: http://wiki.joyent.com/jpc2/Base+Instance\n"
        },
        "platform.system": "SunOS"
    },
    {
        "name": "OpenIndiana",
        "uname_v": "oi_151a9",
        "result": {
            "distribution_release": "OpenIndiana Development oi_151.1.9 X86 (powered by illumos)",
            "distribution": "OpenIndiana",
            "os_family": "Solaris",
            "distribution_version": "oi_151a9"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("             OpenIndiana Development oi_151.1.9 X86 (powered by illumos)\n        Copyright 2011 Oracle and/or its affiliates. "
                             "All rights reserved.\n                        Use is subject to license terms.\n                           "
                             "Assembled 17 January 2014\n")
        },
        "platform.system": "SunOS"
    },
    {
        "name": "OmniOS",
        "uname_v": "omnios-10b9c79",
        "result": {
            "distribution_release": "OmniOS v11 r151012",
            "distribution": "OmniOS",
            "os_family": "Solaris",
            "distribution_version": "r151012"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": (
                "  OmniOS v11 r151012\n  Copyright 2014 OmniTI Computer Consulting, Inc. All rights reserved.\n  Use is subject to license terms.\n\n"
            )
        },
        "platform.system": "SunOS"
    },
    {
        "name": "Nexenta 3",
        "uname_v": "NexentaOS_134f",
        "result": {
            "distribution_release": "Open Storage Appliance v3.1.6",
            "distribution": "Nexenta",
            "os_family": "Solaris",
            "distribution_version": "3.1.6"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                         Open Storage Appliance v3.1.6\n           Copyright (c) 2014 Nexenta Systems, Inc.  "
                             "All Rights Reserved.\n           Copyright (c) 2011 Oracle.  All Rights Reserved.\n                         "
                             "Use is subject to license terms.\n")
        },
        "platform.system": "SunOS"
    },
    {
        "name": "Nexenta 4",
        "uname_v": "NexentaOS_4:cd604cd066",
        "result": {
            "distribution_release": "Open Storage Appliance 4.0.3-FP2",
            "distribution": "Nexenta",
            "os_family": "Solaris",
            "distribution_version": "4.0.3-FP2"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                        Open Storage Appliance 4.0.3-FP2\n           Copyright (c) 2014 Nexenta Systems, Inc.  "
                             "All Rights Reserved.\n           Copyright (c) 2010 Oracle.  All Rights Reserved.\n                        "
                             "Use is subject to license terms.\n")
        },
        "platform.system": "SunOS"
    },
    {
        "name": "Solaris 10",
        "uname_v": "Generic_141445-09",
        "result": {
            "distribution_release": "Solaris 10 10/09 s10x_u8wos_08a X86",
            "distribution": "Solaris",
            "os_family": "Solaris",
            "distribution_version": "10"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                       Solaris 10 10/09 s10x_u8wos_08a X86\n           Copyright 2009 Sun Microsystems, Inc.  "
                             "All Rights Reserved.\n                        Use is subject to license terms.\n                           "
                             "Assembled 16 September 2009\n")
        },
        "platform.system": "SunOS"
    },
    {
        "name": "Solaris 11",
        "uname_v": "11.0",
        "result": {
            "distribution_release": "Oracle Solaris 11 11/11 X86",
            "distribution": "Solaris",
            "os_family": "Solaris",
            "distribution_version": "11"
        },
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/release": ("                           Oracle Solaris 11 11/11 X86\n  Copyright (c) 1983, 2011, Oracle and/or its affiliates.  "
                             "All rights reserved.\n                            Assembled 18 October 2011\n")
        },
        "platform.system": "SunOS"
    },

    {
        "name": "Solaris 11.3",
        "platform.dist": [
            "",
            "",
            ""
            ],
        "input": {
            "/etc/release": ("                             Oracle Solaris 11.3 X86\n  Copyright (c) 1983, 2015, Oracle and/or its affiliates.  "
            "All rights reserved.\n                            Assembled 06 October 2015\n")
            },
        "platform.system": "SunOS",
        "result": {
            "distribution_release": "Oracle Solaris 11.3 X86",
            "distribution": "Solaris",
            "os_family": "Solaris",
            "distribution_version": "11.3"
            }
        },

    {
        "name": "Solaris 10",
        "platform.dist": [
            "",
            "",
            ""
            ],
        "input": {
            "/etc/release": ("                    Oracle Solaris 10 1/13 s10x_u11wos_24a X86\n  Copyright (c) 1983, 2013, Oracle and/or its affiliates. "
                             "All rights reserved.\n                            Assembled 17 January 2013\n")
            },
        "platform.system": "SunOS",
        "result": {
            "distribution_release": "Oracle Solaris 10 1/13 s10x_u11wos_24a X86",
            "distribution": "Solaris",
            "os_family": "Solaris",
            "distribution_version": "10"
            }
        },

    {
        "name": "Fedora 22",
        "platform.dist": [
            "fedora",
            "22",
            "Twenty Two"
            ],
        "input": {
            "/etc/redhat-release": "Fedora release 22 (Twenty Two)\n",
            "/etc/os-release": ("NAME=Fedora\nVERSION=\"22 (Twenty Two)\"\nID=fedora\nVERSION_ID=22\nPRETTY_NAME=\"Fedora 22 (Twenty Two)\"\n"
                                "ANSI_COLOR=\"0;34\"\nCPE_NAME=\"cpe:/o:fedoraproject:fedora:22\"\nHOME_URL=\"https://fedoraproject.org/\"\n"
                                "BUG_REPORT_URL=\"https://bugzilla.redhat.com/\"\nREDHAT_BUGZILLA_PRODUCT=\"Fedora\"\nREDHAT_BUGZILLA_PRODUCT_VERSION=22\n"
                                "REDHAT_SUPPORT_PRODUCT=\"Fedora\"\nREDHAT_SUPPORT_PRODUCT_VERSION=22\n"
                                "PRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy\n"),
            "/etc/system-release": "Fedora release 22 (Twenty Two)\n"
            },
        "result": {
            "distribution_release": "Twenty Two",
            "distribution": "Fedora",
            "distribution_major_version": "22",
            "os_family": "RedHat",
            "distribution_version": "22"
            }
        },
    {
        "platform.dist": [
            "fedora",
            "25",
            "Rawhide"
            ],
        "input": {
            "/etc/redhat-release": "Fedora release 25 (Rawhide)\n",
            "/etc/os-release": ("NAME=Fedora\nVERSION=\"25 (Workstation Edition)\"\nID=fedora\nVERSION_ID=25\n"
                                "PRETTY_NAME=\"Fedora 25 (Workstation Edition)\"\nANSI_COLOR=\"0;34\"\nCPE_NAME=\"cpe:/o:fedoraproject:fedora:25\"\n"
                                "HOME_URL=\"https://fedoraproject.org/\"\nBUG_REPORT_URL=\"https://bugzilla.redhat.com/\"\n"
                                "REDHAT_BUGZILLA_PRODUCT=\"Fedora\"\nREDHAT_BUGZILLA_PRODUCT_VERSION=rawhide\nREDHAT_SUPPORT_PRODUCT=\"Fedora\"\n"
                                "REDHAT_SUPPORT_PRODUCT_VERSION=rawhide\nPRIVACY_POLICY_URL=https://fedoraproject.org/wiki/Legal:PrivacyPolicy\n"
                                "VARIANT=\"Workstation Edition\"\nVARIANT_ID=workstation\n"),
            "/etc/system-release": "Fedora release 25 (Rawhide)\n"
            },
        "name": "Fedora 25",
        "result": {
            "distribution_release": "Rawhide",
            "distribution": "Fedora",
            "distribution_major_version": "25",
            "os_family": "RedHat",
            "distribution_version": "25"
            }
        },

    {
        "platform.dist": [
            "",
            "",
            ""
        ],
        "input": {
            "/etc/sourcemage-release": ("Source Mage GNU/Linux x86_64-pc-linux-gnu\nInstalled from tarball using chroot image (Grimoire 0.61-rc) "
                                        "on Thu May 17 17:31:37 UTC 2012\n")
        },
        "name": "SMGL NA",
        "result": {
            "distribution_release": "NA",
            "distribution": "SMGL",
            "distribution_major_version": "NA",
            "os_family": "SMGL",
            "distribution_version": "NA"
            }
        },

]


@pytest.mark.parametrize("testcase", TESTSETS, ids=lambda x: x['name'])
def test_distribution_version(testcase):
    """tests the distribution parsing code of the Facts class

    testsets have
    * a name (for output/debugging only)
    * input files that are faked
      * those should be complete and also include "irrelevant" files that might be mistaken as coming from other distributions
      * all files that are not listed here are assumed to not exist at all
    * the output of pythons platform.dist()
    * results for the ansible variables distribution* and os_family
    """

    from ansible.module_utils import basic

    args = json.dumps(dict(ANSIBLE_MODULE_ARGS={}))
    with swap_stdin_and_argv(stdin_data=args):
        basic._ANSIBLE_ARGS = None
        module = basic.AnsibleModule(argument_spec=dict())

        _test_one_distribution(facts, module, testcase)

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

    def mock_get_uname_version(module):
        return testcase.get('uname_v', None)

    def mock_path_exists(fname):
        return fname in testcase['input']

    def mock_path_getsize(fname):
        if fname in testcase['input']:
            # the len is not used, but why not be honest if you can be?
            return len(testcase['input'][fname])
        else:
            return 0

    def mock_platform_system():
        return testcase.get('platform.system', 'Linux')

    @patch('ansible.module_utils.facts.get_file_content', mock_get_file_content)
    @patch('ansible.module_utils.facts.get_uname_version', mock_get_uname_version)
    @patch('os.path.exists', mock_path_exists)
    @patch('os.path.getsize', mock_path_getsize)
    @patch('platform.dist', lambda: testcase['platform.dist'])
    @patch('platform.system', mock_platform_system)
    def get_facts(testcase):
        return facts.Facts(module).populate()

    generated_facts = get_facts(testcase)

    # testcase['result'] has a list of variables and values it expects Facts() to set
    for key, val in testcase['result'].items():
        assert key in generated_facts
        msg = 'Comparing value of %s on %s, should: %s, is: %s' %\
            (key, testcase['name'], val, generated_facts[key])
        assert generated_facts[key] == val, msg
