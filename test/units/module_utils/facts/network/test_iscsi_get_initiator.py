# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.network import iscsi
import pytest


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


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "platform": "aix6",
                "iscsi_path": "/usr/sbin/lsattr",
                "return_command": LSATTR_OUTPUT
            },
            {"iscsi_iqn": "iqn.localhost.hostid.7f000002"},
            id="aix",
        ),
        pytest.param(
            {
                "platform": "hp-ux",
                "iscsi_path": "/opt/iscsi/bin/iscsiutil",
                "return_command": ISCSIUTIL_OUTPUT
            },
            {"iscsi_iqn": " iqn.2001-04.com.hp.stor:svcio"},
            id="hpux",
        )
    ]
)
def test_get_iscsi_info(mocker, test_input, expected):
    module = mocker.MagicMock()
    inst = iscsi.IscsiInitiatorNetworkCollector()

    mocker.patch('sys.platform', test_input['platform'])
    mocker.patch.object(module, 'get_bin_path', return_value=test_input['iscsi_path'])
    mocker.patch.object(module, 'run_command', return_value=(0, test_input['return_command'], ''))
    assert expected == inst.collect(module=module)
