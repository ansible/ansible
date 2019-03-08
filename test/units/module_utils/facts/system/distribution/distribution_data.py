# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DISTRIBUTION_FILE_DATA = {
    'coreos': 'DISTRIB_ID="Container Linux by CoreOS"\nDISTRIB_RELEASE=1911.5.0\nDISTRIB_CODENAME="Rhyolite"\nDISTRIB_DESCRIPTION="Container Linux by CoreOS '
              '1911.5.0 (Rhyolite)"',
    'debian9': 'PRETTY_NAME="Debian GNU/Linux 9 (stretch)"\nNAME="Debian GNU/Linux"\nVERSION_ID="9"\nVERSION="9 (stretch)"\nID=debian\nHOME_URL="https://www.d'
               'ebian.org/"\nSUPPORT_URL="https://www.debian.org/support"\nBUG_REPORT_URL="https://bugs.debian.org/"\n',
    'clearlinux': 'NAME="Clear Linux OS"\nVERSION=1\nID=clear-linux-os\nID_LIKE=clear-linux-os\nVERSION_ID=28120\nPRETTY_NAME="Clear Linux OS"\nANSI_COLOR="1;'
                  '35"\nHOME_URL="https://clearlinux.org"\nSUPPORT_URL="https://clearlinux.org"\nBUG_REPORT_URL="mailto:dev@lists.clearlinux.org"',
    'linuxmint': 'NAME="Linux Mint"\nVERSION="19.1 (Tessa)"\nID=linuxmint\nID_LIKE=ubuntu\nPRETTY_NAME="Linux Mint 19.1"\nVERSION_ID="19.1"\nHOME_URL="h'
                 'ttps://www.linuxmint.com/"\nSUPPORT_URL="https://forums.ubuntu.com/"\nBUG_REPORT_URL="http://linuxmint-troubleshooting-guide.readthedo'
                 'cs.io/en/latest/"\nPRIVACY_POLICY_URL="https://www.linuxmint.com/"\nVERSION_CODENAME=tessa\nUBUNTU_CODENAME=bionic',
}
