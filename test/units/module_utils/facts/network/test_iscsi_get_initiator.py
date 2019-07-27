# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.facts.network import iscsi
from units.compat.mock import Mock


# AIX # lsattr -E -l iscsi0
LSATTR_OUTPUT = """
disc_filename  /etc/iscsi/targets            Configuration file                            False
disc_policy    file                          Discovery Policy                              True
initiator_name iqn.localhost.hostid.7f000002 iSCSI Initiator Name                          True
isns_srvnames  auto                          iSNS Servers IP Addresses                     True
isns_srvports                                iSNS Servers Port Numbers                     True
max_targets    16                            Maximum Targets Allowed                       True
num_cmd_elems  200                           Maximum number of commands to queue to driver True
"""

# HP-UX # iscsiutil -l
ISCSIUTIL_OUTPUT = """
Initiator Name             : iqn.2001-04.com.hp.stor:svcio
Initiator Alias            :
Authentication Method      : None
CHAP Method                : CHAP_UNI
Initiator CHAP Name        :
CHAP Secret                :
NAS Hostname               :
NAS Secret                 :
Radius Server Hostname     :
Header Digest              : None,CRC32C (default)
Data Digest                : None,CRC32C (default)
SLP Scope list for iSLPD   :
"""


def test_get_iscsi_info(mocker):
    module = Mock()
    inst = iscsi.IscsiInitiatorNetworkCollector()

    mocker.patch('sys.platform', 'aix6')
    mocker.patch('ansible.module_utils.facts.network.iscsi.get_bin_path', return_value='/usr/sbin/lsattr')
    mocker.patch.object(module, 'run_command', return_value=(0, LSATTR_OUTPUT, ''))
    aix_iscsi_expected = {"iscsi_iqn": "iqn.localhost.hostid.7f000002"}
    assert aix_iscsi_expected == inst.collect(module=module)

    mocker.patch('sys.platform', 'hp-ux')
    mocker.patch('ansible.module_utils.facts.network.iscsi.get_bin_path', return_value='/opt/iscsi/bin/iscsiutil')
    mocker.patch.object(module, 'run_command', return_value=(0, ISCSIUTIL_OUTPUT, ''))
    hpux_iscsi_expected = {"iscsi_iqn": " iqn.2001-04.com.hp.stor:svcio"}
    assert hpux_iscsi_expected == inst.collect(module=module)
