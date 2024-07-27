# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

from ansible.module_utils.facts.network import fc_wwn
import pytest


# AIX lsdev
LSDEV_OUTPUT = """
fcs0 Defined   00-00 8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)
fcs1 Available 04-00 8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)
"""

# slightly cut output of lscfg (from Z0 to ZC)
LSCFG_OUTPUT = """
  fcs1             U78CB.001.WZS00ZS-P1-C9-T1  8Gb PCI Express Dual Port FC Adapter (df1000f114108a03)

        Part Number.................00E0806
        Serial Number...............1C4090830F
        Manufacturer................001C
        EC Level.................... D77161
        Customer Card ID Number.....577D
        FRU Number..................00E0806
        Device Specific.(ZM)........3
        Network Address.............10000090FA551508
        ROS Level and ID............027820B7
        Device Specific.(Z0)........31004549
        Device Specific.(ZC)........00000000
        Hardware Location Code......U78CB.001.WZS00ZS-P1-C9-T1
"""

# Solaris
FCINFO_OUTPUT = """
HBA Port WWN: 10000090fa1658de
        Port Mode: Initiator
        Port ID: 30100
        OS Device Name: /dev/cfg/c13
        Manufacturer: Emulex
        Model: LPe12002-S
        Firmware Version: LPe12002-S 2.01a12
        FCode/BIOS Version: Boot:5.03a0 Fcode:3.01a1
        Serial Number: 4925381+13090001ER
        Driver Name: emlxs
        Driver Version: 3.3.00.1 (2018.01.05.16.30)
        Type: N-port
        State: online
        Supported Speeds: 2Gb 4Gb 8Gb
        Current Speed: 8Gb
        Node WWN: 20000090fa1658de
        NPIV Not Supported
"""

IOSCAN_OUT = """
Class     I  H/W Path    Driver S/W State   H/W Type     Description
==================================================================
fc        0  2/0/10/1/0  fcd   CLAIMED     INTERFACE    HP AB379-60101 4Gb Dual Port PCI/PCI-X Fibre Channel Adapter (FC Port 1)
                        /dev/fcd0
"""

FCMSUTIL_OUT = """
                           Vendor ID is = 0x1077
                           Device ID is = 0x2422
            PCI Sub-system Vendor ID is = 0x103C
                   PCI Sub-system ID is = 0x12D7
                               PCI Mode = PCI-X 133 MHz
                       ISP Code version = 5.4.0
                       ISP Chip version = 3
                               Topology = PTTOPT_FABRIC
                             Link Speed = 4Gb
                     Local N_Port_id is = 0x010300
                  Previous N_Port_id is = None
            N_Port Node World Wide Name = 0x50060b00006975ed
            N_Port Port World Wide Name = 0x50060b00006975ec
            Switch Port World Wide Name = 0x200300051e046c0f
            Switch Node World Wide Name = 0x100000051e046c0f
              N_Port Symbolic Port Name = server1_fcd0
              N_Port Symbolic Node Name = server1_HP-UX_B.11.31
                           Driver state = ONLINE
                       Hardware Path is = 2/0/10/1/0
                     Maximum Frame Size = 2048
         Driver-Firmware Dump Available = NO
         Driver-Firmware Dump Timestamp = N/A
                                   TYPE = PFC
                         NPIV Supported = YES
                         Driver Version = @(#) fcd B.11.31.1103 Dec  6 2010
"""


def mock_get_bin_path(cmd, required=False, opt_dirs=None):
    cmds = {
        'lsdev': '/usr/sbin/lsdev',
        'lscfg': '/usr/sbin/lscfg',
        'fcinfo': '/usr/sbin/fcinfo',
        'ioscan': '/usr/bin/ioscan',
        'fcmsutil': '/opt/fcms/bin/fcmsutil',
    }
    return cmds.get(cmd, None)


@pytest.mark.parametrize(
    ("test_input", "expected"),
    [
        pytest.param(
            {
                "platform": "aix6",
                "mock_run_command": [(0, LSDEV_OUTPUT, ""), (0, LSCFG_OUTPUT, "")],
            },
            ["10000090FA551508"],
            id="aix6",
        ),
        pytest.param(
            {
                "platform": "sunos5",
                "mock_run_command": [
                    (0, FCINFO_OUTPUT, ""),
                ],
            },
            ["10000090fa1658de"],
            id="sunos5",
        ),
        pytest.param(
            {
                "platform": "hp-ux11",
                "mock_run_command": [(0, IOSCAN_OUT, ""), (0, FCMSUTIL_OUT, "")],
            },
            ["0x50060b00006975ec"],
            id="hp-ux11",
        ),
    ],
)
def test_get_fc_wwn_info(mocker, test_input, expected):
    module = mocker.MagicMock()
    inst = fc_wwn.FcWwnInitiatorFactCollector()

    mocker.patch("sys.platform", test_input["platform"])
    mocker.patch.object(module, "get_bin_path", side_effect=mock_get_bin_path)
    mocker.patch.object(
        module, "run_command", side_effect=test_input["mock_run_command"]
    )
    wwn_expected = {"fibre_channel_wwn": expected}
    assert wwn_expected == inst.collect(module=module)
